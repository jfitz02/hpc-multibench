#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The definition of the user interface."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    TabbedContent,
    TabPane,
    TextArea,
    Tree,
)
from textual.widgets.tree import TreeNode
from textual_plotext import PlotextPlot

from hpc_multibench.yaml_model import BenchModel, RunConfigurationModel, TestPlan

TestPlanTreeType = RunConfigurationModel | BenchModel

PLOTEXT_MARKER = "braille"
INITIAL_TAB = "metrics-tab"


class TestPlanTree(Tree[TestPlanTreeType]):
    """A tree showing the hierarchy of benches and runs in a test plan."""

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate a tree representing a test plan."""
        self.previous_cursor_node: TreeNode[TestPlanTreeType] | None = None
        self._app: "UserInterface" = self.app
        super().__init__(*args, **kwargs)

    def populate(self) -> None:
        """Populate the tree with data from the test plan."""
        for bench_name, bench in self._app.test_plan.benches.items():
            bench_node = self.root.add(bench_name, data=bench)
            for run_configuration_name in bench.run_configurations:
                run_configuration: RunConfigurationModel = (
                    self._app.test_plan.run_configurations[run_configuration_name]
                )
                bench_node.add(
                    run_configuration_name,
                    allow_expand=False,
                    data=run_configuration,
                )
            bench_node.expand()
        self.root.expand()

    def action_select_cursor(self) -> None:
        """Pass the selection back and only toggle if already selected."""
        if self.cursor_node is not None:
            self._app.handle_tree_selection(self.cursor_node)
            if self.cursor_node in (self.previous_cursor_node, self.root):
                self.cursor_node.toggle()
        self.previous_cursor_node = self.cursor_node


class UserInterface(App[None]):
    """The interactive TUI."""

    CSS_PATH = "user_interface.tcss"
    TITLE = "HPC MultiBench"
    SUB_TITLE = "A Swiss army knife for comparing programs on HPC resources"

    BINDINGS = [
        ("q", "quit", "quit"),
    ]

    def __init__(self, test_plan: TestPlan, *args, **kwargs) -> None:
        """."""
        self.test_plan: TestPlan = test_plan
        self.start_pane_shown: bool = True
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Compose the structure of the application."""
        yield Header()
        with Horizontal():
            # The navigation bar for the test plan
            yield TestPlanTree(label="Test Plan", id="explorer")

            # The starting pane that conceals the data pane when nothing selected
            with Container(id="start-pane"):
                yield Label("Select a benchmark or run to start", id="start-pane-label")

            with TabbedContent(initial=INITIAL_TAB, id="informer"):
                with TabPane("Run", id="run-tab"):
                    yield Label("", id="run-information")
                    # TODO: Get bash language working
                    yield TextArea(
                        "echo hello",
                        id="sbatch-contents",
                        read_only=True,
                        show_line_numbers=True,
                    )
                    yield Button("Run", id="run-button")
                with TabPane("Metrics", id="metrics-tab"):
                    yield DataTable(id="metrics-table")
                with TabPane("Plot", id="plot-tab"):
                    yield PlotextPlot(id="metrics-plot")
        yield Footer()

    def on_mount(self) -> None:
        """Initialise data when the application is created."""
        tree = self.query_one(TestPlanTree)
        tree.populate()

    def remove_start_pane(self) -> None:
        """Remove the start pane from the screen."""
        if self.start_pane_shown:
            self.query_one("#start-pane", Container).remove()
            self.start_pane_shown = False

    def update_run_tab(self, node: TreeNode[TestPlanTreeType]) -> None:
        """."""
        run_information = self.query_one("#run-information", Label)
        sbatch_contents = self.query_one("#sbatch-contents", TextArea)

        if isinstance(node.data, BenchModel):
            # TODO: This is a slightly annoying hack - but it works...
            run_information.visible = True
            sbatch_contents.visible = False
            run_information.update(
                "\n".join([str(x) for x in node.data.matrix_iterator])
            )
            sbatch_contents.text = ""
        else:
            sbatch_contents.visible = True
            run_information.visible = False
            sbatch_contents.text = node.data.realise(
                "", str(node.label), {}
            ).sbatch_contents
            run_information.update("")

    def update_metrics_tab(self, node: TreeNode[TestPlanTreeType]) -> None:
        """."""
        metrics_table = self.query_one("#metrics-table", DataTable)
        metrics_table.clear(columns=True)
        if isinstance(node.data, BenchModel):
            column_names = ["Name", *list(node.data.analysis.metrics.keys())]
            metrics_table.add_columns(*column_names)
            for results in node.data.get_analysis(str(node.label)):
                metrics_table.add_row(*results.values())
            # TODO: Fix sorting
            # metrics_table.sort("Name", node.data.analysis.plot.x)
        else:
            assert node.parent is not None
            metrics_table.add_columns(*node.parent.data.analysis.metrics.keys())
            for results in node.parent.data.get_analysis(str(node.parent.label)):
                if results["name"] == str(node.label):
                    metrics_table.add_row(
                        *[value for key, value in results.items() if key != "name"]
                    )
            # metrics_table.sort(node.parent.data.analysis.plot.x)

    def update_plot_tab(self, node: TreeNode[TestPlanTreeType]) -> None:
        """."""
        metrics_plot_widget = self.query_one("#metrics-plot", PlotextPlot)
        metrics_plot = metrics_plot_widget.plt
        metrics_plot.clear_figure()
        metrics_plot.title("Benchmark analysis")
        if isinstance(node.data, BenchModel):
            # metrics_plot.plot(metrics_plot.sin())
            for name, result in node.data.comparative_plot_results(
                str(node.label)
            ).items():
                metrics_plot.plot(
                    *zip(*result, strict=True), label=name, marker=PLOTEXT_MARKER
                )
        else:
            assert node.parent is not None
            for name, result in node.parent.data.comparative_plot_results(
                str(node.parent.label)
            ).items():
                if name == str(node.label):
                    metrics_plot.plot(
                        *zip(*result, strict=True), label=name, marker=PLOTEXT_MARKER
                    )
        metrics_plot_widget.refresh()

    def handle_tree_selection(self, node: TreeNode[TestPlanTreeType]) -> None:
        """."""
        if node == self.query_one(TestPlanTree).root:
            return

        self.remove_start_pane()

        self.update_run_tab(node)
        self.update_metrics_tab(node)
        self.update_plot_tab(node)

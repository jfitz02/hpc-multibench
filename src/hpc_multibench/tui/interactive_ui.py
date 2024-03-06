#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The definition of the interactive user interface."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
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

from hpc_multibench.yaml_model import RunConfigurationModel
from hpc_multibench.test_bench import TestBench
from hpc_multibench.test_plan import TestPlan

TestPlanTreeType = RunConfigurationModel | TestBench

PLOTEXT_MARKER = "braille"
INITIAL_TAB = "run-tab"


class TestPlanTree(Tree[TestPlanTreeType]):
    """A tree showing the hierarchy of benches and runs in a test plan."""

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate a tree representing a test plan."""
        self.previous_cursor_node: TreeNode[TestPlanTreeType] | None = None
        self._app: UserInterface = self.app  # type: ignore
        super().__init__(*args, **kwargs)

    def populate(self) -> None:
        """Populate the tree with data from the test plan."""
        for bench in self._app.test_plan.benches:
            bench_node = self.root.add(bench.name, data=bench)
            for (
                run_configuration_name,
                run_configuration,
            ) in bench.run_configuration_models.items():
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

    CSS_PATH = "interactive_ui.tcss"
    TITLE = "HPC MultiBench"
    SUB_TITLE = "A Swiss army knife for comparing programs on HPC resources"

    BINDINGS = [
        ("q", "quit", "Quit"),
        # TODO: Add button to reload test plan
    ]

    def __init__(self, test_plan: TestPlan, *args, **kwargs) -> None:
        """Initialise the user interface."""
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
                    yield DataTable(id="run-information")
                    # TODO: Get bash language working
                    yield TextArea(
                        "echo hello",
                        id="sbatch-contents",
                        read_only=True,
                        show_line_numbers=True,
                    )
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
        """Update the run tab of the user interface."""
        run_information = self.query_one("#run-information", DataTable)
        sbatch_contents = self.query_one("#sbatch-contents", TextArea)
        run_information.clear(columns=True)

        if isinstance(node.data, TestBench):
            # TODO: This is a slightly annoying hack - but it works...
            sbatch_contents.visible = False
            sbatch_contents.text = ""
            instantiations = node.data.instantiations
        else:
            sbatch_contents.visible = True
            assert node.parent is not None
            test_bench = node.parent.data
            # TODO: Realise with selected column in data table
            sbatch_contents.text = node.data.realise(
                str(node.label), test_bench.output_directory, {}
            ).sbatch_contents
            instantiations = test_bench.instantiations

        if len(instantiations) > 0:
            run_information.add_columns(*instantiations[0].keys())
        for instantiation in instantiations:
            run_information.add_row(*instantiation.values())

    def update_metrics_tab(self, node: TreeNode[TestPlanTreeType]) -> None:
        """Update the metrics tab of the user interface."""
        # metrics_table = self.query_one("#metrics-table", DataTable)
        # metrics_table.clear(columns=True)
        # if isinstance(node.data, TestBench):
        #     column_names = [
        #         "Name",
        #         *list(node.data.bench_model.analysis.metrics.keys()),
        #     ]
        #     metrics_table.add_columns(*column_names)
        #     for results in node.data.get_analysis(str(node.label)):
        #         metrics_table.add_row(*results.values())
        #     # TODO: Fix sorting
        #     # metrics_table.sort("Name", node.data.analysis.plot.x)
        # else:
        #     assert node.parent is not None
        #     metrics_table.add_columns(*node.parent.data.analysis.metrics.keys())
        #     for results in node.parent.data.get_analysis(str(node.parent.label)):
        #         if results["name"] == str(node.label):
        #             metrics_table.add_row(
        #                 *[value for key, value in results.items() if key != "name"]
        #            )
        # metrics_table.sort(node.parent.data.analysis.plot.x)

    def update_plot_tab(self, node: TreeNode[TestPlanTreeType]) -> None:
        """Update the plot tab of the user interface."""
        # TODO: Add button to open matplotlib window with plot as well
        # metrics_plot_widget = self.query_one("#metrics-plot", PlotextPlot)
        # metrics_plot = metrics_plot_widget.plt
        # metrics_plot.clear_figure()
        # metrics_plot.title("Benchmark analysis")
        # if isinstance(node.data, BenchModel):
        #     # metrics_plot.plot(metrics_plot.sin())
        #     for name, result in node.data.comparative_plot_results(
        #         str(node.label)
        #     ).items():
        #         metrics_plot.plot(
        #             *zip(*result, strict=True), label=name, marker=PLOTEXT_MARKER
        #         )
        # else:
        #     assert node.parent is not None
        #     for name, result in node.parent.data.comparative_plot_results(
        #         str(node.parent.label)
        #     ).items():
        #         if name == str(node.label):
        #             metrics_plot.plot(
        #                 *zip(*result, strict=True), label=name, marker=PLOTEXT_MARKER
        #             )
        # metrics_plot_widget.refresh()

    def handle_tree_selection(self, node: TreeNode[TestPlanTreeType]) -> None:
        """Drive the user interface updates when new tree nodes are selected."""
        if node == self.query_one(TestPlanTree).root:
            return

        self.remove_start_pane()

        self.update_run_tab(node)
        self.update_metrics_tab(node)
        self.update_plot_tab(node)

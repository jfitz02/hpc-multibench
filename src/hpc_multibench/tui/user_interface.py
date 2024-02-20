#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The definition of the user interface."""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Container
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    TabbedContent,
    TabPane,
    Tree,
)
from textual.widgets.tree import TreeNode
from textual_plotext import PlotextPlot

from hpc_multibench.yaml_model import BenchModel, RunConfigurationModel, TestPlan


TestPlanTreeType = RunConfigurationModel | BenchModel


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
            if self.cursor_node == self.previous_cursor_node:
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
        yield Header()
        with Horizontal():
            yield TestPlanTree(label="Test Plan", id="explorer")

            with Container(id="start-pane"):
                yield Label("Select a benchmark or run to start", id="start-pane-label")

            with TabbedContent(initial="run-tab", id="informer"):
                with TabPane("Run", id="run-tab"):
                    yield Label("Select a benchmark to start", id="run-information")
                    yield Button("Run", id="run-button")
                with TabPane("Metrics", id="metrics-tab"):
                    yield DataTable(id="metrics-table")
                with TabPane("Plot", id="plot-tab"):
                    yield PlotextPlot(id="metrics-plot")
        yield Footer()

    def on_mount(self) -> None:
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
        output_string = f"{type(node.data)} {node.label}"
        if isinstance(node.data, BenchModel):
            output_string = "\n".join([str(x) for x in node.data.matrix_iterator])
        else:
            output_string = node.data.realise("", str(node.label), {}).sbatch_contents
        run_information.update(output_string)

    def update_metrics_tab(self, node: TreeNode[TestPlanTreeType]) -> None:
        """."""
        metrics_table = self.query_one("#metrics-table", DataTable)
        if isinstance(node.data, BenchModel):
            metrics_table.add_columns(*node.data.analysis.metrics.keys())
            metrics_table.add_row([])
            # for results in node.data.get_analysis(str(node.label)):
            #     metrics_table.add_row(*[str(x) for x in results.values()])

    def update_plot_tab(self, node: TreeNode[TestPlanTreeType]) -> None:
        """."""
        metrics_plot = self.query_one("#metrics-plot", PlotextPlot).plt
        metrics_plot.title("Scatter Plot")
        metrics_plot.plot(metrics_plot.sin())

    def handle_tree_selection(self, node: TreeNode[TestPlanTreeType]) -> None:
        """."""
        self.remove_start_pane()

        self.update_run_tab(node)
        self.update_metrics_tab(node)
        self.update_plot_tab(node)

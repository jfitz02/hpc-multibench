# -*- coding: utf-8 -*-
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Static,
    TabbedContent,
    TabPane,
    Tree,
)
from textual.widgets.tree import TreeNode
from textual_plotext import PlotextPlot

from hpc_multibench.yaml_model import BenchModel, RunConfigurationModel, TestPlan


class RunAnalysisPlot(PlotextPlot):
    pass


TestPlanTreeType = RunConfigurationModel | BenchModel


class TestPlanTree(Tree[TestPlanTreeType]):
    def __init__(self, *args, **kwargs) -> None:
        """."""
        self.previous_cursor_node: TreeNode[TestPlanTreeType] | None = None
        self._app: "UserInterface" = self.app
        super().__init__(*args, **kwargs)

    def populate(self) -> None:
        """."""
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
    CSS_PATH = "user_interface.tcss"
    TITLE = "HPC MultiBench"
    SUB_TITLE = "A Swiss army knife for comparing programs on HPC resources"

    BINDINGS = [
        ("q", "quit", "quit"),
    ]

    def __init__(self, test_plan: TestPlan, *args, **kwargs) -> None:
        """."""
        self.test_plan: TestPlan = test_plan
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield TestPlanTree(label="Test Plan", id="explorer")

            with TabbedContent(initial="run", id="view-pane"):
                with TabPane("Run", id="run"):
                    # yield Static("Select a benchmark to start", id="test-node")
                    yield Static("Select a benchmark to start", id="information-box")
                    yield Button("Run", classes="run-button")
                with TabPane("Metrics", id="metrics"):
                    yield DataTable(id="metrics-table")
                    yield Button("Re-run", classes="run-button")
                with TabPane("Plot", id="plot"):
                    yield RunAnalysisPlot(id="metrics_plot")
                    yield Button("Re-run", classes="run-button")
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one(TestPlanTree)
        tree.populate()

        plt = self.query_one(RunAnalysisPlot).plt
        plt.title("Scatter Plot")
        plt.scatter(plt.sin())

    def handle_tree_selection(self, node: TreeNode[TestPlanTreeType]) -> None:
        """."""
        info_box = self.app.query_one("#information-box", Static)

        output_string = f"{type(node.data)} {node.label}"
        if isinstance(node.data, BenchModel):
            output_string = "\n".join([str(x) for x in node.data.matrix_iterator])
        else:
            # TODO: Could be a text area
            output_string = node.data.realise("", str(node.label), {}).sbatch_contents

        info_box.update(output_string)

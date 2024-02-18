# -*- coding: utf-8 -*-
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Header, Static, TabbedContent, TabPane, Tree
from textual.widgets.tree import TreeNode
from textual_plotext import PlotextPlot

from hpc_multibench.yaml_model import TestPlan


class UserInterface(App):
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
                    yield Static("Select a benchmark to start", id="test-node")
                with TabPane("Analyse", id="analyse"):
                    yield RunAnalysisPlot()
                    yield Button("Re-run", id="run-button")
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one(TestPlanTree)
        tree.populate()

        plt = self.query_one(RunAnalysisPlot).plt
        plt.title("Scatter Plot")
        plt.scatter(plt.sin())

    def handle_tree_selection(self, node: TreeNode[None]) -> None:
        """."""
        test_node = self.app.query_one("#test-node", Static)
        test_node.update(node.label)


class RunAnalysisPlot(PlotextPlot):
    pass


class TestPlanTree(Tree[None]):
    def __init__(self, *args, **kwargs) -> None:
        """."""
        self.previous_cursor_node: TreeNode[None] | None = None
        self._app: UserInterface = self.app
        super().__init__(*args, **kwargs)

    def populate(self) -> None:
        """."""
        for bench_name, bench in self._app.test_plan.benches.items():
            bench_node = self.root.add(bench_name)
            for run_configuration_name in bench.run_configurations:
                bench_node.add(run_configuration_name, allow_expand=False)
            bench_node.expand()
        self.root.expand()

    def action_select_cursor(self) -> None:
        """Pass the selection back and only toggle if already selected."""
        self._app.handle_tree_selection(self.cursor_node)
        if self.cursor_node == self.previous_cursor_node:
            self.cursor_node.toggle()
        self.previous_cursor_node = self.cursor_node

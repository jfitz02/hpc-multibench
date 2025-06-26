#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The definition of the interactive user interface."""

from argparse import Namespace
from enum import Enum, auto
from typing import cast

from textual.app import App, ComposeResult
from textual.containers import Center, Container, Horizontal, Vertical
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    ProgressBar,
    TabbedContent,
    TabPane,
    TextArea,
    Tree,
)
from textual.widgets.tree import TreeNode
from textual_plotext import PlotextPlot
from tree_sitter_languages import get_language

from hpc_multibench.plot import plot_matplotlib, plot_plotext
from hpc_multibench.run_configuration import RunConfiguration, get_queued_job_ids
from hpc_multibench.test_bench import TestBench
from hpc_multibench.test_plan import TestPlan
from hpc_multibench.tui.bash_highlights import BASH_HIGHLIGHTS
from hpc_multibench.uncertainties import UFloat
from hpc_multibench.yaml_model import (
    BarChartModel,
    LinePlotModel,
    RooflinePlotModel,
    RunConfigurationModel,
)

TestPlanTreeType = RunConfigurationModel | TestBench

PLOTEXT_MARKER = "braille"
INITIAL_TAB = "run-tab"


class ShowMode(Enum):
    """The current state of the application."""

    TestBench = auto()
    RunConfiguration = auto()
    Uninitialised = auto()


class TestPlanTree(Tree[TestPlanTreeType]):
    """A tree showing the hierarchy of benches and runs in a test plan."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Instantiate a tree representing a test plan."""
        self.previous_cursor_node: TreeNode[TestPlanTreeType] | None = None
        self._app: UserInterface = self.app  # type: ignore[assignment]
        super().__init__(*args, **kwargs)

    def populate(self) -> None:
        """Populate the tree with data from the test plan."""
        self.clear()
        for bench in self._app.test_plan.benches:
            bench_node = self.root.add(
                (
                    bench.name
                    if bench.bench_model.enabled
                    else f"[dim]{bench.name}[/dim]"
                ),
                data=bench,
            )
            for (
                run_configuration_name,
                run_configuration,
            ) in bench.run_configuration_models.items():
                bench_node.add(
                    (
                        run_configuration_name
                        if bench.bench_model.enabled
                        else f"[dim]{run_configuration_name}[/dim]"
                    ),
                    allow_expand=False,
                    data=run_configuration,
                )
            if bench.bench_model.enabled:
                bench_node.expand()
        self.root.expand()

    def action_select_cursor(self) -> None:
        """Pass the selection back and only toggle if already selected."""
        if self.cursor_node is not None:
            self._app.handle_tree_selection(self.cursor_node)
            if self.cursor_node in (self.previous_cursor_node, self.root):
                self.cursor_node.toggle()
        self.previous_cursor_node = self.cursor_node


class RunDialogScreen(Screen[None]):
    """Screen with a dialog to quit."""

    progress_timer: Timer

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Instantiate a dialog screen for spawning runs."""
        self._app: UserInterface = self.app  # type: ignore[assignment]
        self.jobs_spawned: bool = False
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Compose the structure of the dialog screen."""
        with Center(id="run-dialog"):
            yield Label(
                (
                    "[bold]Waiting for queued jobs to complete.[/bold]\n\n"
                    "You can continue, but will need to reload the test plan "
                    "once they are complete to see any new results."
                ),
                id="run-dialog-message",
            )
            yield ProgressBar(id="run-dialog-progress")
            yield Button("Continue", variant="primary", id="run-dialog-continue")

    def on_mount(self) -> None:
        """Set up a timer to simulate progess happening."""
        self.progress_timer = self.set_interval(5, self.make_progress)

    def make_progress(self) -> None:
        """Automatically advance the progress bar."""
        progress_bar = self.query_one("#run-dialog-progress", ProgressBar)
        if not self.jobs_spawned:
            self.jobs_spawned = True
            # Wait till everything is rendered to kick off blocking calls...
            for bench in self._app.test_plan.benches:
                if bench.bench_model.enabled:
                    bench.record(self._app.command_args)
            total_jobs = sum(
                [
                    len(set(bench.all_job_ids))
                    for bench in self._app.test_plan.benches
                    if bench.bench_model.enabled
                ]
            )
            progress_bar.update(total=total_jobs)

        # Update the progress based on jobs completed
        queued_jobs = set(get_queued_job_ids())
        completed_jobs = sum(
            [
                len(set(bench.all_job_ids) - queued_jobs)
                for bench in self._app.test_plan.benches
                if bench.bench_model.enabled
            ]
        )
        progress_bar.progress = completed_jobs

        # Reload the test plan when all the jobs are completed
        if progress_bar.progress == progress_bar.total:
            self.query_one("#run-dialog-message", Label).update(
                "[bold]All queued jobs have completed!\n\n[/bold]"
                "Press 'Continue' to dismiss this dialog, then 'R' on the "
                "keyboard to reload the test plan and view the new results."
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss the modal dialog when the continue button is pressed."""
        if event.button.id == "run-dialog-continue":
            self.progress_timer.stop()
            self.app.pop_screen()


class UserInterface(App[None]):
    """The interactive TUI."""

    CSS_PATH = "interactive_ui.tcss"
    TITLE = "HPC MultiBench"
    SUB_TITLE = "A Swiss army knife for comparing programs on HPC resources"

    BINDINGS = [
        ("r", "reload_test_plan()", "Reload Test Plan"),
        # ("s", "sort_selected_column()", "Sort by selected column"),
        ("n", "change_plot(1)", "Next Graph"),
        ("m", "change_plot(-1)", "Previous Graph"),
        ("p", "open_graph()", "Open Graph"),
        ("q", "quit", "Quit"),
    ]

    def __init__(  # type: ignore[no-untyped-def]
        self, test_plan: TestPlan, command_args: Namespace, *args, **kwargs
    ) -> None:
        """Initialise the user interface."""
        self.test_plan: TestPlan = test_plan
        self.command_args: Namespace = command_args
        self.show_mode = ShowMode.Uninitialised
        self.current_test_bench: TestBench | None = None
        self.current_run_configuration: RunConfigurationModel | None = None
        self.current_run_configuration_name: str | None = None
        self.current_plot_index: int | None = None
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Compose the structure of the application."""
        yield Header()
        with Horizontal():
            # The navigation bar for the test plan
            with Vertical(id="explorer"):
                yield Button("Run Test Plan", id="run-button")
                yield TestPlanTree(label="Test Plan", id="tree-explorer")

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
                        theme="monokai",
                    )
                with TabPane("Metrics", id="metrics-tab"):
                    yield DataTable(id="metrics-table")
                with TabPane("Plot", id="plot-tab"):
                    yield PlotextPlot(id="metrics-plot")
        yield Footer()

    def on_mount(self) -> None:
        """Initialise data when the application is created."""
        self.initialise_test_plan_tree()
        self.query_one("#sbatch-contents", TextArea).register_language(
            get_language("bash"), BASH_HIGHLIGHTS
        )
        self.query_one("#sbatch-contents", TextArea).language = "bash"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """When a button is pressed."""
        if event.button.id == "run-button":
            self.push_screen(RunDialogScreen())

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """When a data table cell is selected."""
        if event.data_table.id == "run-information":
            self.update_sbatch_contents()

    def remove_start_pane(self) -> None:
        """Remove the start pane from the screen if it is uninitialised."""
        if self.show_mode is ShowMode.Uninitialised:
            self.query_one("#start-pane", Container).remove()

    def initialise_test_plan_tree(self) -> None:
        """Initialise the test plan tree."""
        tree = self.query_one(TestPlanTree)
        tree.populate()
        self.app.set_focus(tree)

    def handle_tree_selection(self, node: TreeNode[TestPlanTreeType]) -> None:
        """Drive the user interface updates when new tree nodes are selected."""
        if node == self.query_one(TestPlanTree).root:
            return

        self.remove_start_pane()

        if isinstance(node.data, TestBench):
            self.show_mode = ShowMode.TestBench
            self.current_test_bench = node.data
            self.current_run_configuration = None
            self.current_run_configuration_name = None
        elif isinstance(node.data, RunConfigurationModel):
            self.show_mode = ShowMode.RunConfiguration
            assert node.parent is not None
            self.current_test_bench = cast(TestBench, node.parent.data)
            self.current_run_configuration = node.data
            self.current_run_configuration_name = (
                str(node.label).strip("[dim]").strip("[/dim]")
            )

        self.current_plot_index = 0
        self.update_all_tabs()

    def update_all_tabs(self) -> None:
        """Update all tabs in the user interface."""
        self.update_run_tab()
        self.update_metrics_tab()
        self.update_plot_tab()

    def update_run_tab(self) -> None:
        """Update the run tab of the user interface."""
        self.update_run_information()
        self.update_sbatch_contents()

    def update_run_information(self) -> None:
        """Update the instantiations table in the run tab."""
        run_information = self.query_one("#run-information", DataTable)

        assert self.current_test_bench is not None
        instantiations = self.current_test_bench.instantiations

        run_information.clear(columns=True)
        if len(instantiations) > 0:
            run_information.add_columns(*instantiations[0].keys())
        for instantiation in instantiations:
            run_information.add_row(*instantiation.values())

    def update_sbatch_contents(self) -> None:
        """Update the sbatch contents in the run tab."""
        run_information = self.query_one("#run-information", DataTable)
        sbatch_contents = self.query_one("#sbatch-contents", TextArea)

        assert self.current_test_bench is not None
        instantiations = self.current_test_bench.instantiations
        if self.show_mode == ShowMode.TestBench:
            sbatch_contents.visible = False
            sbatch_contents.text = ""
        else:
            assert self.current_run_configuration is not None
            assert self.current_run_configuration_name is not None
            sbatch_contents.visible = True
            selected_instantiation = instantiations[run_information.cursor_row]

            sbatch_contents.text = self.current_run_configuration.realise(
                self.current_run_configuration_name,
                self.current_test_bench.output_directory,
                selected_instantiation,
            ).sbatch_contents

    def get_aggregated_metrics(
        self,
    ) -> list[tuple[RunConfiguration, dict[str, str | UFloat]]] | None:
        """."""
        assert self.current_test_bench is not None
        run_outputs = self.current_test_bench.get_run_outputs()
        if run_outputs is None:
            return None
        run_metrics = self.current_test_bench.get_run_metrics(run_outputs)
        aggregated_metrics = self.current_test_bench.aggregate_run_metrics(run_metrics)
        return self.current_test_bench.calculate_derived_metrics(aggregated_metrics)

    def update_metrics_tab(self) -> None:
        """Update the metrics tab of the user interface."""
        metrics_table = self.query_one("#metrics-table", DataTable)
        metrics_table.clear(columns=True)

        assert self.current_test_bench is not None
        aggregated_metrics = self.get_aggregated_metrics()
        if aggregated_metrics is None:
            metrics_table.add_columns("No run data to show!")
            return
        
        display_metrics = []
        
        agg_metrics = ["fmean", "stdev", "min", "max", "sum"]
        for metric in self.current_test_bench.bench_model.analysis.metrics.keys():
            if metric in self.current_test_bench.bench_model.analysis.multiple_values:
                for agg_metric in agg_metrics:
                    display_metrics.append(f"{metric} {agg_metric}")
            else:
                display_metrics.append(metric)
                
        with open("metrics.txt", "w") as f:
            f.write(str(len(display_metrics)) + "\n")

        if self.show_mode == ShowMode.TestBench:
            metrics_table.add_columns(
                "Name",
                *display_metrics,
                *list(
                    self.current_test_bench.bench_model.analysis.derived_metrics.keys()
                ),
            )
            for run_configuration, metrics in aggregated_metrics:
                with open("metrics2.txt", "w") as f:
                    f.write(str(len(list(metrics.values()))) + "\n")
                metrics_table.add_row(
                    run_configuration.name,
                    *list(metrics.values()),
                )
        else:
            assert self.current_run_configuration is not None
            assert self.current_run_configuration_name is not None
            metrics_table.add_columns(
                *list(self.current_test_bench.bench_model.analysis.metrics.keys()),
                *list(
                    self.current_test_bench.bench_model.analysis.derived_metrics.keys()
                ),
            )
            for run_configuration, metrics in aggregated_metrics:
                if run_configuration.name != self.current_run_configuration_name:
                    continue
                metrics_table.add_row(*list(metrics.values()))

    def update_plot_tab(self) -> None:
        """Update the plot tab of the user interface."""
        metrics_plot_widget = self.query_one("#metrics-plot", PlotextPlot)
        metrics_plot = metrics_plot_widget.plt

        assert self.current_test_bench is not None
        aggregated_metrics = self.get_aggregated_metrics()
        if aggregated_metrics is None:
            metrics_plot.clear_figure()
            metrics_plot.title("No run data to show!")
            return

        plot_model = self.get_plot_model()
        if self.show_mode == ShowMode.RunConfiguration:
            aggregated_metrics = [
                (run_configuration, metrics)
                for run_configuration, metrics in aggregated_metrics
                if run_configuration.name == self.current_run_configuration_name
            ]
        if isinstance(plot_model, LinePlotModel):
            plot_plotext.draw_line_plot(metrics_plot, plot_model, aggregated_metrics)
        elif isinstance(plot_model, BarChartModel):
            plot_plotext.draw_bar_chart(metrics_plot, plot_model, aggregated_metrics)
        elif isinstance(plot_model, RooflinePlotModel):
            plot_plotext.draw_roofline_plot(
                metrics_plot, plot_model, aggregated_metrics
            )
        metrics_plot_widget.refresh()

    def get_plot_model(
        self,
    ) -> LinePlotModel | BarChartModel | RooflinePlotModel | None:
        """Get the model for the current plot."""
        if self.current_plot_index is None or self.current_test_bench is None:
            return None
        all_plot_models: list[LinePlotModel | BarChartModel | RooflinePlotModel] = [
            *self.current_test_bench.bench_model.analysis.line_plots,
            *self.current_test_bench.bench_model.analysis.bar_charts,
            *self.current_test_bench.bench_model.analysis.roofline_plots,
        ]
        enabled_plot_models = [
            plot_model for plot_model in all_plot_models if plot_model.enabled
        ]
        if len(enabled_plot_models) == 0:
            return None
        return enabled_plot_models[self.current_plot_index % len(enabled_plot_models)]

    def action_reload_test_plan(self) -> None:
        """Reload the test plan for the user interface."""
        self.test_plan = TestPlan(
            self.test_plan.yaml_path, self.test_plan.base_output_directory
        )
        self.initialise_test_plan_tree()
        self.update_all_tabs()

    def action_change_plot(self, offset: int) -> None:
        """Change which plot is being shown in the user interface."""
        if self.current_plot_index is None:
            self.app.bell()
            return
        # TODO: Add support for skipping disabled plots
        self.current_plot_index += offset
        self.update_plot_tab()

    def action_open_graph(self) -> None:
        """Open the current plot in matplotlib."""
        if self.current_plot_index is None:
            self.app.bell()
            return

        assert self.current_test_bench is not None
        aggregated_metrics = self.get_aggregated_metrics()
        if aggregated_metrics is None:
            return

        plot_model = self.get_plot_model()
        if self.show_mode == ShowMode.RunConfiguration:
            aggregated_metrics = [
                (run_configuration, metrics)
                for run_configuration, metrics in aggregated_metrics
                if run_configuration.name == self.current_run_configuration_name
            ]

        if isinstance(plot_model, LinePlotModel):
            plot_matplotlib.draw_line_plot(plot_model, aggregated_metrics)
        elif isinstance(plot_model, BarChartModel):
            plot_matplotlib.draw_bar_chart(plot_model, aggregated_metrics)
        elif isinstance(plot_model, RooflinePlotModel):
            plot_matplotlib.draw_roofline_plot(plot_model, aggregated_metrics)

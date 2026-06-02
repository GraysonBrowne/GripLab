# app/app.py
"""
GripLab - Tire Data Analysis Application
"""

import sys
import webbrowser
from pathlib import Path
from typing import Any, Dict, cast

import numpy as np
import pandas as pd
import panel as pn
import plotly.express as px
from panel.io import hold

from app.config import AppConfig
from app.controllers import DataController, PlotController
from converters.conventions import ConventionConverter, SignConvention
from converters.units import UnitSystem, UnitSystemConverter

# Import application modules
from core.dataio import DataManager
from ui.components import (
    AppSettingsWidgets,
    DataInfoWidgets,
    PlotControlWidgets,
    PlotSettingsWidgets,
)
from ui.modals import (
    create_plot_settings_layout,
    create_removal_dialog,
    create_settings_layout,
)
from utils.dialogs import Tk_utils
from utils.logger import logger


_cache: Dict[str, Any] = cast(Dict[str, Any], pn.state.cache)


class GripLabApp:
    """Main application orchestrator."""

    def __init__(self):
        logger.info(f"GripLab v{AppConfig.read_version()} starting")
        # Determine program directory
        if getattr(sys, "frozen", False):
            # Adjust working directory for frozen executable
            self.local_dir = Path(sys.executable).parent
        else:
            self.local_dir = Path(__file__).parent.parent
        self.program_dir = Path(__file__).parent.parent

        # Initialize configuration
        self.config_path = str(Path(self.local_dir, "config.yaml"))
        self.config = AppConfig.from_yaml(self.config_path)

        # Initialize data manager — restore from cache if available
        if "dm" not in _cache:
            _cache["dm"] = DataManager()
            _cache["session"] = {}
            logger.info("New session — initialized fresh DataManager")
        else:
            logger.info("Reconnected — restoring session from cache")

        self.dm = _cache["dm"]
        self.data_controller = DataController(self.dm, self.config)
        self.plot_controller = PlotController(self.dm, self.config)

        # Setup Panel
        self._setup_panel()

        # Initialize UI
        self._initialize_ui()
        self._layout_ui()
        self._setup_callbacks()
        self._restore_session()

        # State tracking
        self.removal_target = ""

    def _setup_panel(self):
        """Configure Panel extensions and settings."""
        pn.extension(
            "tabulator",
            "plotly",
            css_files=[
                "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css"
            ],
            notifications=True,
        )

    def _load_css(self) -> str:
        """Load custom CSS styles."""
        css_path = Path(self.program_dir, "ui", "styles.css")
        try:
            with open(css_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            logger.error("styles.css not found")
            return ""

    def _initialize_ui(self):
        """Initialize all UI components."""
        # Create main template
        self.template = pn.template.FastListTemplate(
            title="Tire Analysis Tool",
            logo=str(Path(self.program_dir, "docs", "images", "GripLab_Banner.png")),
            favicon=str(Path(self.program_dir, "docs", "images", "GripLab_Icon.ico")),
            sidebar_width=420,
            accent="#283442",
            theme=self.config.theme,
            theme_toggle=False,
            raw_css=[self._load_css()],
        )

        # Initialize widget groups
        self.plot_widgets = PlotControlWidgets()
        self.data_widgets = DataInfoWidgets()
        self.plot_settings_widgets = PlotSettingsWidgets()
        self.app_settings_widgets = AppSettingsWidgets(self.config)

        # Initialize other widgets
        self._init_header_widgets()
        self._init_sidebar_widgets()
        self._init_main_view()

        # Modal container
        self.modal_content = pn.Column()

    def _restore_session(self):
        """Restore widget state and re-plot from cached session."""
        session = _cache.get("session", {})
        if not session or not self.dm.list_datasets():
            return

        logger.info("Restoring session state from cache")

        # Populate options first, then restore values
        self._update_channel_options()
        self._update_data_select_options()
        self.plot_widgets.restore(session)
        self.plot_settings_widgets.restore(session)

        # Restore table selection — guard against stale indices
        cached_selection = session.get("data_selection", [])
        table_len = len(self.dm.list_datasets())
        self.data_table.selection = [i for i in cached_selection if i < table_len]

        # Re-plot
        self._on_plot_data(clicks=None)

    def _save_session(self):
        """Save current widget state to cache."""
        _cache["session"] = {
            "plot_type":     self.plot_widgets.plot_type.value,
            "x_channel":    self.plot_widgets.x_axis.value,
            "y_channel":    self.plot_widgets.y_axis.value,
            "z_channel":    self.plot_widgets.z_axis.value,
            "c_channel":    self.plot_widgets.color_axis.value,
            "downsample":   self.plot_widgets.downsample_slider.value,
            "cmd_channels": [s.value for s in self.plot_widgets.cmd_selects],
            "cmd_options":  [m.options for m in self.plot_widgets.cmd_multi_selects],
            "cmd_values":   [m.value for m in self.plot_widgets.cmd_multi_selects],
            "data_selection": self.data_table.selection,
            "title": self.plot_settings_widgets.title.value,
            "subtitle": self.plot_settings_widgets.subtitle.value,
            "x_label": self.plot_settings_widgets.x_label.value,
            "y_label": self.plot_settings_widgets.y_label.value,
            "z_label": self.plot_settings_widgets.z_label.value,
            "color_label": self.plot_settings_widgets.c_label.value,
            "color_map": self.plot_settings_widgets.color_map.value,
            "font_size": self.plot_settings_widgets.font_size.value,
            "marker_size": self.plot_settings_widgets.marker_size.value,
            "marker_opacity": self.plot_settings_widgets.marker_opacity.value,
        }

    def _init_header_widgets(self):
        """Initialize header widgets."""
        file_menu_items = [
            ("Save Session", "save_session"),
            ("Import Session", "import_session"),
        ]
        self.file_menu = pn.widgets.MenuButton(
            name="File",
            items=file_menu_items,
            button_type="primary",
            width=100,
        )
        self.settings_btn = pn.widgets.Button(
            name="Settings", button_type="primary", width=100
        )
        help_menu_items = [
            ("Sign Convention", "signcon"),
            ("User Guide", "userguide"),
            ("Discussion Board", "discuss"),
            ("Report An Issue", "issue"),
            ("TTC Forum", "ttc"),
            None,
            (f"v{AppConfig.read_version()}", "version"),
        ]
        self.help_menu = pn.widgets.MenuButton(
            name="Help",
            items=help_menu_items,
            button_type="primary",
            width=100,
        )

    def _init_sidebar_widgets(self):
        """Initialize sidebar widgets."""
        self.import_btn = pn.widgets.Button(name="Import Data", button_type="primary")

        self.data_table = pn.widgets.Tabulator(
            pd.DataFrame(columns=["Dataset", ""]),
            buttons={"trash": '<i class="fa fa-trash"></i>'},
            show_index=False,
            configuration={"columnDefaults": {"headerSort": False}},
            selectable="checkbox",
            sizing_mode="stretch_both",
            min_height=150,
            editors={"": None, "trash": None},
            widths={"Dataset": 279, "": 40, "trash": 40},
        )

        # Repopulate table if dm has cached datasets
        if self.dm.list_datasets():
            self._refresh_data_table()

    def _init_main_view(self):
        """Initialize main view with plot pane."""
        theme_name = getattr(self.template.theme, "name", None)
        defaults = cast(Any, px.defaults)

        defaults.template = (
            "plotly_dark" if str(theme_name) == "DarkTheme" else "plotly_white"
        )
        self.plot_pane = pn.pane.Plotly(px.scatter(), sizing_mode="stretch_both")

    def _layout_ui(self):
        """Layout all UI components in the template."""
        # Header

        header_object = cast(list, self.template.header)
        header_object.append(
            pn.Row(
                pn.layout.HSpacer(),
                self.file_menu,
                self.settings_btn,
                self.help_menu,
            )
        )

        # Sidebar - Plot tab
        plot_tab = pn.Column(
            pn.Row(
                self.plot_widgets.plot_type,
                self.plot_widgets.settings_button,
                self.plot_widgets.plot_button,
            ),
            pn.Row(
                pn.GridBox(
                    self.plot_widgets.x_axis,
                    self.plot_widgets.y_axis,
                    self.plot_widgets.z_axis,
                    self.plot_widgets.color_axis,
                    ncols=2,
                    sizing_mode="stretch_width",
                ),
                pn.Column(
                    self.plot_widgets.downsample_slider,
                    self.plot_widgets.node_count,
                    width=160,
                ),
            ),
            pn.GridBox(
                *self.plot_widgets.cmd_selects,
                *self.plot_widgets.cmd_multi_selects,
                ncols=4,
            ),
            name="Plot Data",
        )

        # Sidebar - Data Info tab
        data_tab = pn.Column(
            self.data_widgets.data_select,
            pn.Row(self.data_widgets.name_input, self.data_widgets.color_picker),
            pn.Row(self.data_widgets.tire_id_input, self.data_widgets.rim_width_input),
            self.data_widgets.notes_input,
            self.data_widgets.update_button,
            name="Data Info",
        )

        self.info_tabs = pn.layout.Tabs(plot_tab, data_tab)

        sidebar_object = cast(list, self.template.sidebar)
        sidebar_object.append(
            pn.Column(
                self.import_btn, self.data_table, pn.layout.Divider(), self.info_tabs
            )
        )

        # Main area
        main_object = cast(list, self.template.main)
        main_object.append(pn.Column(self.plot_pane))

        # Modal
        modal_object = cast(list, self.template.modal)
        modal_object.append(self.modal_content)

    def _setup_callbacks(self):
        """Setup all widget callbacks."""
        # Main action callbacks
        pn.bind(self._on_import_data, self.import_btn.param.clicks, watch=True)
        pn.bind(self._on_settings_click, self.settings_btn.param.clicks, watch=True)
        pn.bind(
            self._on_plot_data, self.plot_widgets.plot_button.param.clicks, watch=True
        )
        pn.bind(
            self._on_plot_settings,
            self.plot_widgets.settings_button.param.clicks,
            watch=True,
        )

        # Widget change callbacks
        pn.bind(
            self._on_plot_type_change,
            self.plot_widgets.plot_type.param.value,
            watch=True,
        )
        pn.bind(
            self._on_data_select, self.data_widgets.data_select.param.value, watch=True
        )
        pn.bind(
            self._on_update_data,
            self.data_widgets.update_button.param.clicks,
            watch=True,
        )
        pn.bind(
            self._on_demo_mode_change,
            self.app_settings_widgets.demo_switch.param.value,
            watch=True,
        )

        # Table callbacks
        self.data_table.on_click(self._on_table_trash_click, column="trash")
        self.data_table.on_click(self._on_table_color_click, column="")
        self.data_table.on_edit(self._on_table_edit)
        self._apply_table_styling()

        # File menu callback
        pn.bind(self._on_file_menu, self.file_menu.param.clicked, watch=True)

        # Help menu callback
        pn.bind(self._on_help_menu, self.help_menu.param.clicked, watch=True)

        # Command selector callbacks
        for selector in self.plot_widgets.cmd_selects:
            pn.bind(self._update_cmd_options, selector.param.value, watch=True)

        # Unit/Sign convention callbacks
        pn.bind(
            self._update_cmd_options,
            self.app_settings_widgets.unit_select.param.value,
            watch=True,
        )
        pn.bind(
            self._update_cmd_options,
            self.app_settings_widgets.sign_select.param.value,
            watch=True,
        )

    # ===========================
    # Main Callback Methods
    # ===========================

    def _on_import_data(self, clicks):
        """Handle data import button click."""
        files = Tk_utils().select_file(
            filetypes=[("MATLAB/ASCII Data Files", "*.mat *.dat *.txt")],
            initialdir=self.config.data_dir,
            icon=str(Path(self.program_dir, "docs", "images", "GripLab_Icon.ico")),
        )

        if not files:
            return

        imported = self.data_controller.import_data(list(files))
        if imported:
            self._refresh_data_table()
            self._update_channel_options()
            self._update_data_select_options()

            # Select newly imported datasets
            current_selection = self.data_table.selection
            table_value = self.data_table.value
            if isinstance(table_value, pd.DataFrame):
                new_indices = list(
                    range(
                        len(table_value) - len(imported),
                        len(table_value),
                    )
                )
                self.data_table.selection = current_selection + new_indices

    def _on_settings_click(self, clicks):
        """Open settings modal."""
        layout = create_settings_layout(
            self.app_settings_widgets, self._on_save_settings, self._on_select_data_dir
        )
        self.modal_content.objects = [layout]
        self.template.open_modal()

    def _on_save_settings(self, clicks):
        """Save application settings."""
        # Update config from widgets
        theme_value = self.app_settings_widgets.theme_select.value
        if theme_value is not None:
            self.config.theme = theme_value
        self.config.unit_system = UnitSystem(
            self.app_settings_widgets.unit_select.value
        )
        self.config.sign_convention = SignConvention(
            self.app_settings_widgets.sign_select.value
        )
        self.config.demo_mode = bool(self.app_settings_widgets.demo_switch.value)
        self.config.data_dir = self.app_settings_widgets.data_dir_input.value

        # Update colorway and colormap
        colorway_options = getattr(
            self.app_settings_widgets.colorway_select, "options", None
        )
        if colorway_options and isinstance(colorway_options, dict):
            for name, value in colorway_options.items():
                if value == self.app_settings_widgets.colorway_select.value:
                    self.config.colorway = name
                    break

        colormap_options = getattr(
            self.plot_settings_widgets.color_map, "options", None
        )
        if colormap_options and isinstance(colormap_options, dict):
            for name, value in colormap_options.items():
                if value == self.plot_settings_widgets.color_map.value:
                    self.config.colormap = name
                    break

        # Save to file
        self.config.save(self.config_path)
        self.template.close_modal()

    def _on_plot_data(self, clicks):
        """Handle plot data button click."""
        if not self.data_table.selection:
            if clicks is not None:      # only notify on user action, not restore
                if pn.state.notifications:
                    pn.state.notifications.warning("Select a dataset to plot", duration=4000)
            return

        # Collect all widget references for the plot controller
        widgets = {
            "data_table": self.data_table,
            "plot_controls": self.plot_widgets,
            "plot_settings": self.plot_settings_widgets,
            "settings": self.app_settings_widgets,
        }

        plot_params = self.plot_controller.get_plot_parameters(widgets, self.config)
        fig, node_count = self.plot_controller.create_plot(plot_params)

        if fig:
            self.plot_pane.object = fig
            self.plot_widgets.node_count.value = str(node_count)
            self._save_session()

    def _on_plot_settings(self, clicks):
        """Open plot settings modal."""
        plot_type = self.plot_widgets.plot_type.value
        if plot_type is not None:
            self.plot_settings_widgets.update_axis_state(plot_type)
        layout = create_plot_settings_layout(self.plot_settings_widgets)
        self.modal_content.objects = [layout]
        self.template.open_modal()

    @hold()
    def _on_plot_type_change(self, plot_type):
        """Handle plot type change."""
        self.plot_widgets.update_plot_type_state(plot_type)
        self.plot_settings_widgets.update_axis_state(plot_type)

    @hold()
    def _on_data_select(self, dataset_name):
        """Handle dataset selection in data info tab."""
        if not dataset_name:
            self.data_widgets.reset()
            return

        info = self.data_controller.get_dataset_info(
            dataset_name, self.config.demo_mode
        )
        if info:
            self.data_widgets.name_input.value = info["name"]
            self.data_widgets.tire_id_input.value = info["tire_id"]
            self.data_widgets.rim_width_input.value = info["rim_width"]
            self.data_widgets.notes_input.value = info["notes"]
            self.data_widgets.color_picker.value = info["node_color"]
            self.data_widgets.enable_all(True)
        else:
            self.data_widgets.reset()

    @hold()
    def _on_update_data(self, clicks):
        """Handle dataset update button click."""
        dataset_name = self.data_widgets.data_select.value
        if not dataset_name:
            logger.warning("No dataset selected to update")
            return

        updates = {
            "name": self.data_widgets.name_input.value,
            "tire_id": self.data_widgets.tire_id_input.value,
            "rim_width": self.data_widgets.rim_width_input.value,
            "notes": self.data_widgets.notes_input.value,
            "node_color": self.data_widgets.color_picker.value,
        }

        success = self.data_controller.update_dataset_info(
            dataset_name, updates, self.config.demo_mode
        )

        if success:
            self._refresh_data_table()
            self._update_data_select_options()
            self.data_widgets.data_select.value = updates["name"]
        else:
            self._refresh_data_table()
            self.data_widgets.name_input.value = dataset_name
            if pn.state.notifications:
                pn.state.notifications.warning(
                    "Dataset name must be unique", duration=4000
                )

    def _on_demo_mode_change(self, demo_mode):
        """Handle demo mode toggle."""
        self.config.demo_mode = bool(demo_mode)
        self._refresh_data_table()
        self._update_data_select_options()

    # ===========================
    # Table Callbacks
    # ===========================

    def _on_table_trash_click(self, event):
        """Handle trash button click in data table."""
        self.removal_target = self.dm.list_datasets()[event.row]

        layout = create_removal_dialog(
            self.removal_target,
            self._confirm_removal,
            lambda x: self.template.close_modal(),
        )
        self.modal_content.objects = [layout]
        self.template.open_modal()

    def _on_table_color_click(self, event):
        """Handle color cell click in data table."""
        self.info_tabs.active = 1  # Switch to Data Info tab

        if self.config.demo_mode:
            self.data_widgets.data_select.value = self.dm.list_demo_names()[event.row]
        else:
            self.data_widgets.data_select.value = self.dm.list_datasets()[event.row]

    @hold()
    def _on_table_edit(self, event):
        """Handle inline editing in data table."""
        if self.config.demo_mode:
            self.data_widgets.data_select.value = self.dm.list_demo_names()[event.row]
        else:
            self.data_widgets.data_select.value = self.dm.list_datasets()[event.row]

        self.data_widgets.name_input.value = event.value
        self._on_update_data(clicks=None)

    def _confirm_removal(self, clicks):
        """Confirm and execute dataset removal."""
        if self.data_controller.remove_dataset(self.removal_target):
            self._refresh_data_table()
            self._update_channel_options()
            self._update_data_select_options()
        self.template.close_modal()

    # ===========================
    # Helper Methods
    # ===========================
    def _on_export_session(self):
        path = Tk_utils().save_file(
            defaultextension=".grip",
            filetypes=[("GripLab Session", "*.grip")],
            initialdir=self.config.data_dir,
            icon=str(Path(self.program_dir, "docs", "images", "GripLab_Icon.ico")),
        )
        if path:
            self._save_session()
            self.data_controller.export_session(path)

    def _on_import_session(self):
        files = Tk_utils().select_file(
            filetypes=[("GripLab Session", "*.grip")],
            initialdir=self.config.data_dir,
            icon=str(Path(self.program_dir, "docs", "images", "GripLab_Icon.ico")),
        )
        if files:
            session = self.data_controller.import_session(str(files[0]))
            if session is not None:
                self.dm = self.data_controller.dm       # sync GripLabApp reference
                self.plot_controller.dm = self.data_controller.dm  # sync PlotController reference
                self._refresh_data_table()
                self._update_channel_options()
                self._update_data_select_options()
                self.plot_widgets.restore(session)
                self.plot_settings_widgets.restore(session)
                cached_selection = session.get("data_selection", [])
                table_len = len(self.dm.list_datasets())
                self.data_table.selection = [i for i in cached_selection if i < table_len]
                self._on_plot_data(clicks=None)
    
    def _on_file_menu(self, clicked):
        """Handle file menu selection."""
        actions = {
            "save_session": self._on_export_session,
            "import_session": self._on_import_session,
        }
        action = actions.get(clicked)
        if action:
            logger.info(f"File menu action: {clicked}")
            action()

    def _on_help_menu(self, clicked):
        """Handle help menu selection."""
        actions = {
            "signcon": lambda: webbrowser.open_new(
                str(Path(self.program_dir, "docs", "Sign_Convention.pdf"))
            ),
            "userguide": lambda: webbrowser.open_new(
                "https://github.com/GraysonBrowne/GripLab/blob/main/docs/USER_GUIDE.md"
            ),
            "discuss": lambda: webbrowser.open_new(
                "https://github.com/GraysonBrowne/GripLab/discussions"
            ),
            "issue": lambda: webbrowser.open_new(
                "https://github.com/GraysonBrowne/GripLab/issues"
            ),
            "ttc": lambda: webbrowser.open_new("https://www.fsaettc.org/"),
        }

        action = actions.get(clicked)
        if action:
            logger.info(f"Opening help resource: {clicked}")
            action()

    def _on_select_data_dir(self, clicks):
        """Handle data directory selection."""
        directory = Tk_utils().select_dir(
            initialdir=self.config.data_dir,
            icon=str(Path(self.program_dir, "docs", "images", "GripLab_Icon.ico")),
        )
        if directory:
            self.app_settings_widgets.data_dir_input.value = directory
            self.config.data_dir = directory

    @hold()
    def _update_cmd_options(self, event):
        """Update command channel options based on selection."""
        try:
            channels = self.dm.get_channels(self.dm.list_datasets())
            cmd_channels = [ch for ch in channels if ch.startswith("Cmd")]

            # Get current selections
            selected = [s.value for s in self.plot_widgets.cmd_selects]

            # Update each selector's options
            for i, selector in enumerate(self.plot_widgets.cmd_selects):
                excluded = set(selected) - {selected[i]}
                selector.options = [""] + [
                    ch for ch in cmd_channels if ch not in excluded
                ]

                # Update corresponding multi-select options
                self._update_cmd_multi_select(i, cast(str, selector.value))

        except Exception as e:
            logger.error(f"Error updating command options: {e}", exc_info=True)

    def _update_cmd_multi_select(self, index: int, channel: str):
        """Update command multi-select options based on data."""
        selection = self.data_table.selection
        if not selection:
            return

        names = [self.dm.list_datasets()[idx] for idx in selection]
        data_values = []

        for name in names:
            dataset = self.dm.get_dataset(name)
            dataset = UnitSystemConverter.convert_dataset(
                dataset,
                to_system=UnitSystem(self.app_settings_widgets.unit_select.value),
            )
            dataset = ConventionConverter.convert_dataset_convention(
                dataset,
                target_convention=SignConvention(
                    self.app_settings_widgets.sign_select.value
                ),
            )

            if channel in dataset.channels:
                col_idx = dataset.channels.index(channel)
                data_values.extend(dataset.data[:, col_idx])
            else:
                data_values.extend([])

        unique_values = sorted(
            np.unique(data_values).astype(np.int64).tolist(), key=abs
        )
        options = {str(v): i for i, v in enumerate(unique_values)}

        # Preserve current selection
        current_value = self.plot_widgets.cmd_multi_selects[index].value
        self.plot_widgets.cmd_multi_selects[index].options = options
        if options:
            self.plot_widgets.cmd_multi_selects[index].value = current_value
        else:
            self.plot_widgets.cmd_multi_selects[index].value = []
        self.plot_widgets.cmd_multi_selects[index].param.trigger("value")

    def _refresh_data_table(self):
        """Refresh the data table display."""
        if self.config.demo_mode:
            datasets = self.dm.list_demo_names()
        else:
            datasets = self.dm.list_datasets()

        self.data_table.value = pd.DataFrame(
            {"Dataset": datasets, "": [""] * len(datasets)}
        )

        self._apply_table_styling()

    def _apply_table_styling(self):
        """Apply color styling to data table."""

        def cell_color(column):
            if column.name == "":
                return [f"background-color: {color}" for color in self.dm.list_colors()]
            return [""] * len(column)

        if self.data_table.style is not None:
            self.data_table.style.apply(cell_color)

    def _update_channel_options(self):
        """Update channel selection dropdowns."""
        channels = self.dm.get_channels(self.dm.list_datasets())

        self.plot_widgets.x_axis.options = channels
        self.plot_widgets.y_axis.options = channels
        self.plot_widgets.z_axis.options = channels
        self.plot_widgets.color_axis.options = channels

        self._update_cmd_options(None)

    def _update_data_select_options(self):
        """Update data select dropdown options."""
        if self.config.demo_mode:
            options = [""] + self.dm.list_demo_names()
        else:
            options = [""] + self.dm.list_datasets()

        self.data_widgets.data_select.options = options

    # ===========================
    # Public Methods
    # ===========================

    def serve(self):
        """Serve the application."""
        if getattr(sys, "frozen", False):
            # Running as frozen executable
            server = self.template.show(threaded=True)

            def on_session_destroyed(session_context):
                logger.info("Shutting down server...")
                server.stop()

            # Need to prevent shutting down on page refresh
            # pn.state.on_session_destroyed(on_session_destroyed)
        else:
            # Running in development mode
            self.template.servable(title="GripLab")

        return self.template

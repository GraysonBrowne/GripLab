# app/app.py
"""
GripLab - Tire Data Analysis Application
"""

import sys
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, cast

import numpy as np
import pandas as pd
import panel as pn
import plotly.express as px
from panel.io import hold

from app.config import AppConfig
from app.controllers import DataController, PlotController
from app.models import PageType, ScatterPage
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
        logger.info(f"GripLab v{AppConfig.version} starting")

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
        self.pages: List[PageType] = []
        self.data_widgets = DataInfoWidgets()
        self.app_settings_widgets = AppSettingsWidgets(self.config)

        # Initialize other widgets
        self._init_header_widgets()
        self._init_sidebar_widgets()
        self._init_main_view()
        self.main_tabs = pn.Tabs(dynamic=True, sizing_mode="stretch_both")
        self.plot_sidebar_tab = pn.Column(name="Plot Data")
        self._add_scatter_tab()

        # Modal container
        self.modal_content = pn.Column()

    def _restore_session(self):
        """Restore widget state and re-plot from cached session."""
        session = _cache.get("session", {})
        if not session or not self.dm.list_datasets():
            return

        logger.info("Restoring session state from cache")

        # Restore table selection — guard against stale indices
        cached_selection = session.get("data_selection", [])
        table_len = len(self.dm.list_datasets())
        self.data_table.selection = [i for i in cached_selection if i < table_len]

        # Populate options
        self._update_channel_options()
        self._update_data_select_options()

        # Re-plot
        scatter_pages = [p for p in self.pages if isinstance(p, ScatterPage)]
        saved_pages = [p for p in session.get("pages", []) if p.get("type") == "scatter"]
        for i, page in enumerate(scatter_pages):
            if i < len(saved_pages):
                page.controls.restore(saved_pages[i])
                page.settings.restore(saved_pages[i])
                self._on_plot_scatter(page, clicks=None)

    def _save_session(self):
        """Save current widget state to cache."""
        _cache["session"] = {
            "data_selection": self.data_table.selection,
            "pages": [
                {
                    "type": "scatter",
                    "name": page.name,
                    "plot_type": page.controls.plot_type.value,
                    "x_channel": page.controls.x_axis.value,
                    "y_channel": page.controls.y_axis.value,
                    "z_channel": page.controls.z_axis.value,
                    "c_channel": page.controls.color_axis.value,
                    "downsample": page.controls.downsample_slider.value,
                    "cmd_channels": [s.value for s in page.controls.cmd_selects],
                    "cmd_options": [m.options for m in page.controls.cmd_multi_selects],
                    "cmd_values": [m.value for m in page.controls.cmd_multi_selects],
                    "title": page.settings.title.value,
                    "subtitle": page.settings.subtitle.value,
                    "x_label": page.settings.x_label.value,
                    "y_label": page.settings.y_label.value,
                    "z_label": page.settings.z_label.value,
                    "c_label": page.settings.c_label.value,
                    "color_map": page.settings.color_map.value,
                    "font_size": page.settings.font_size.value,
                    "marker_size": page.settings.marker_size.value,
                    "marker_opacity": page.settings.marker_opacity.value,
                }
                if isinstance(page, ScatterPage) else
                {
                    "type": "time_series",
                    "name": page.name,
                    "subplots": [
                        {"channels": s.channels, "label": s.label}
                        for s in page.subplots
                    ],
                }
                for page in self.pages
            ]
        }

    def _init_header_widgets(self):
        """Initialize header widgets."""
        file_menu_items = [
            ("Import Data", "import_data"),
            ("Save Session", "save_session"),
            ("Import Session", "import_session"),
        ]
        self.file_menu = pn.widgets.MenuButton(
            name="File",
            items=file_menu_items,
            button_type="primary",
            width=100,
            margin=(5, 5),
        )
        insert_menu_items = [
            ("Scatter Plot", "scatter_plot"),
            ("Time Series", "time_series"),
        ]
        self.insert_menu = pn.widgets.MenuButton(
            name="Insert",
            items=insert_menu_items,
            button_type="primary",
            width=100,
            margin=(5, 5),
        )
        self.settings_btn = pn.widgets.Button(
            name="Settings",
            button_type="primary",
            width=100,
            margin=(5, 5),
        )
        help_menu_items = [
            ("Sign Convention", "signcon"),
            ("User Guide", "userguide"),
            ("Discussion Board", "discuss"),
            ("Report An Issue", "issue"),
            ("TTC Forum", "ttc"),
            None,
            (f"v{AppConfig.version}", "version"),
        ]
        self.help_menu = pn.widgets.MenuButton(
            name="Help",
            items=help_menu_items,
            button_type="primary",
            width=100,
            margin=(5, 5),
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

    def _layout_ui(self):
        """Layout all UI components in the template."""
        # Header

        header_object = cast(list, self.template.header)
        header_object.append(
            pn.Row(
                pn.layout.HSpacer(),
                self.file_menu,
                self.insert_menu,
                self.settings_btn,
                self.help_menu,
            )
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

        self.info_tabs = pn.layout.Tabs(self.plot_sidebar_tab, data_tab)

        sidebar_object = cast(list, self.template.sidebar)
        sidebar_object.append(
            pn.Column(
                self.import_btn, self.data_table, pn.layout.Divider(), self.info_tabs
            )
        )

        # Main area
        main_object = cast(list, self.template.main)
        main_object.append(self.main_tabs)

        # Modal
        modal_object = cast(list, self.template.modal)
        modal_object.append(self.modal_content)

    def _load_sidebar_for_page(self, page: PageType):
        if isinstance(page, ScatterPage):
            self.plot_sidebar_tab.objects = [
                page.controls.plot_type,
                pn.Row(page.controls.x_axis, page.controls.y_axis),
                page.controls.z_axis,
                page.controls.color_axis,
                *page.controls.cmd_selects,
                *page.controls.cmd_multi_selects,
                page.controls.downsample_slider,
                pn.Row(page.controls.plot_button, page.controls.settings_button),
                page.controls.node_count,
            ]

    def _setup_callbacks(self):
        """Setup all widget callbacks."""
        # Main action callbacks
        pn.bind(self._on_import_data, self.import_btn.param.clicks, watch=True)
        pn.bind(self._on_settings_click, self.settings_btn.param.clicks, watch=True)
        pn.bind(self._on_main_tab_change, self.main_tabs.param.active, watch=True)

        # Widget change callbacks
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

        # Insert menu callback
        pn.bind(self._on_insert_menu, self.insert_menu.param.clicked, watch=True)

        # Help menu callback
        pn.bind(self._on_help_menu, self.help_menu.param.clicked, watch=True)

        # Unit/Sign convention callbacks
        pn.bind(
            self._update_all_cmd_options,
            self.app_settings_widgets.unit_select.param.value,
            watch=True,
        )
        pn.bind(
            self._update_all_cmd_options,
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

        # Save to file
        self.config.save(self.config_path)
        self.template.close_modal()

    def _on_plot_settings(self, page, clicks):
        """Open plot settings modal."""
        plot_type = page.controls.plot_type.value
        if plot_type is not None:
            page.settings.update_axis_state(plot_type)
        layout = create_plot_settings_layout(page.settings)
        self.modal_content.objects = [layout]
        self.template.open_modal()

    @hold()
    def _on_plot_type_change(self, page, plot_type):
        """Handle plot type change."""
        page.controls.update_plot_type_state(plot_type)
        page.settings.update_axis_state(plot_type)

    def _on_main_tab_change(self, active):
        if 0 <= active < len(self.pages):
            page = self.pages[active]
            self._load_sidebar_for_page(page)

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
        if not path:
            return
        else:
            self._save_session()
            if self.data_controller.export_session(path):
                if pn.state.notifications:
                    pn.state.notifications.success(
                        f"Session exported as {Path(path).name}", duration=4000
                    )
            else:
                if pn.state.notifications:
                    pn.state.notifications.error(
                        "Failed to export session.", duration=4000
                    )

    def _on_import_session(self):
        files = Tk_utils().select_file(
            filetypes=[("GripLab Session", "*.grip")],
            initialdir=self.config.data_dir,
            icon=str(Path(self.program_dir, "docs", "images", "GripLab_Icon.ico")),
        )
        if files:
            session = self.data_controller.import_session(str(files[0]))
            if session is not None:
                self.dm = self.data_controller.dm  # sync GripLabApp reference
                self.plot_controller.dm = (
                    self.data_controller.dm
                )  # sync PlotController reference
                cached_selection = session.get("data_selection", [])
                table_len = len(self.dm.list_datasets())
                self.data_table.selection = [
                    i for i in cached_selection if i < table_len
                ]
                self._refresh_data_table()
                self._update_channel_options()
                self._update_data_select_options()
                scatter_pages = [p for p in self.pages if isinstance(p, ScatterPage)]
                saved_pages = [p for p in session.get("pages", []) if p.get("type") == "scatter"]
                for i, page in enumerate(scatter_pages):
                    if i < len(saved_pages):
                        page.controls.restore(saved_pages[i])
                        page.settings.restore(saved_pages[i])
                        self._on_plot_scatter(page, clicks=None)
                if pn.state.notifications:
                    pn.state.notifications.success(
                        f"Session imported from {Path(files[0]).name}", duration=4000
                    )
            else:
                if pn.state.notifications:
                    pn.state.notifications.error(
                        "Failed to import session.", duration=4000
                    )

    def _on_file_menu(self, clicked):
        """Handle file menu selection."""
        actions = {
            "import_data": lambda: self._on_import_data(clicks=None),
            "save_session": self._on_export_session,
            "import_session": lambda: self._on_import_session(),
        }
        action = actions.get(clicked)
        if action:
            logger.info(f"File menu action: {clicked}")
            action()

    def _on_plot_scatter(self, page: ScatterPage, clicks):
        if not self.data_table.selection:
            if clicks is not None:
                if pn.state.notifications:
                    pn.state.notifications.warning("Select a dataset to plot",
                                                   duration=4000)
            return
        widgets = {
            "data_table": self.data_table,
            "plot_controls": page.controls,
            "plot_settings": page.settings,
            "settings": self.app_settings_widgets,
        }
        plot_params = self.plot_controller.get_plot_parameters(widgets, self.config)
        fig, node_count = self.plot_controller.create_plot(plot_params)
        if fig:
            page.pane.object = fig
            page.controls.node_count.value = str(node_count)

    def _wire_scatter_callbacks(self, page: ScatterPage):
        pn.bind(
            lambda clicks: self._on_plot_scatter(page, clicks),
            page.controls.plot_button.param.clicks,
            watch=True,
        )
        for selector in page.controls.cmd_selects:
            pn.bind(
                lambda event, p=page: self._update_cmd_options(p, event),
                selector.param.value,
                watch=True,
            )
        pn.bind(
            lambda clicks, p=page: self._on_plot_settings(p, clicks),
            page.controls.settings_button.param.clicks,
            watch=True,
        )
        pn.bind(
            lambda plot_type, p=page: self._on_plot_type_change(p, plot_type),
            page.controls.plot_type.param.value,
            watch=True,
        )

    def _add_scatter_tab(self):
        count = sum(1 for p in self.pages if isinstance(p, ScatterPage)) + 1
        page = ScatterPage(
            name=f"Scatter {count}",
            controls=PlotControlWidgets(),
            settings=PlotSettingsWidgets(),
            pane=pn.pane.Plotly(sizing_mode="stretch_both"),
        )
        self._wire_scatter_callbacks(page)
        self.pages.append(page)
        self.main_tabs.append((page.name, page.pane))
        self.main_tabs.active = len(self.main_tabs) - 1
        self._update_channel_options()
        self._load_sidebar_for_page(page)

    def _on_insert_menu(self, clicked):
        actions = {
            "scatter_plot": self._add_scatter_tab,
            #"time_series": self._add_time_series_tab,
        }
        action = actions.get(clicked)
        if action:
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
    def _update_cmd_options(self, page: PageType, event):
        """Update command channel options based on selection."""
        try:
            channels = self.dm.get_channels(self.dm.list_datasets())
            cmd_channels = [ch for ch in channels if ch.startswith("Cmd")]

            # Get current selections
            selected = [s.value for s in page.controls.cmd_selects]

            # Update each selector's options
            for i, selector in enumerate(page.controls.cmd_selects):
                excluded = set(selected) - {selected[i]}
                selector.options = [""] + [
                    ch for ch in cmd_channels if ch not in excluded
                ]

                # Update corresponding multi-select options
                self._update_cmd_multi_select(page, i, cast(str, selector.value))

        except Exception as e:
            logger.error(f"Error updating command options: {e}", exc_info=True)

    @hold()
    def _update_all_cmd_options(self, event=None):
        for page in self.pages:
            if isinstance(page, ScatterPage):
                self._update_cmd_options(page, event)

    def _update_cmd_multi_select(self, page: PageType, index: int, channel: str):
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
        current_value = page.controls.cmd_multi_selects[index].value
        page.controls.cmd_multi_selects[index].options = options
        if options:
            page.controls.cmd_multi_selects[index].value = current_value
        else:
            page.controls.cmd_multi_selects[index].value = []
        page.controls.cmd_multi_selects[index].param.trigger("value")

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
        for page in self.pages:
            if isinstance(page, ScatterPage):
                page.controls.x_axis.options = channels
                page.controls.y_axis.options = channels
                page.controls.z_axis.options = channels
                page.controls.color_axis.options = channels
        self._update_all_cmd_options(None)

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

            pn.state.on_session_destroyed(on_session_destroyed)
        else:
            # Running in development mode
            self.template.servable(title="GripLab")

        return self.template

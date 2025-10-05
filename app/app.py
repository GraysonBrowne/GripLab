# app/app.py
"""
GripLab - Tire Data Analysis Application
"""

import sys
import webbrowser
from pathlib import Path
import numpy as np
import pandas as pd
import panel as pn
import plotly.express as px
from panel.io import hold

# Import application modules
import core.dataio as IO
from converters.conventions import ConventionConverter
from utils.logger import logger
from utils.dialogs import Tk_utils
from converters.units import UnitSystemConverter

# Import new modular components
from app.config import AppConfig
from ui.components import (
    PlotControlWidgets, DataInfoWidgets, 
    PlotSettingsWidgets, AppSettingsWidgets
)
from app.controllers import DataController, PlotController
from ui.modals import (
    create_settings_layout, create_plot_settings_layout, 
    create_removal_dialog
)


class GripLabApp:
    """Simplified main application class for GripLab."""
    
    def __init__(self, config_path: str = "config.yaml"):
        # Initialize configuration
        self.config = AppConfig.from_yaml(config_path)
        self.config_path = config_path
        
        # Initialize data manager and controllers
        self.dm = IO.DataManager()
        self.data_controller = DataController(self.dm, self.config)
        self.plot_controller = PlotController(self.dm, self.config)
        
        # Setup Panel
        self._setup_panel()
        
        # Initialize UI
        self._initialize_ui()
        self._layout_ui()
        self._setup_callbacks()
        
        # State tracking
        self.removal_target = ""
        
    def _setup_panel(self):
        """Configure Panel extensions and settings."""
        pn.extension(
            "tabulator", "plotly",
            css_files=["https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css"],
            notifications=True
        )
    
    def _load_css(self) -> str:
        """Load custom CSS styles."""
        css_path = Path(Path(__file__).parent.parent, "ui", "styles.css")
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
            title="GripLab",
            sidebar_width=420,
            accent="#2A3F5F",
            theme=self.config.theme,
            raw_css=[self._load_css()]
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
    
    def _init_header_widgets(self):
        """Initialize header widgets."""
        menu_items = [
            ("Sign Convention", "signcon"),
            ("GitHub Repository", "readme"),
            ("Discussion Board", "discuss"),
            ("Report An Issue", "issue"),
            ("TTC Forum", "ttc")
        ]
        self.help_menu = pn.widgets.MenuButton(
            name="Help", items=menu_items, button_type="primary", width=100
        )
        self.settings_btn = pn.widgets.Button(
            name="Settings", button_type="primary", width=100
        )
    
    def _init_sidebar_widgets(self):
        """Initialize sidebar widgets."""
        self.import_btn = pn.widgets.Button(
            name="Import Data", button_type="primary"
        )
        
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
    
    def _init_main_view(self):
        """Initialize main view with plot pane."""
        px.defaults.template = (
            "plotly_dark" if self.template.theme.name == "DarkTheme" else "plotly_white"
        )
        self.plot_pane = pn.pane.Plotly(
            px.scatter(), sizing_mode="stretch_both"
        )
    
    def _layout_ui(self):
        """Layout all UI components in the template."""
        # Header
        self.template.header.append(
            pn.Row(pn.layout.HSpacer(), self.settings_btn, self.help_menu)
        )
        
        # Sidebar - Plot tab
        plot_tab = pn.Column(
            pn.Row(
                self.plot_widgets.plot_type,
                self.plot_widgets.settings_button,
                self.plot_widgets.plot_button
            ),
            pn.Row(
                pn.GridBox(
                    self.plot_widgets.x_axis,
                    self.plot_widgets.y_axis,
                    self.plot_widgets.z_axis,
                    self.plot_widgets.color_axis,
                    ncols=2,
                    sizing_mode="stretch_width"
                ),
                pn.Column(
                    self.plot_widgets.downsample_slider,
                    self.plot_widgets.node_count,
                    width=160
                )
            ),
            pn.GridBox(
                *self.plot_widgets.cmd_selects,
                *self.plot_widgets.cmd_multi_selects,
                ncols=4
            ),
            name="Plot Data"
        )
        
        # Sidebar - Data Info tab
        data_tab = pn.Column(
            self.data_widgets.data_select,
            pn.Row(self.data_widgets.name_input, self.data_widgets.color_picker),
            pn.Row(self.data_widgets.tire_id_input, self.data_widgets.rim_width_input),
            self.data_widgets.notes_input,
            self.data_widgets.update_button,
            name="Data Info"
        )
        
        self.info_tabs = pn.layout.Tabs(plot_tab, data_tab)
        
        self.template.sidebar.append(
            pn.Column(
                self.import_btn,
                self.data_table,
                pn.layout.Divider(),
                self.info_tabs
            )
        )
        
        # Main area
        self.template.main.append(pn.Column(self.plot_pane))
        
        # Modal
        self.template.modal.append(self.modal_content)
    
    def _setup_callbacks(self):
        """Setup all widget callbacks."""
        # Main action callbacks
        pn.bind(self._on_import_data, self.import_btn.param.clicks, watch=True)
        pn.bind(self._on_settings_click, self.settings_btn.param.clicks, watch=True)
        pn.bind(self._on_plot_data, self.plot_widgets.plot_button.param.clicks, watch=True)
        pn.bind(self._on_plot_settings, self.plot_widgets.settings_button.param.clicks, watch=True)
        
        # Widget change callbacks
        pn.bind(self._on_plot_type_change, self.plot_widgets.plot_type.param.value, watch=True)
        pn.bind(self._on_data_select, self.data_widgets.data_select.param.value, watch=True)
        pn.bind(self._on_update_data, self.data_widgets.update_button.param.clicks, watch=True)
        pn.bind(self._on_demo_mode_change, self.app_settings_widgets.demo_switch.param.value, watch=True)
        
        # Table callbacks
        self.data_table.on_click(self._on_table_trash_click, column="trash")
        self.data_table.on_click(self._on_table_color_click, column="")
        self.data_table.on_edit(self._on_table_edit)
        self._apply_table_styling()
        
        # Help menu callback
        pn.bind(self._on_help_menu, self.help_menu.param.clicked, watch=True)
        
        # Command selector callbacks
        for selector in self.plot_widgets.cmd_selects:
            pn.bind(self._update_cmd_options, selector.param.value, watch=True)
        
        # Unit/Sign convention callbacks
        pn.bind(self._update_cmd_options, self.app_settings_widgets.unit_select.param.value, watch=True)
        pn.bind(self._update_cmd_options, self.app_settings_widgets.sign_select.param.value, watch=True)
    
    # ===========================
    # Main Callback Methods
    # ===========================
    
    def _on_import_data(self, clicks):
        """Handle data import button click."""
        files = Tk_utils.select_file(
            filetypes=[("MATLAB/ASCII Data Files", "*.mat *.dat *.txt")],
            initialdir=self.config.data_dir
        )
        
        if not files:
            return
        
        imported = self.data_controller.import_data(files)
        if imported:
            self._refresh_data_table()
            self._update_channel_options()
            self._update_data_select_options()
            
            # Select newly imported datasets
            current_selection = self.data_table.selection
            new_indices = list(range(len(self.data_table.value) - len(imported), len(self.data_table.value)))
            self.data_table.selection = current_selection + new_indices
    
    def _on_settings_click(self, clicks):
        """Open settings modal."""
        layout = create_settings_layout(
            self.app_settings_widgets,
            self._on_save_settings,
            self._on_select_data_dir
        )
        self.modal_content.objects = [layout]
        self.template.open_modal()
    
    def _on_save_settings(self, clicks):
        """Save application settings."""
        # Update config from widgets
        self.config.theme = self.app_settings_widgets.theme_select.value
        self.config.unit_system = self.app_settings_widgets.unit_select.value
        self.config.sign_convention = self.app_settings_widgets.sign_select.value
        self.config.demo_mode = self.app_settings_widgets.demo_switch.value
        self.config.data_dir = self.app_settings_widgets.data_dir_input.value
        
        # Update colorway and colormap
        for name, value in self.app_settings_widgets.colorway_select.options.items():
            if value == self.app_settings_widgets.colorway_select.value:
                self.config.colorway = name
                break
        
        for name, value in self.plot_settings_widgets.color_map.options.items():
            if value == self.plot_settings_widgets.color_map.value:
                self.config.colormap = name
                break
        
        # Save to file
        self.config.save(self.config_path)
        self.template.close_modal()
    
    def _on_plot_data(self, clicks):
        """Handle plot data button click."""
        if not self.data_table.selection:
            logger.warning("No datasets selected to plot")
            pn.state.notifications.warning("Select a dataset to plot", duration=4000)
            return
        
        # Collect all widget references for the plot controller
        widgets = {
            'data_table': self.data_table,
            'plot_controls': self.plot_widgets,
            'plot_settings': self.plot_settings_widgets,
            'settings': self.app_settings_widgets
        }
        
        plot_params = self.plot_controller.get_plot_parameters(widgets, self.config)
        fig, node_count = self.plot_controller.create_plot(plot_params)
        
        if fig:
            self.plot_pane.object = fig
            self.plot_widgets.node_count.value = str(node_count)
    
    def _on_plot_settings(self, clicks):
        """Open plot settings modal."""
        self.plot_settings_widgets.update_axis_state(self.plot_widgets.plot_type.value)
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
        
        info = self.data_controller.get_dataset_info(dataset_name, self.config.demo_mode)
        if info:
            self.data_widgets.name_input.value = info['name']
            self.data_widgets.tire_id_input.value = info['tire_id']
            self.data_widgets.rim_width_input.value = info['rim_width']
            self.data_widgets.notes_input.value = info['notes']
            self.data_widgets.color_picker.value = info['node_color']
            self.data_widgets.enable_all(True)
        else:
            self.data_widgets.reset()
    
    @hold()
    def _on_update_data(self, clicks):
        """Handle dataset update button click."""
        updates = {
            'name': self.data_widgets.name_input.value,
            'tire_id': self.data_widgets.tire_id_input.value,
            'rim_width': self.data_widgets.rim_width_input.value,
            'notes': self.data_widgets.notes_input.value,
            'node_color': self.data_widgets.color_picker.value
        }
        
        success = self.data_controller.update_dataset_info(
            self.data_widgets.data_select.value,
            updates,
            self.config.demo_mode
        )
        
        if success:
            self._refresh_data_table()
            self._update_data_select_options()
            self.data_widgets.data_select.value = updates['name']
    
    def _on_demo_mode_change(self, demo_mode):
        """Handle demo mode toggle."""
        self.config.demo_mode = demo_mode
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
            lambda x: self.template.close_modal()
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
    
    def _on_help_menu(self, clicked):
        """Handle help menu selection."""
        actions = {
            "signcon": lambda: webbrowser.open_new(str(Path("docs/Sign_Convention.pdf"))),
            "readme": lambda: webbrowser.open_new(
                "https://github.com/GraysonBrowne/GripLab/blob/main/README.md"
            ),
            "discuss": lambda: webbrowser.open_new(
                "https://github.com/GraysonBrowne/GripLab/discussions"
            ),
            "issue": lambda: webbrowser.open_new(
                "https://github.com/GraysonBrowne/GripLab/issues"
            ),
            "ttc": lambda: webbrowser.open_new(
                "https://www.fsaettc.org/"
            )
        }
        
        action = actions.get(clicked)
        if action:
            logger.info(f"Opening help resource: {clicked}")
            action()
    
    def _on_select_data_dir(self, clicks):
        """Handle data directory selection."""
        directory = Tk_utils.select_dir(initialdir=self.config.data_dir)
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
                selector.options = [""] + [ch for ch in cmd_channels if ch not in excluded]
                
                # Update corresponding multi-select
                self._update_cmd_multi_select(i, selector.value)
        
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
                dataset, to_system=self.app_settings_widgets.unit_select.value
            )
            dataset = ConventionConverter.convert_dataset_convention(
                dataset, target_convention=self.app_settings_widgets.sign_select.value
            )
            
            if channel in dataset.channels:
                col_idx = dataset.channels.index(channel)
                data_values.extend(dataset.data[:, col_idx])
            else:
                data_values.extend([])
        
        unique_values = sorted(np.unique(data_values).astype(np.int64).tolist(), key=abs)
        options = {str(v): i for i, v in enumerate(unique_values)}
        
        # Preserve current selection
        current_value = self.plot_widgets.cmd_multi_selects[index].value
        self.plot_widgets.cmd_multi_selects[index].options = options
        if options:
            self.plot_widgets.cmd_multi_selects[index].value = current_value
        else:
            self.plot_widgets.cmd_multi_selects[index].value.clear()
        self.plot_widgets.cmd_multi_selects[index].param.trigger("value")
    
    def _refresh_data_table(self):
        """Refresh the data table display."""
        if self.config.demo_mode:
            datasets = self.dm.list_demo_names()
        else:
            datasets = self.dm.list_datasets()
        
        self.data_table.value = pd.DataFrame({
            "Dataset": datasets,
            "": [""] * len(datasets)
        })
        
        self._apply_table_styling()
    
    def _apply_table_styling(self):
        """Apply color styling to data table."""
        def cell_color(column):
            if column.name == "":
                return [f"background-color: {color}" for color in self.dm.list_colors()]
            return [""] * len(column)
        
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
        if getattr(sys, 'frozen', False):
            # Running as frozen executable
            server = self.template.show(threaded=True)
            
            def on_session_destroyed(session_context):
                logger.info("Shutting down server...")
                server.stop()
            
            pn.state.on_session_destroyed(on_session_destroyed)
        else:
            # Running in development mode
            self.template.servable()
        
        return self.template

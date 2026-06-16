# ui/components.py
"""UI component classes for GripLab application."""

from typing import List, Optional

import panel as pn
import plotly.express as px

from app.models import SubplotConfig
from converters.conventions import SignConvention
from converters.units import UnitSystem

def _cmap_css() -> str:
    return (
        "div, div:hover {background: var(--panel-surface-color); color: currentColor}"
        if pn.config.theme == "dark"
        else ""
    )


class WidgetFactory:
    """Factory class for creating UI widgets with consistent styling."""

    @staticmethod
    def create_button(
        name: str, button_type: str = "primary", **kwargs
    ) -> pn.widgets.Button:
        """Create a styled button widget."""
        defaults = {"button_type": button_type}
        defaults.update(kwargs)
        return pn.widgets.Button(name=name, **defaults)

    @staticmethod
    def create_select(
        name: str, options: Optional[List] = None, **kwargs
    ) -> pn.widgets.Select:
        """Create a select dropdown widget."""
        defaults = {"options": options or [], "sizing_mode": "stretch_width"}
        defaults.update(kwargs)
        return pn.widgets.Select(name=name, **defaults)

    @staticmethod
    def create_text_input(name: str, **kwargs) -> pn.widgets.TextInput:
        """Create a text input widget."""
        defaults = {"sizing_mode": "stretch_width"}
        defaults.update(kwargs)
        return pn.widgets.TextInput(name=name, **defaults)


class PlotControlWidgets:
    """Container for plot control widgets."""

    def __init__(self):
        wf = WidgetFactory()
        self.name_input = pn.widgets.TextInput(
            name="Page Name", placeholder="Scatter", sizing_mode="stretch_width"
        )

        # Plot type selection
        self.plot_type = pn.widgets.Select(
            name="Plot Type",
            options=["2D", "2D Color", "3D", "3D Color"],
            width=90,
            margin=(5,5),
        )

        # Axis selectors
        self.x_axis = wf.create_select("X-Axis")
        self.y_axis = wf.create_select("Y-Axis")
        self.z_axis = wf.create_select("Z-Axis", disabled=True)
        self.color_axis = wf.create_select("Colorbar", disabled=True)

        # Command channel selectors
        self.cmd_selects = [
            wf.create_select("Conditional Parsing", min_width=80),
            wf.create_select(" ", min_width=80, margin=(9, 10, 5, 10)),
            wf.create_select(" ", min_width=80, margin=(9, 10, 5, 10)),
            wf.create_select(" ", min_width=80, margin=(9, 10, 5, 10)),
        ]

        self.cmd_multi_selects = [
            pn.widgets.MultiSelect(
                options={},
                size=8,
                sizing_mode="stretch_width",
                height=100,
                min_width=80,
            )
            for _ in range(4)
        ]

        # Other controls
        self.downsample_slider = pn.widgets.IntSlider(
            name="Down Sample Factor",
            start=1,
            end=10,
            step=1,
            value=10,
            sizing_mode="stretch_width",
        )
        self.node_count = pn.widgets.StaticText(name="Node Count", value="0")

        # Plot action buttons
        self.plot_button = wf.create_button(
            "Plot Data", width=90, margin=(26, 10, 5, 7)
        )
        self.settings_button = wf.create_button(
            "⚙️", button_type="default", width=43, margin=(26, 0, 5, 15)
        )

    def update_plot_type_state(self, plot_type: str):
        """Update widget states based on plot type selection."""
        states = {
            "2D": {"z": True, "c": True},
            "2D Color": {"z": True, "c": False},
            "3D": {"z": False, "c": True},
            "3D Color": {"z": False, "c": False},
        }
        state = states.get(plot_type, states["2D"])
        self.z_axis.disabled = state["z"]
        self.color_axis.disabled = state["c"]

    def restore(self, session: dict):
        """Restore widget values from a cached session state."""
        if not session:
            return

        self.plot_type.value = session.get("plot_type", "2D")
        self.downsample_slider.value = session.get("downsample", 10)
        self.node_count.value = session.get("node_count", "0")

        # Channels are restored after options are populated — only set if valid
        for widget, key in [
            (self.x_axis, "x_channel"),
            (self.y_axis, "y_channel"),
            (self.z_axis, "z_channel"),
            (self.color_axis, "c_channel"),
        ]:
            value = session.get(key)
            if value and value in widget.options:
                widget.value = value

        # Restore command channel selectors and multi-selects
        cmd_channels = session.get("cmd_channels", [])
        cmd_options = session.get("cmd_options", [])
        cmd_values = session.get("cmd_values", [])

        for i, (sel, multi) in enumerate(zip(self.cmd_selects, self.cmd_multi_selects)):
            if i < len(cmd_channels) and cmd_channels[i] in sel.options:
                sel.value = cmd_channels[i]
            if i < len(cmd_options):
                multi.options = cmd_options[i]
            if i < len(cmd_values):
                multi.value = cmd_values[i]

        self.update_plot_type_state(self.plot_type.value)


class DataInfoWidgets:
    """Container for dataset information widgets."""

    def __init__(self):
        wf = WidgetFactory()

        self.data_select = wf.create_select("Dataset")
        self.name_input = wf.create_text_input("Name", disabled=True)
        self.color_picker = pn.widgets.ColorPicker(name="Color", disabled=True)
        self.tire_id_input = wf.create_text_input("Tire ID", disabled=True)
        self.rim_width_input = pn.widgets.IntInput(
            name="Rim Width [in]", width=100, disabled=True
        )
        self.notes_input = pn.widgets.TextAreaInput(
            name="Notes", sizing_mode="stretch_width", disabled=True
        )
        self.update_button = wf.create_button(
            "Update Dataset", sizing_mode="stretch_width", disabled=True
        )

    def enable_all(self, enabled: bool = True):
        """Enable or disable all data info widgets."""
        self.name_input.disabled = not enabled
        self.color_picker.disabled = not enabled
        self.tire_id_input.disabled = not enabled
        self.rim_width_input.disabled = not enabled
        self.notes_input.disabled = not enabled
        self.update_button.disabled = not enabled

    def reset(self):
        """Reset all widgets to default values."""
        self.name_input.value = ""
        self.color_picker.value = "#000000"
        self.tire_id_input.value = ""
        self.rim_width_input.value = 0
        self.notes_input.value = ""
        self.enable_all(False)


class PlotSettingsWidgets:
    """Container for plot settings widgets."""

    def __init__(self):
        self.title = pn.widgets.TextInput(
            name="Title", placeholder="Tire ID", sizing_mode="stretch_width"
        )
        self.subtitle = pn.widgets.TextInput(
            name="Subtitle", placeholder="Test conditions", sizing_mode="stretch_width"
        )
        self.x_label = pn.widgets.TextInput(
            name="X-Axis Label",
            placeholder="Channel [unit]",
            sizing_mode="stretch_width",
        )
        self.y_label = pn.widgets.TextInput(
            name="Y-Axis Label",
            placeholder="Channel [unit]",
            sizing_mode="stretch_width",
        )
        self.z_label = pn.widgets.TextInput(
            name="Z-Axis Label",
            placeholder="Channel [unit]",
            sizing_mode="stretch_width",
        )
        self.c_label = pn.widgets.TextInput(
            name="Colorbar Label",
            placeholder="Channel [unit]",
            sizing_mode="stretch_width",
        )
        self.font_size = pn.widgets.IntSlider(
            name="Font Size",
            value=18,
            start=4,
            end=32,
            step=1,
            sizing_mode="stretch_width",
        )
        self.marker_size = pn.widgets.IntSlider(
            name="Marker Size",
            value=10,
            start=2,
            end=18,
            step=1,
            sizing_mode="stretch_width",
        )

        self.marker_opacity = pn.widgets.FloatSlider(
            name="Marker Opacity",
            value=0.3,
            start=0.0,
            end=1.0,
            step=0.05,
            sizing_mode="stretch_width",
        )

        # Color map
        color_map_options = {
            "Jet": [
                "#010179",
                "#022291",
                "#0450b2",
                "#0aa5c1",
                "#4ffdc8",
                "#c8ff3a",
                "#ffaf02",
                "#fc1d00",
                "#c10000",
                "#810001",
            ],
            "Inferno": px.colors.sequential.Inferno,
            "Viridis": px.colors.sequential.Viridis,
        }

        self.color_map = pn.widgets.ColorMap(  # type: ignore[attr-defined]
            name="Color Map",
            options=color_map_options,
            value=color_map_options["Jet"],
            ncols=1,
            width=200,
            stylesheets=[_cmap_css()],
        )

    def update_axis_state(self, plot_type: str):
        """Update axis label states based on plot type."""
        z_disabled = plot_type in ["2D", "2D Color"]
        c_disabled = "Color" not in plot_type

        self.z_label.disabled = z_disabled
        self.c_label.disabled = c_disabled

    def restore(self, session: dict):
        """Restore widget values from a cached session state."""
        if not session:
            return

        # Restore plot settings
        self.title.value = session.get("title", "")
        self.subtitle.value = session.get("subtitle", "")
        self.x_label.value = session.get("x_label", "")
        self.y_label.value = session.get("y_label", "")
        self.z_label.value = session.get("z_label", "")
        self.c_label.value = session.get("c_label", "")
        self.font_size.value = session.get("font_size", 18)
        self.marker_size.value = session.get("marker_size", 10)
        self.marker_opacity.value = session.get("marker_opacity", 0.3)

        if "color_map" in session:
            self.color_map.value = session["color_map"]


class AppSettingsWidgets:
    """Container for application settings widgets."""

    def __init__(self, config):
        self.theme_select = pn.widgets.Select(
            name="Default Theme",
            options={"Light": "default", "Dark": "dark"},
            value=config.theme,
            description="Sets the default theme on application start.",
            sizing_mode="stretch_width",
        )

        colorway_dict = {
            "G10": px.colors.qualitative.G10,
            "Plotly": px.colors.qualitative.Plotly,
            "D3": px.colors.qualitative.D3,
            "T10": px.colors.qualitative.T10,
            "Set1": px.colors.qualitative.Set1,
            "Dark2": px.colors.qualitative.Dark2,
        }

        self.colorway_select = pn.widgets.ColorMap(  # type: ignore[attr-defined]
            name="Color Sequence",
            options=colorway_dict,
            value=colorway_dict[config.colorway],
            ncols=1,
            width=200,
            stylesheets=[_cmap_css()],
        )

        self.demo_switch = pn.widgets.Switch(name="Demo Mode", value=config.demo_mode)

        self.data_dir_btn = pn.widgets.Button(
            name="Set Directory", button_type="default", margin=(28, 5, 2, 15)
        )

        self.data_dir_input = pn.widgets.TextInput(
            name="Data Directory", value=config.data_dir, sizing_mode="stretch_width"
        )

        self.unit_select = pn.widgets.Select(
            name="Unit System",
            options=[s.value for s in UnitSystem if s != UnitSystem.SI],
            value=config.unit_system,
            description="USCS: lb, ft-lb, in, psi, mph, deg F \n\r"
            "Metric: N, N-m, cm, kPa, kph, deg C",
            sizing_mode="stretch_width",
        )

        self.sign_select = pn.widgets.Select(
            name="Sign Convention",
            options=[c.value for c in SignConvention],
            value=config.sign_convention,
            description="SAE: As supplied from TTC \n\r"
            "Adapted SAE: Used in Pacejka 2012 \n\r"
            "ISO: Used in most commercial sim tools \n\r"
            "Adapted ISO: Used in Besselink 2000",
            sizing_mode="stretch_width",
        )

        self.save_button = pn.widgets.Button(
            name="Save Settings",
            button_type="primary",
            margin=(10, 15, 0, 15),
            width=200,
        )

class SubplotCellWidget:
    def __init__(self, channels: list[str] = []):
        wf = WidgetFactory()
        opts = [""] + channels
        self.channel_selects = [
            wf.create_select(f"Channel {i + 1}", options=opts)
            for i in range(4)
        ]
        self.label = wf.create_text_input("Y-Axis Label", placeholder="Channel [unit]")
        self._default_channels: list[str] = []

    def selected_channels(self) -> list[str]:
        return [s.value for s in self.channel_selects if s.value]

    def update_channel_options(self, channels: list[str]):
        opts = [""] + channels
        for i, sel in enumerate(self.channel_selects):
            if sel.value in channels:
                current = sel.value
            elif i < len(self._default_channels) and self._default_channels[i] in channels:
                current = self._default_channels[i]
            else:
                current = ""
            sel.options = opts
            sel.value = current

class TimeSeriesControlWidgets:
    def __init__(self):
        self.cells: List[List[SubplotCellWidget]] = []
        self.n_rows: int = 0
        self.n_cols: int = 0

        self.name_input = pn.widgets.TextInput(
            name="Page Name", placeholder="Time Series", sizing_mode="stretch_width"
        )
        self.subplot_select = WidgetFactory.create_select("Selection", width=90, margin=(5,5), sizing_mode="fixed")
        self.channel_grid = pn.GridBox(ncols=2, sizing_mode="stretch_width")
        self.settings_column = pn.Column(self.channel_grid)
        self.add_row_btn = WidgetFactory.create_button("+ Add Subplot", button_type="default", sizing_mode="stretch_width")
        self.remove_btn = WidgetFactory.create_button("Remove Subplot", button_type="danger", sizing_mode="stretch_width")
        self.plot_button = WidgetFactory.create_button("Plot Data", 
                                                       width=90, margin=(26, 10, 5, 7))
        self.settings_button = WidgetFactory.create_button("⚙️", button_type="default", 
                                                           width=43, margin=(26, 0, 5, 15))

    def _cell_label(self, row: int, col: int) -> str:
        if self.n_cols == 1:
            return f"Plot {row + 1}"
        return f"Row {row + 1}, Col {col + 1}"

    def _rebuild_select_options(self):
        opts = [
            self._cell_label(r, c)
            for r in range(self.n_rows)
            for c in range(self.n_cols)
        ]
        current = self.subplot_select.value
        self.subplot_select.options = opts
        self.subplot_select.value = current if current in opts else (opts[0] if opts else None)

    def get_selected_cell(self) -> Optional[SubplotCellWidget]:
        val = self.subplot_select.value
        if not val:
            return None
        for r in range(self.n_rows):
            for c in range(self.n_cols):
                if self._cell_label(r, c) == val:
                    return self.cells[r][c]
        return None

    def show_selected_settings(self):
        cell = self.get_selected_cell()
        if cell is None:
            self.settings_column.objects = []
        else:
            self.channel_grid.objects = [*cell.channel_selects]
            self.settings_column.objects = [
                self.channel_grid,
                cell.label,
                pn.Row(self.remove_btn, self.add_row_btn),
            ]

    def add_row(self, channels: list[str] = [], after: int = -1) -> List[SubplotCellWidget]:
        new_row = [SubplotCellWidget(channels)]
        if 0 <= after < self.n_rows:
            self.cells.insert(after + 1, new_row)
        else:
            self.cells.append(new_row)
        self.n_rows += 1
        if self.n_cols == 0:
            self.n_cols = 1
        self._rebuild_select_options()
        return new_row

    def add_col(self, channels: list[str] = []) -> List[SubplotCellWidget]:
        new_cells = []
        for row in self.cells:
            cell = SubplotCellWidget(channels)
            row.append(cell)
            new_cells.append(cell)
        self.n_cols += 1
        self._rebuild_select_options()
        return new_cells

    def remove_selected(self) -> Optional[tuple[int, int]]:
        """Remove the currently selected cell. Returns (row, col) removed."""
        val = self.subplot_select.value
        if not val:
            return None
        if self.n_rows <= 1:
            return None
        for r in range(self.n_rows):
            for c in range(self.n_cols):
                if self._cell_label(r, c) != val:
                    continue
                if self.n_cols == 1:
                    self.cells.pop(r)
                    self.n_rows -= 1
                elif self.n_rows == 1:
                    self.cells[r].pop(c)
                    self.n_cols -= 1
                else:
                    self.cells[r].pop(c)
                    if not self.cells[r]:
                        self.cells.pop(r)
                        self.n_rows -= 1
                    if self.n_cols > 0 and all(len(row) < self.n_cols for row in self.cells):
                        self.n_cols -= 1
                self._rebuild_select_options()
                if self.n_rows > 0:
                    new_r = min(r, self.n_rows - 1)
                    self.subplot_select.value = self._cell_label(new_r, 0)
                self.show_selected_settings()
                return (r, c)
        return None

    def update_channel_options(self, channels: list[str]):
        for row in self.cells:
            for cell in row:
                cell.update_channel_options(channels)

    def get_subplot_grid(self) -> List[List[SubplotConfig]]:
        return [
            [
                SubplotConfig(channels=cell.selected_channels(), label=cell.label.value)
                for cell in row
            ]
            for row in self.cells
        ]
    
class TimeSeriesSettingsWidgets:
    def __init__(self):
        self.title = pn.widgets.TextInput(
            name="Title", placeholder="Run conditions", sizing_mode="stretch_width"
        )
        self.font_size = pn.widgets.IntSlider(
            name="Font Size", value=12, start=4, end=32, step=1,
            sizing_mode="stretch_width"
        )
        self.line_width = pn.widgets.IntSlider(
            name="Line Width", value=2, start=1, end=8, step=1,
            sizing_mode="stretch_width"
        )

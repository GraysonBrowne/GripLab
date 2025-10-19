# ui/components.py
"""UI component classes for GripLab application."""

from typing import List

import panel as pn
import plotly.express as px


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
    def create_select(name: str, options: List = None, **kwargs) -> pn.widgets.Select:
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

        # Plot type selection
        self.plot_type = pn.widgets.RadioBoxGroup(
            name="Plot Type", options=["2D", "2D Color", "3D", "3D Color"], inline=True
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
            value=5,
            sizing_mode="stretch_width",
        )
        self.node_count = pn.widgets.StaticText(name="Node Count", value="0")

        # Plot action buttons
        self.plot_button = wf.create_button(
            "Plot Data", sizing_mode="stretch_width", margin=(5, 10, 5, 7)
        )
        self.settings_button = wf.create_button(
            "⚙️", button_type="default", width=43, margin=(5, 0, 5, 15)
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

        self.color_map = pn.widgets.ColorMap(
            name="Color Map",
            options=color_map_options,
            value=color_map_options["Jet"],
            ncols=1,
            width=200,
        )

    def update_axis_state(self, plot_type: str):
        """Update axis label states based on plot type."""
        z_disabled = plot_type in ["2D", "2D Color"]
        c_disabled = "Color" not in plot_type

        self.z_label.disabled = z_disabled
        self.c_label.disabled = c_disabled


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

        self.colorway_select = pn.widgets.ColorMap(
            name="Color Sequence",
            options=colorway_dict,
            value=colorway_dict[config.colorway],
            ncols=1,
            width=200,
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
            options=["USCS", "Metric"],
            value=config.unit_system,
            description="USCS: lb, ft-lb, in, psi, mph, deg F \n\r"
            "Metric: N, N-m, cm, kPa, kph, deg C",
            sizing_mode="stretch_width",
        )

        self.sign_select = pn.widgets.Select(
            name="Sign Convention",
            options=["SAE", "Adapted SAE", "ISO", "Adapted ISO"],
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

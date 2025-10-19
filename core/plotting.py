# core/plotting.py
"""2D/3D visualization utilities for tire test data."""

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from converters.conventions import ConventionConverter
from converters.units import UnitSystemConverter
from core.processing import DataDownsampler
from utils.logger import logger


class PlotType(Enum):
    """Types of plots available."""

    PLOT_2D = "2D"
    PLOT_2D_COLOR = "2D Color"
    PLOT_3D = "3D"
    PLOT_3D_COLOR = "3D Color"


@dataclass
class PlotConfig:
    """Configuration for plot generation."""

    plot_type: PlotType
    x_channel: str
    y_channel: str
    z_channel: Optional[str] = None
    color_channel: Optional[str] = None

    # Units
    x_unit: str = ""
    y_unit: str = ""
    z_unit: str = ""
    color_unit: str = ""

    # Display options
    title: str = ""
    subtitle: str = ""
    x_label: str = ""
    y_label: str = ""
    z_label: str = ""
    color_label: str = ""

    # Style options
    font_size: int = 18
    marker_size: int = 10
    color_map: Any = None
    show_axes: bool = True

    # Data options
    downsample_factor: int = 5
    unit_system: str = "USCS"
    sign_convention: str = "ISO"

    def __post_init__(self):
        """Validate configuration after initialization."""
        if isinstance(self.plot_type, str):
            self.plot_type = PlotType(self.plot_type)

        # Validate required channels
        if not self.x_channel or not self.y_channel:
            raise ValueError("X and Y channels are required")

        # Validate 3D requirements
        if "3D" in self.plot_type.value and not self.z_channel:
            raise ValueError("Z channel required for 3D plots")

        # Validate color requirements
        if "Color" in self.plot_type.value and not self.color_channel:
            raise ValueError("Color channel required for color plots")


@dataclass
class PlotData:
    """Container for plot data and metadata."""

    x: np.ndarray
    y: np.ndarray
    z: Optional[np.ndarray] = None
    c: Optional[np.ndarray] = None
    name: str = ""
    color: str = "#1f77b4"
    hover_text: Optional[List[str]] = None

    @property
    def point_count(self) -> int:
        """Get number of data points."""
        return len(self.x)

    def is_valid(self) -> bool:
        """Check if data is valid for plotting."""
        return len(self.x) > 0 and len(self.y) > 0


class PlotBuilder:
    """Builds Plotly figures from processed data."""

    @staticmethod
    def create_figure(plot_type: PlotType) -> go.Figure:
        """Create base figure for plot type."""
        if "3D" in plot_type.value:
            return px.scatter_3d()
        else:
            # Use WebGL for better performance with large datasets
            return px.scatter(render_mode="webgl")

    @staticmethod
    def add_2d_trace(fig: go.Figure, data: PlotData, config: PlotConfig) -> None:
        """Add 2D scatter trace to figure."""
        if config.show_axes:
            hovertemplate = (
                "<b>%{hovertext}</b><br>"
                + f"{config.x_channel}: %{{x:.2f}} {config.x_unit}<br>"
                + f"{config.y_channel}: %{{y:.2f}} {config.y_unit}<extra></extra>"
            )
        else:
            hovertemplate = "<b>%{hovertext}</b><br><extra></extra>"
        trace = dict(
            type="scatter",
            x=data.x,
            y=data.y,
            mode="markers",
            name=data.name,
            marker=dict(size=config.marker_size, color=data.color),
            hovertext=data.hover_text or [data.name] * data.point_count,
            hovertemplate=hovertemplate,
        )
        fig.add_trace(trace)

    @staticmethod
    def add_2d_color_trace(
        fig: go.Figure,
        data: PlotData,
        config: PlotConfig,
        color_range: Tuple[float, float],
    ) -> None:
        """Add 2D scatter trace with color mapping."""
        if config.show_axes:
            hovertemplate = (
                "<b>%{hovertext}</b><br>"
                + f"{config.x_channel}: %{{x:.2f}} {config.x_unit}<br>"
                + f"{config.y_channel}: %{{y:.2f}} {config.y_unit}<br>"
                + f"{config.color_channel}: %{{marker.color:.2f}} {config.color_unit}<extra></extra>"
            )
        else:
            hovertemplate = "<b>%{hovertext}</b><br><extra></extra>"
        trace = dict(
            type="scatter",
            x=data.x,
            y=data.y,
            mode="markers",
            marker=dict(
                size=config.marker_size,
                color=data.c,
                colorscale=config.color_map,
                cmin=color_range[0],
                cmax=color_range[1],
                colorbar=dict(
                    title=config.color_label, showticklabels=config.show_axes
                ),
                showscale=True,
            ),
            hovertext=data.hover_text or [data.name] * data.point_count,
            hovertemplate=hovertemplate,
        )
        fig.add_trace(trace)

    @staticmethod
    def add_3d_trace(fig: go.Figure, data: PlotData, config: PlotConfig) -> None:
        """Add 3D scatter trace to figure."""
        if config.show_axes:
            hovertemplate = (
                "<b>%{hovertext}</b><br>"
                + f"{config.x_channel}: %{{x:.2f}} {config.x_unit}<br>"
                + f"{config.y_channel}: %{{y:.2f}} {config.y_unit}<br>"
                + f"{config.z_channel}: %{{z:.2f}} {config.z_unit}<extra></extra>"
            )
        else:
            hovertemplate = "<b>%{hovertext}</b><br><extra></extra>"
        trace = dict(
            type="scatter3d",
            x=data.x,
            y=data.y,
            z=data.z,
            mode="markers",
            name=data.name,
            marker=dict(size=config.marker_size, color=data.color),
            hovertext=data.hover_text or [data.name] * data.point_count,
            hovertemplate=hovertemplate,
        )
        fig.add_trace(trace)

    @staticmethod
    def add_3d_color_trace(
        fig: go.Figure,
        data: PlotData,
        config: PlotConfig,
        color_range: Tuple[float, float],
    ) -> None:
        """Add 3D scatter trace with color mapping."""
        if config.show_axes:
            hovertemplate = (
                "<b>%{hovertext}</b><br>"
                + f"{config.x_channel}: %{{x:.2f}} {config.x_unit}<br>"
                + f"{config.y_channel}: %{{y:.2f}} {config.y_unit}<br>"
                + f"{config.z_channel}: %{{z:.2f}} {config.z_unit}<br>"
                + f"{config.color_channel}: %{{marker.color:.2f}} {config.color_unit}<extra></extra>"
            )
        else:
            hovertemplate = "<b>%{hovertext}</b><br><extra></extra>"
        trace = dict(
            type="scatter3d",
            x=data.x,
            y=data.y,
            z=data.z,
            mode="markers",
            marker=dict(
                size=config.marker_size,
                color=data.c,
                colorscale=config.color_map,
                cmin=color_range[0],
                cmax=color_range[1],
                colorbar=dict(
                    title=config.color_label, showticklabels=config.show_axes
                ),
                showscale=True,
            ),
            hovertext=data.hover_text or [data.name] * data.point_count,
            hovertemplate=hovertemplate,
        )
        fig.add_trace(trace)

    @staticmethod
    def update_layout(fig: go.Figure, config: PlotConfig) -> None:
        """Update figure layout with labels and styling."""
        if "3D" in config.plot_type.value:
            fig.update_layout(
                title=dict(
                    text=f"{config.title}<br><sup>{config.subtitle}</sup>",
                    xanchor="center",
                    x=0.5,
                ),
                scene=dict(
                    xaxis=dict(
                        title=config.x_label,
                        showticklabels=config.show_axes,
                        tickfont=dict(size=config.font_size - 3),
                    ),
                    yaxis=dict(
                        title=config.y_label,
                        showticklabels=config.show_axes,
                        tickfont=dict(size=config.font_size - 3),
                    ),
                    zaxis=dict(
                        title=config.z_label,
                        showticklabels=config.show_axes,
                        tickfont=dict(size=config.font_size - 3),
                    ),
                ),
                font=dict(size=config.font_size),
                showlegend="Color" not in config.plot_type.value,
            )
        else:
            fig.update_layout(
                title=dict(
                    text=f"{config.title}<br><sup>{config.subtitle}</sup>",
                    xanchor="center",
                    x=0.5,
                ),
                xaxis=dict(title=config.x_label, showticklabels=config.show_axes),
                yaxis=dict(title=config.y_label, showticklabels=config.show_axes),
                font=dict(size=config.font_size),
                showlegend="Color" not in config.plot_type.value,
            )


class DataProcessor:
    """Processes datasets for plotting."""

    @staticmethod
    def prepare_dataset(
        dataset: Any, config: PlotConfig, cmd_filters: Optional[Dict[str, List]] = None
    ) -> Any:
        """
        Prepare dataset for plotting with conversions and filtering.

        Args:
            dataset: Input dataset
            config: Plot configuration
            cmd_filters: Command channel filters to apply

        Returns:
            Processed dataset
        """
        # Apply unit conversion
        dataset = UnitSystemConverter.convert_dataset(
            dataset, to_system=config.unit_system
        )

        # Apply sign convention
        dataset = ConventionConverter.convert_dataset_convention(
            dataset, target_convention=config.sign_convention
        )

        # Apply command channel filtering if provided
        if cmd_filters:
            for channel, values in cmd_filters.items():
                if channel and values:
                    logger.debug(
                        f"Filtering {dataset.name} on {channel} for values {values}"
                    )
                    dataset = DataProcessor._filter_by_channel(dataset, channel, values)

        return dataset

    @staticmethod
    def _filter_by_channel(dataset: Any, channel: str, values: List) -> Any:
        """Filter dataset by channel values."""
        if channel not in dataset.channels:
            return dataset

        from dataclasses import replace

        result = replace(dataset, data=dataset.data.copy())

        if None in values:
            result.data = np.empty((0, result.data.shape[1]))
        else:
            idx = result.channels.index(channel)
            mask = np.isin(result.data[:, idx].astype(np.int64), values)
            result.data = result.data[mask, :]

        return result

    @staticmethod
    def extract_plot_data(dataset: Any, config: PlotConfig) -> PlotData:
        """
        Extract and downsample data for plotting.

        Args:
            dataset: Processed dataset
            config: Plot configuration

        Returns:
            PlotData object with extracted arrays
        """
        # Get channel indices
        x_idx = dataset.channels.index(config.x_channel)
        y_idx = dataset.channels.index(config.y_channel)

        x_data = dataset.data[:, x_idx]
        y_data = dataset.data[:, y_idx]
        z_data = None
        c_data = None

        # Extract Z data for 3D plots
        if config.z_channel:
            z_idx = dataset.channels.index(config.z_channel)
            z_data = dataset.data[:, z_idx]

        # Extract color data
        if config.color_channel:
            c_idx = dataset.channels.index(config.color_channel)
            c_data = dataset.data[:, c_idx]

        # Downsample
        x, y, z, c = DataDownsampler.downsample_uniform(
            x_data, y_data, z_data, c_data, factor=config.downsample_factor
        )

        return PlotData(x=x, y=y, z=z, c=c, name=dataset.name, color=dataset.node_color)


class PlotMetadataBuilder:
    """Builds metadata for plot display."""

    @staticmethod
    def build_title(
        datasets: List[Any], config: PlotConfig, demo_mode: bool = False
    ) -> str:
        """Build plot title from datasets."""
        if config.title:
            return config.title

        # Use tire IDs if all the same
        if demo_mode:
            tire_ids = [ds.demo_tire_id for ds in datasets]
        else:
            tire_ids = [ds.tire_id for ds in datasets]

        unique_ids = list(set(tire_ids))
        if len(unique_ids) == 1:
            return unique_ids[0]

        return ""

    @staticmethod
    def build_subtitle(datasets: List[Any], config: PlotConfig) -> str:
        """Build plot subtitle with test conditions."""
        if config.subtitle:
            return config.subtitle

        conditions = defaultdict(list)
        for dataset in datasets:
            for cond in ["CmdSA", "SL", "CmdIA", "CmdFZ", "CmdP", "CmdV"]:
                condition_data = np.unique(
                    dataset.data[:, dataset.channels.index(cond)]
                ).tolist()
                conditions[cond].extend(condition_data)
            conditions["rim_width"].extend(str(dataset.rim_width))

        # Format condition strings
        parts = []
        for key, values in conditions.items():
            if not values:
                continue

            unique_vals = [int(x) for x in list(set(values))]
            if not config.show_axes:
                unique_vals[0] = "X"
            if len(unique_vals) == 1:
                if key == "rim_width":
                    parts.append(f"Rim Width: {unique_vals[0]} in")
                elif key == "SL":
                    unit = dataset.units[dataset.channels.index(key)]
                    parts.append(f"SR: {unique_vals[0]} {unit}")
                else:
                    unit = dataset.units[dataset.channels.index(key)]
                    parts.append(f"{key.replace('Cmd', '')}: {unique_vals[0]} {unit}")
            else:
                parts.append(f"{key.replace('Cmd', '')}: VAR")

        return " | ".join(parts)

    @staticmethod
    def build_axis_label(channel: str, unit: str, custom_label: str = "") -> str:
        """Build axis label with channel and unit."""
        if custom_label:
            return custom_label
        return f"{channel} [{unit}]" if unit else channel


class PlottingUtils:
    """Main plotting utility class - maintains backward compatibility."""

    @classmethod
    def plot_data(
        cls,
        data_table,
        dm,
        x_select,
        y_select,
        z_select,
        color_select,
        unit_select,
        sign_select,
        plot_radio_group,
        color_map,
        downsample_slider,
        cmd_select_1,
        cmd_select_2,
        cmd_select_3,
        cmd_select_4,
        cmd_multi_select_1,
        cmd_multi_select_2,
        cmd_multi_select_3,
        cmd_multi_select_4,
        axis_visibility,
        title_text="",
        subtitle_text="",
        x_label_text="",
        y_label_text="",
        z_label_text="",
        c_label_text="",
        font_size=18,
        marker_size=10,
    ) -> Tuple[go.Figure, int]:
        """
        Legacy interface for backward compatibility.
        Creates a plot from widget selections.
        """
        # Get selected datasets
        selection = data_table.selection
        if not selection:
            logger.warning("No datasets selected to plot")
            return None, 0

        # Build configuration
        config = PlotConfig(
            plot_type=PlotType(plot_radio_group.value),
            x_channel=x_select.value,
            y_channel=y_select.value,
            z_channel=z_select.value if "3D" in plot_radio_group.value else None,
            color_channel=(
                color_select.value if "Color" in plot_radio_group.value else None
            ),
            title=title_text,
            subtitle=subtitle_text,
            x_label=x_label_text,
            y_label=y_label_text,
            z_label=z_label_text,
            color_label=c_label_text,
            font_size=font_size,
            marker_size=marker_size,
            color_map=color_map.value if hasattr(color_map, "value") else color_map,
            show_axes=not axis_visibility,
            downsample_factor=downsample_slider.value,
            unit_system=unit_select.value,
            sign_convention=sign_select.value,
        )

        # Build command filters
        cmd_filters = cls._build_cmd_filters(
            [cmd_select_1, cmd_select_2, cmd_select_3, cmd_select_4],
            [
                cmd_multi_select_1,
                cmd_multi_select_2,
                cmd_multi_select_3,
                cmd_multi_select_4,
            ],
        )

        # Process datasets
        datasets = []
        plot_data_list = []
        total_points = 0

        for idx in selection:
            name = dm.list_datasets()[idx]
            dataset = dm.get_dataset(name)

            # Process dataset
            processed = DataProcessor.prepare_dataset(dataset, config, cmd_filters)
            datasets.append(processed)

            # Extract plot data
            plot_data = DataProcessor.extract_plot_data(processed, config)

            # Update name for demo mode
            if axis_visibility:
                plot_data.name = dm.list_demo_names()[idx]

            plot_data_list.append(plot_data)
            total_points += plot_data.point_count

        # Create figure
        fig = PlotBuilder.create_figure(config.plot_type)

        # Determine color range for color plots
        color_range = None
        if "Color" in config.plot_type.value:
            all_colors = [
                pd.c for pd in plot_data_list if pd.c is not None and len(pd.c) > 0
            ]
            if all_colors:
                color_range = (
                    min(c.min() for c in all_colors),
                    max(c.max() for c in all_colors),
                )

        # Build metadata
        config.title = PlotMetadataBuilder.build_title(
            datasets, config, axis_visibility
        )
        config.subtitle = PlotMetadataBuilder.build_subtitle(datasets, config)

        # Get units for labels
        if datasets:
            config.x_unit = datasets[0].units[
                datasets[0].channels.index(config.x_channel)
            ]
            config.y_unit = datasets[0].units[
                datasets[0].channels.index(config.y_channel)
            ]

            config.x_label = PlotMetadataBuilder.build_axis_label(
                config.x_channel, config.x_unit, config.x_label
            )
            config.y_label = PlotMetadataBuilder.build_axis_label(
                config.y_channel, config.y_unit, config.y_label
            )

            if config.z_channel:
                config.z_unit = datasets[0].units[
                    datasets[0].channels.index(config.z_channel)
                ]
                config.z_label = PlotMetadataBuilder.build_axis_label(
                    config.z_channel, config.z_unit, config.z_label
                )

            if config.color_channel:
                config.color_unit = datasets[0].units[
                    datasets[0].channels.index(config.color_channel)
                ]
                config.color_label = PlotMetadataBuilder.build_axis_label(
                    config.color_channel, config.color_unit, config.color_label
                )

        # Add traces
        for plot_data in plot_data_list:
            if not plot_data.is_valid():
                continue

            if config.plot_type == PlotType.PLOT_2D:
                PlotBuilder.add_2d_trace(fig, plot_data, config)
            elif config.plot_type == PlotType.PLOT_2D_COLOR:
                PlotBuilder.add_2d_color_trace(fig, plot_data, config, color_range)
            elif config.plot_type == PlotType.PLOT_3D:
                PlotBuilder.add_3d_trace(fig, plot_data, config)
            elif config.plot_type == PlotType.PLOT_3D_COLOR:
                PlotBuilder.add_3d_color_trace(fig, plot_data, config, color_range)

        # Update layout
        PlotBuilder.update_layout(fig, config)

        return fig, total_points

    @staticmethod
    def _build_cmd_filters(selectors: List, multi_selectors: List) -> Dict[str, List]:
        """Build command channel filters from widget selections."""
        filters = {}

        for selector, multi in zip(selectors, multi_selectors):
            if selector.value and multi.value:
                # Get selected values from multi-select
                selected_values = [
                    int(k) for k, v in multi.options.items() if v in multi.value
                ]
                filters[selector.value] = selected_values
            elif selector.value and not multi.value:
                # If no values selected, filter to none
                filters[selector.value] = [None]

        return filters

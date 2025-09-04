# 2D/3D visualization
import plotly.express as px

from .logger_setup import logger
from .unit_conversion import UnitSystemConverter
from .convention_conversion import ConventionConverter
from .processing import downsample_uniform

class PlottingUtils:

    # --- Helpers ---
    @staticmethod
    def _get_channel_data(dataset, channel):
        """Extract data for a given channel name."""
        return dataset.data[:, dataset.channels.index(channel)]

    @staticmethod
    def _get_unit(dataset, channel):
        """Return the unit string for a given channel name."""
        return dataset.units[dataset.channels.index(channel)] if channel else None

    # --- Plot helpers ---
    @classmethod
    def _plot_2d(cls, dataset, x_channel, y_channel, downsample_factor, name):
        """Generates a 2D scatter plot dictionary for the given dataset and channels."""
        x, y, z, c = downsample_uniform(
            cls._get_channel_data(dataset, x_channel),
            cls._get_channel_data(dataset, y_channel),
            factor=downsample_factor
        )
        return dict(
            type="scatter",
            x=x, y=y,
            name=name,
            hovertext=[name] * len(x),
            line=dict(color=dataset.node_color),
            mode="markers"
        )

    @classmethod
    def _plot_2d_color(cls, dataset, x_channel, y_channel, color_channel, 
                       downsample_factor, name, axis_visibility):
        """Generates a 2D scatter plot dictionary with color mapping for the 
            given dataset and channels."""
        x, y, z, c = downsample_uniform(
            cls._get_channel_data(dataset, x_channel),
            cls._get_channel_data(dataset, y_channel),
            c=cls._get_channel_data(dataset, color_channel),
            factor=downsample_factor
        )
        color_unit = cls._get_unit(dataset, color_channel)
        return dict(
            type="scatter",
            x=x, y=y,
            hovertext=[name] * len(x),
            marker=dict(color=c, colorbar=dict(title=f"{color_channel} [{color_unit}]",
                                               showticklabels=(not axis_visibility))),
            mode="markers"
        ), c

    @classmethod
    def _plot_3d(cls, dataset, x_channel, y_channel, z_channel, downsample_factor, name):
        """Generates a 3D scatter plot dictionary for the given dataset and channels."""
        # Downsample the data
        x, y, z, c = downsample_uniform(
            cls._get_channel_data(dataset, x_channel),
            cls._get_channel_data(dataset, y_channel),
            cls._get_channel_data(dataset, z_channel),
            factor=downsample_factor
        )
        return dict(
            type="scatter3d",
            x=x, y=y, z=z,
            name=name,
            hovertext=[name] * len(x),
            line=dict(color=dataset.node_color),
            mode="markers"
        )

    @classmethod
    def _plot_3d_color(cls, dataset, x_channel, y_channel, z_channel, color_channel, 
                       downsample_factor, name, axis_visibility):
        """Generates a 3D scatter plot dictionary with color mapping for the 
            given dataset and channels."""
        x, y, z, c = downsample_uniform(
            cls._get_channel_data(dataset, x_channel),
            cls._get_channel_data(dataset, y_channel),
            cls._get_channel_data(dataset, z_channel),
            c=cls._get_channel_data(dataset, color_channel),
            factor=downsample_factor
        )
        color_unit = cls._get_unit(dataset, color_channel)
        return dict(
            type="scatter3d",
            x=x, y=y, z=z,
            name=name,
            hovertext=[name] * len(x),
            line=dict(color=dataset.node_color),
            marker=dict(color=c, colorbar=dict(title=f"{color_channel} [{color_unit}]",
                                               showticklabels=(not axis_visibility))),
            mode="markers"
        ), c

    # --- Hover template helper ---
    @staticmethod
    def _get_hover_template(plot_type, x_channel, y_channel, z_channel, color_channel,
                            x_unit, y_unit, z_unit, color_unit,):
        """Returns a hover template string based on the plot type."""
        templates = {
            "2D": f"<b>%{{hovertext}}</b><br>"
                  f"{x_channel}: %{{x:.2f}} {x_unit}<br>"
                  f"{y_channel}: %{{y:.2f}} {y_unit}<extra></extra>",

            "2D Color": f"<b>%{{hovertext}}</b><br>"
                        f"{x_channel}: %{{x:.2f}} {x_unit}<br>"
                        f"{y_channel}: %{{y:.2f}} {y_unit}<br>"
                        f"{color_channel}: %{{marker.color:.2f}} {color_unit}<extra></extra>",

            "3D": f"<b>%{{hovertext}}</b><br>"
                  f"{x_channel}: %{{x:.2f}} {x_unit}<br>"
                  f"{y_channel}: %{{y:.2f}} {y_unit}<br>"
                  f"{z_channel}: %{{z:.2f}} {z_unit}<extra></extra>",

            "3D Color": f"<b>%{{hovertext}}</b><br>"
                        f"{x_channel}: %{{x:.2f}} {x_unit}<br>"
                        f"{y_channel}: %{{y:.2f}} {y_unit}<br>"
                        f"{z_channel}: %{{z:.2f}} {z_unit}<br>"
                        f"{color_channel}: %{{marker.color:.2f}} {color_unit}<extra></extra>"
        }
        return templates[plot_type]

    # --- Axis label helper ---
    @classmethod
    def _update_axis_labels(cls, fig, plot_type, names,
                            x_channel, y_channel, z_channel, x_unit, y_unit, z_unit,
                            axis_visibility):
        """Updates axis titles based on the plot type and channel names and units."""
        title = names[0] if len(names) == 1 else ""

        if "3D" in plot_type:
            fig.update_layout(
                title=title,
                scene_xaxis_title_text=f"{x_channel} [{x_unit}]",
                scene_yaxis_title_text=f"{y_channel} [{y_unit}]",
                scene_zaxis_title_text=f"{z_channel} [{z_unit}]",
                scene_xaxis=dict(showticklabels=(not axis_visibility)),
                scene_yaxis=dict(showticklabels=(not axis_visibility)),
                scene_zaxis=dict(showticklabels=(not axis_visibility))
            )
        else:
            fig.update_layout(
                title=title,
                xaxis_title=f"{x_channel} [{x_unit}]",
                yaxis_title=f"{y_channel} [{y_unit}]",
                xaxis=dict(showticklabels=(not axis_visibility)),
                yaxis=dict(showticklabels=(not axis_visibility))
            )

    # --- Colorbar helper ---
    @staticmethod
    def _update_colorbar(fig, plot_type, cmin, cmax, color_map):
        """Updates colorbar settings if the plot type includes color mapping."""
        if "Color" in plot_type and cmin and cmax:
            fig.update_traces(marker=dict(
                cmin=min(cmin), cmax=max(cmax),
                colorscale=color_map.value, showscale=True))
            fig.update_layout(showlegend=False)

    # --- Main entry point ---
    @classmethod
    def plot_data(cls, data_table, dm,x_select, y_select, z_select, color_select,
                  unit_select, sign_select, plot_radio_group, color_map, downsample_slider,
                  cmd_select_1, cmd_select_2, cmd_select_3, cmd_select_4, cmd_multi_select_1, 
                  cmd_multi_select_2, cmd_multi_select_3, cmd_multi_select_4, axis_visibility):
        """
        Plots selected datasets using Plotly, supporting 2D/3D and color mapping.

        Parameters
        ----------
        data_table : Tabulator
            The data table widget containing dataset selections.
        dm : DataManager
            The data manager for accessing datasets.
        x_select : Select
            Widget for selecting the x-axis channel.
        y_select : Select
            Widget for selecting the y-axis channel.
        z_select : Select
            Widget for selecting the z-axis channel (used for 3D plots).
        color_select : Select
            Widget for selecting the color channel (used for color plots).
        unit_select : Select
            Widget for selecting the unit system for conversion.
        sign_select : Select
            Widget for selecting the sign convention for conversion.
        plot_radio_group : RadioGroup
            Widget for selecting the plot type (e.g., "2D", "2D Color", "3D", "3D Color").
        color_map : str
            Name of the color map to use for color plots.
        downsample_slider : Slider
            Widget for selecting the downsampling rate.

        Returns
        -------
        fig : plotly.graph_objs.Figure or None
            The generated Plotly figure, or None if no datasets are selected.

        Notes
        -----
        - Supports 2D and 3D scatter plots, with optional color mapping.
        - Converts datasets to the selected unit system and sign convention.
        - Updates axis labels, hover templates, and colorbars according to selections.
        - Logs warnings if no datasets are selected or if an unknown plot type is specified.
        """

        selection = data_table.selection
        if not selection:
            logger.warning("No datasets selected to plot.")
            return

        # Get selected dataset names and plot type
        names = [dm.list_datasets()[idx] for idx in selection]
        plot_type = plot_radio_group.value
        logger.debug(f"Selected datasets: {names}, plot_type={plot_type}")

        # Get selected channels
        x_channel, y_channel = x_select.value, y_select.value
        z_channel = z_select.value if "3D" in plot_type else None
        color_channel = color_select.value if "Color" in plot_type else None

        # Initialize figure
        fig = px.scatter_3d() if "3D" in plot_type else px.scatter(render_mode="webgl")
        # Initialize color range lists
        cmin, cmax = [], []

        chan_selectors = [cmd_select_1, cmd_select_2, cmd_select_3, cmd_select_4]
        chan_selected = [sel.value for sel in chan_selectors]
        condition_selectors = [cmd_multi_select_1, cmd_multi_select_2, cmd_multi_select_3, cmd_multi_select_4]
        
        for name in names:
            # Retrieve and convert dataset
            dataset = dm.get_dataset(name)
            dataset = UnitSystemConverter.convert_dataset(dataset, to_system=unit_select.value)
            dataset = ConventionConverter.convert_dataset_convention(dataset, target_convention=sign_select.value)
            
            # Apply command channel filtering
            for i, chan in enumerate(chan_selected):
                keys_matching = [k for k, v in condition_selectors[i].options.items() if v in condition_selectors[i].value]
                dataset = dm.parse_dataset(dataset, chan, keys_matching) if chan else dataset

            # Generate and add traces based on plot type
            match plot_type:
                case "2D":
                    trace = cls._plot_2d(dataset, x_channel, y_channel, 
                                         downsample_slider.value, name)
                    fig.add_scatter(**trace)

                case "2D Color":
                    trace, c = cls._plot_2d_color(dataset, x_channel, y_channel, 
                                                  color_channel, downsample_slider.value, 
                                                  name, axis_visibility)
                    if len(c) > 0:
                        cmin.append(c.min()); cmax.append(c.max())
                    fig.add_scatter(**trace)

                case "3D":
                    trace = cls._plot_3d(dataset, x_channel, y_channel, z_channel, 
                                         downsample_slider.value, name)
                    fig.add_scatter3d(**trace)

                case "3D Color":
                    trace, c = cls._plot_3d_color(dataset, x_channel, y_channel, 
                                                  z_channel, color_channel, 
                                                  downsample_slider.value, name,
                                                  axis_visibility)
                    if len(c) > 0:
                        cmin.append(c.min()); cmax.append(c.max())
                    fig.add_scatter3d(**trace)

                case _:
                    logger.warning(f"Unknown plot type: {plot_type}")

        # Axis labels
        x_unit = cls._get_unit(dataset, x_channel)
        y_unit = cls._get_unit(dataset, y_channel)
        z_unit = cls._get_unit(dataset, z_channel)
        color_unit = cls._get_unit(dataset, color_channel)
        cls._update_axis_labels(fig, plot_type, names, x_channel, y_channel,
                                z_channel, x_unit, y_unit, z_unit, axis_visibility)

        # Hover template
        hover_template = cls._get_hover_template(plot_type, x_channel, y_channel, z_channel, color_channel,
                                                 x_unit, y_unit, z_unit, color_unit)
        if axis_visibility:
            fig.update_traces(hovertemplate=f"<b>%{{hovertext}}</b><br>") 
        else:
            fig.update_traces(hovertemplate=hover_template)

        # Colorbar
        cls._update_colorbar(fig, plot_type, cmin, cmax, color_map)

        return fig
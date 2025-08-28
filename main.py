# main.py
import panel as pn
import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import sys
import yaml
from pathlib import Path
from scripts.tk_utilities import Tk_utils 
from scripts.logger_setup import logger
import scripts.dataio as IO
from scripts.unit_conversion import UnitSystemConverter
from scripts.convention_conversion import ConventionConverter
from scripts.processing import downsample_uniform
from plotly_resampler import FigureResampler

pn.extension('tabulator','plotly')

with open("config.yaml") as f:
    config = yaml.safe_load(f)

dm = IO.DataManager()

# Define the main application template
template = pn.template.FastListTemplate(
    title='GripLab',
    #sidebar_width=300,
    header_background='#2A3F5F',
    header_color='white',
    accent_base_color='#2A3F5F',
    theme=config['theme'],
)

# Define colorway for plots
color = config['ploting']['colorway']
colorway = px.colors.qualitative.__getattribute__(color) if hasattr(px.colors.qualitative, color) else px.colors.qualitative.G10

class callback:
    def import_data(clicks):
        # Open file dialog for user to select a data file
        files = Tk_utils.select_file(filetypes=[('MATLAB/ASCII Data Files',
                                                 '*.mat *.dat *.txt')], 
                                     initialdir=config['paths']['data_dir'],)
        for file_path in files:
            file_path = Path(file_path)
            name = file_path.stem

            # Handle duplicate dataset names
            copy = 0
            while name in dm.list_datasets():
                if copy == 0:
                    og_name = name
                copy += 1
                name = f"{og_name} ({copy})"
            
            # If no file was selected, exit the function
            if str(file_path) == '.':
                return
            color = colorway[len(dm.list_datasets()) % len(colorway)]
            # Determine file type and import data accordingly
            if file_path.suffix.lower() == '.mat':
                data = IO.import_mat(file_path, name, color)
            elif file_path.suffix.lower() in ['.dat', '.txt']:
                data = IO.import_dat(file_path, name, color)
            else:
                logger.error("Unsupported file type selected.")
                return

            # Add the imported dataset to the DataManager
            dm.add_dataset(name,data)

            # Update the data table to reflect the newly added dataset
            data_table.value = pd.DataFrame({'Dataset': dm.list_datasets(),
                                             '': ['']*len(dm.list_datasets())})

            # Update channel selection options based on the imported data
            channels = dm.get_channels(dm.list_datasets())
            x_select.options = channels
            y_select.options = channels
            z_select.options = channels
            color_select.options = channels

            logger.info(f"Data imported from {file_path.name}: {data}")

    def update_plot_type(event):
        # Enable/disable axis selectors based on the selected plot type
        states = plot_states.get(event)
        x_select.disabled = states["x"]
        y_select.disabled = states["y"]
        z_select.disabled = states["z"]
        color_select.disabled = states["c"]
        color_map.disabled = states["c"]

    def plot_data(clicks):
        selection = data_table.selection

        if len(selection) == 0:
            logger.warning("No datasets selected to plot.")
            return
        
        logger.debug(f"Selected rows: {selection}")
        names = [dm.list_datasets()[idx] for idx in selection]
        logger.debug(f"Selected datasets: {names}")

        x_channel = x_select.value
        y_channel = y_select.value
        cmin = []
        cmax = []

        #fig = FigureResampler(go.Figure())
        fig = px.scatter(render_mode='webgl')

        for name in names:
            dataset_unit = UnitSystemConverter.convert_dataset(dm.get_dataset(name),
                                                               to_system=unit_select.value)
            dataset = ConventionConverter.convert_dataset_convention(dataset_unit,
                                                                     target_convention=sign_select.value)
            
            match plot_radio_group.value:
                case "2D":
                    x, y = downsample_uniform(x=dataset.data[:, dataset.channels.index(x_channel)],
                                            y=dataset.data[:, dataset.channels.index(y_channel)],
                                            factor=downsample_slider.value)
                    fig.add_scatter(x=x, y=y, name=name,
                            line=dict(color=dm.get_dataset(name).node_color),
                            mode='markers', # 'markers' mode seems to be memory intensive
                            )
                case "2D Color":
                    x, y, c = downsample_uniform(dataset.data[:, dataset.channels.index(x_channel)],
                                                dataset.data[:, dataset.channels.index(y_channel)],
                                                c=dataset.data[:, dataset.channels.index(color_select.value)],
                                                factor=downsample_slider.value)
                    cmin.append(c.min())
                    cmax.append(c.max())
                    color_unit = dataset.units[dataset.channels.index(color_select.value)]
                    fig.add_scatter(x=x, y=y, hovertext=[name]*len(x),
                                    marker=dict(color=c, colorscale='Viridis', 
                                                showscale=True, 
                                                colorbar=dict(title=f'{color_select.value} [{color_unit}]'),),
                            mode='markers', # 'markers' mode seems to be memory intensive
                            )
                case "3D":
                    x, y, z = downsample_uniform(x=dataset.data[:, dataset.channels.index(x_channel)],
                                                 y=dataset.data[:, dataset.channels.index(y_channel)],
                                                 c=dataset.data[:, dataset.channels.index(z_select.value)],
                                                 factor=downsample_slider.value)
                case "3D Color":
                    x, y, z, c = downsample_uniform(x=dataset.data[:, dataset.channels.index(x_channel)],
                                                    y=dataset.data[:, dataset.channels.index(y_channel)],
                                                    c=dataset.data[:, dataset.channels.index(z_select.value)],
                                                    d=dataset.data[:, dataset.channels.index(color_select.value)],
                                                    factor=downsample_slider.value)
            
        x_unit = dataset.units[dataset.channels.index(x_channel)]
        y_unit = dataset.units[dataset.channels.index(y_channel)]

        if len(names) == 1:
            title = name
        else:
            title = ""
        fig.update_layout(title=f"{title} <br><sup>Plot Subtitle</sup>",
                            #title=f"{title} <br><sup>{conditons}</sup>",
                            xaxis_title=f"{x_channel} [{x_unit}]",
                            yaxis_title=f"{y_channel} [{y_unit}]",
                            
                            )
        match plot_radio_group.value:
            case "2D":
                fig.update_traces(hovertemplate = f"{x_channel}: %{{x:.2f}} {x_unit}<br>{y_channel}: %{{y:.2f}} {y_unit}<extra></extra>",)
            case "2D Color":
                fig.update_traces(hovertemplate = f"<b>%{{hovertext}}</b><br>" +
                                  f"{x_channel}: %{{x:.2f}} {x_unit}<br>" +
                                  f"{y_channel}: %{{y:.2f}} {y_unit}<br>" +
                                  f"{color_select.value}: %{{marker.color:.2f}} {color_unit}<extra></extra>",
                                  marker=dict(cmin = min(c), cmax=max(c), 
                                              colorscale=color_map.value, 
                                                showscale=True,))
                fig.update_layout(showlegend=False)
        plotly_pane.object = fig



## Sidebar Widgets
import_button = pn.widgets.Button(name='Import Data', button_type='primary')
pn.bind(callback.import_data, import_button.param.clicks, watch=True)

# Function to color the dataset rows in the data table
def cell_color(column):
    if column.name == '':
        background_color = dm.list_colors()
    else:
        background_color = [''] * len(column)
    return [f'background-color: {color}' for color in background_color]

data_table = pn.widgets.Tabulator(pd.DataFrame(columns=['Dataset','']), 
                                  show_index=False, 
                                  configuration={'columnDefaults':{'headerSort':False}},
                                  selectable='checkbox',
                                  sizing_mode='stretch_both',
                                  min_height=400,
                                  editors={'Dataset':None,'': None},
                                  widths={'Dataset': 230, '': 20},
                                  )
data_table.style.apply(cell_color)

unit_select = pn.widgets.Select(name='Unit System', options=['USCS', 'Metric'], value='USCS', 
                                description="USCS: lb, ft-lb, in, psi, mph, deg F \n\r" \
                                "Metric: N, N-m, cm, kPa, kph, deg C",
                                sizing_mode='stretch_width')
sign_select = pn.widgets.Select(name='Sign Convention', 
                                options=['SAE', 'Adapted SAE', 'ISO', 'Adapted ISO'], 
                                value='ISO',
                                description="SAE: As supplied from TTC \n\r" \
                                "Adapted SAE: Used in Pacejka 2012 \n\r" \
                                "ISO: Used in most commercial sim tools (ADAMS, MF-Tyre/MF-Swift, ect.) \n\r" \
                                "Adapted ISO: Used in Besselink 2000",
                                sizing_mode='stretch_width')

template.sidebar.objects = [import_button, 
                            data_table, 
                            pn.Row(unit_select, sign_select)]

## Main pane
# Bind the plotly theme to the panel theme
px.defaults.template = "plotly_dark" if template.theme.name == "DarkTheme" else "plotly_white"

# Initial empty figure
plotly_pane = pn.pane.Plotly(px.scatter(), sizing_mode='stretch_both')

# plot type selection
plot_radio_group = pn.widgets.RadioBoxGroup(name='Plot Type', 
                                       options=['2D', '2D Color', '3D', '3D Color'], 
                                       inline=True)

# Define plot states for enabling/disabling axis selectors
plot_states = {
    "2D":       {"x": False, "y": False, "z": True,  "c": True},
    "2D Color": {"x": False, "y": False, "z": True,  "c": False},
    "3D":       {"x": False, "y": False, "z": False, "c": True},
    "3D Color": {"x": False, "y": False, "z": False, "c": False},
}
pn.bind(callback.update_plot_type, plot_radio_group.param.value, watch=True)

x_select = pn.widgets.Select(name='X-Axis', options=[], 
                             sizing_mode='stretch_width',
                             disabled=False)
y_select = pn.widgets.Select(name='Y-Axis', options=[], 
                             sizing_mode='stretch_width',
                             disabled=False)
z_select = pn.widgets.Select(name='Z-Axis', options=[], 
                             sizing_mode='stretch_width',
                             disabled=True)
color_select = pn.widgets.Select(name='Colorbar', options=[], 
                                 sizing_mode='stretch_width',
                                 disabled=True)

color_map = pn.widgets.ColorMap(options={'Inferno':px.colors.sequential.Inferno,
                                         'Viridis':px.colors.sequential.Viridis,
                                         'Jet':px.colors.sequential.Jet,},
                                         ncols =1,
                                         )

plot_data_button = pn.widgets.Button(name='Plot Data', button_type='primary')
pn.bind(callback.plot_data, plot_data_button.param.clicks, watch=True)

downsample_slider = pn.widgets.IntSlider(name='Downsample Rate', start=1, end=10, 
                                         step=1, value=5, sizing_mode='stretch_width')

template.main.objects = [pn.Column(plotly_pane,
                         pn.Row(pn.Column(pn.Row(plot_radio_group,color_map),
                         pn.Row(x_select, y_select, z_select, color_select)),
                         pn.Column(pn.Row(pn.Row(sizing_mode='stretch_width'),
                                   plot_data_button),
                                   downsample_slider)))]

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True.
    server = template.show(threaded=True)

    def destroyed(session_context):
         logger.info("Shutting down server...")
         server.stop()
    pn.state.on_session_destroyed(destroyed)
else:
    # If the application is run directly (e.g. panel serve main.py --show)
    template.servable()
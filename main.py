# main.py
import panel as pn
import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import sys
import yaml
from pathlib import Path
import webbrowser

from scripts.tk_utilities import Tk_utils 
from scripts.logger_setup import logger
import scripts.dataio as IO
from scripts.unit_conversion import UnitSystemConverter
from scripts.convention_conversion import ConventionConverter
from scripts.processing import downsample_uniform
from scripts.plotting import PlottingUtils

css = """
#sidebar > ul
{height: calc(100% - 2em);}
"""

pn.extension('tabulator','plotly', raw_css=[css])

with open("config.yaml") as f:
    config = yaml.safe_load(f)

dm = IO.DataManager()

# Define the main application template
template = pn.template.FastListTemplate(
    title='GripLab',
    sidebar_width=400,
    #right_sidebar_width=400,
    accent="#2A3F5F",
    theme=config['theme'],
)

# Define colorway for plots
color = config['ploting']['colorway']
colorway = px.colors.qualitative.__getattribute__(color) if hasattr(px.colors.qualitative, color) else px.colors.qualitative.G10

class callback:
    def help_selection(clicked):
        logger.debug(f"Help menu clicked: {clicked}")
        match clicked:
            case 'signcon':
                logger.info("Opening Sign Convention Documentation...")
                webbrowser.open_new(str(Path('docs/Sign_Convention.pdf')))
            case 'github':
                logger.info("Opening GitHub Repository...")
                webbrowser.open_new("https://github.com/GraysonBrowne/GripLab/blob/main/README.md")

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
            
            # Assign a color to the dataset based on the number of existing datasets
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

            # Update command channel options
            callback.update_cmd_options(event=None)
            logger.info(f"Data imported from {file_path.name}: {data}")

    def update_plot_type(event):
        # Enable/disable axis selectors based on the selected plot type
        states = plot_states.get(event)
        x_select.disabled = states["x"]
        y_select.disabled = states["y"]
        z_select.disabled = states["z"]
        color_select.disabled = states["c"]
        color_map.disabled = states["c"]

    def update_scatter_plot(clicks):
        if data_table.selection == []:
            logger.warning("No datasets selected to plot.")
            return
        plotly_pane.object = PlottingUtils.plot_data(data_table,dm, x_select, 
                                                     y_select, z_select, 
                                                     color_select, unit_select,
                                                     sign_select, plot_radio_group,
                                                     color_map, downsample_slider)
        
    def update_cmd_options(event):
        # Update command channel options to prevent duplicate selections
        channels = dm.get_channels(dm.list_datasets())
        cmd_channels = [chan for chan in channels if chan.startswith('Cmd')]
        selectors = [cmd_select_1, cmd_select_2, cmd_select_3, cmd_select_4]
        selected = [sel.value for sel in selectors]

        # Update options for each selector
        for i, sel in enumerate(selectors):
            excluded = set(selected) - {selected[i]}
            sel.options = [""] + [chan for chan in cmd_channels if chan not in excluded]

 

## Header widgets
menu_items = [('GitHub Repository','github'),('Sign Convention','signcon')]
help_menu_button = pn.widgets.MenuButton(name="Help", items=menu_items, 
                                         button_type='primary', width=100)
pn.bind(callback.help_selection, help_menu_button.param.clicked, watch=True)

template.header.append(pn.Row(pn.Row(sizing_mode='stretch_width'),help_menu_button))

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
                                  min_height=150,
                                  editors={'Dataset':None,'': None},
                                  widths={'Dataset': 300, '': 20},
                                  )
data_table.style.apply(cell_color)

model_table = pn.widgets.Tabulator(pd.DataFrame(columns=['Model','']), 
                                  show_index=False, 
                                  configuration={'columnDefaults':{'headerSort':False}},
                                  selectable='checkbox',
                                  sizing_mode='stretch_both',
                                  min_height=150,
                                  editors={'Model':None,'': None},
                                  widths={'Model': 300, '': 20},
                                  )

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

plot_data_button = pn.widgets.Button(name='Plot Data', button_type='primary',sizing_mode='stretch_width')
pn.bind(callback.update_scatter_plot, plot_data_button.param.clicks, watch=True)

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
                                         'Jet':['#010179','#022291','#0450b2',
                                                 '#0aa5c1','#4ffdc8','#c8ff3a',
                                                 '#ffaf02','#fc1d00','#c10000',
                                                 '#810001'],},
                                         ncols =1,width=200
                                         )


cmd_select_1 = pn.widgets.Select(name='Conditional Parsing:', options=[], 
                                 sizing_mode='stretch_width', min_width=80)
cmd_select_2 = pn.widgets.Select(name=' ', options=[], 
                                 sizing_mode='stretch_width', min_width=80, margin=(9,10,5,10))
cmd_select_3 = pn.widgets.Select(name=' ', options=[], 
                                 sizing_mode='stretch_width', min_width=80, margin=(9,10,5,10))
cmd_select_4 = pn.widgets.Select(name=' ', options=[], 
                                 sizing_mode='stretch_width', min_width=80, margin=(9,10,5,10))
pn.bind(callback.update_cmd_options, cmd_select_1.param.value, watch=True)
pn.bind(callback.update_cmd_options, cmd_select_2.param.value, watch=True)
pn.bind(callback.update_cmd_options, cmd_select_3.param.value, watch=True)
pn.bind(callback.update_cmd_options, cmd_select_4.param.value, watch=True)

cmd_multi_select_1 = pn.widgets.MultiSelect(options=[], size=8, 
                                            sizing_mode='stretch_width', height=100, min_width=80)
cmd_multi_select_2 = pn.widgets.MultiSelect(options=[], size=8, 
                                            sizing_mode='stretch_width', height=100, min_width=80)
cmd_multi_select_3 = pn.widgets.MultiSelect(options=[], size=8, 
                                            sizing_mode='stretch_width', height=100, min_width=80)
cmd_multi_select_4 = pn.widgets.MultiSelect(options=[], size=8, 
                                            sizing_mode='stretch_width', height=100, min_width=80)

downsample_slider = pn.widgets.IntSlider(name='Down Sample Rate', start=1, end=10, 
                                         step=1, value=5,
                                         sizing_mode='stretch_width',)
template.sidebar.append(pn.Column(import_button, 
                            data_table, model_table,
                            pn.layout.Divider(),
                            pn.Row(plot_radio_group,plot_data_button), 
                                  pn.Row(pn.GridBox(x_select, y_select, z_select, color_select, ncols=2,sizing_mode='stretch_width'),pn.Column(downsample_slider,color_map,width=220)),
                                  pn.GridBox(cmd_select_1, cmd_select_2,cmd_select_3, cmd_select_4,
                                  cmd_multi_select_1, cmd_multi_select_2, cmd_multi_select_3, cmd_multi_select_4, ncols=4),
                                  pn.Row(unit_select, sign_select)))

## Main pane
# Bind the plotly theme to the panel theme
px.defaults.template = "plotly_dark" if template.theme.name == "DarkTheme" else "plotly_white"

# Initial empty figure
plotly_pane = pn.pane.Plotly(px.scatter(), sizing_mode='stretch_both')



template.main.append(pn.Column(plotly_pane))


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
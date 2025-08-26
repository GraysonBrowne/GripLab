# main.py
import panel as pn
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path
from scripts.tk_utilities import Tk_utils 
from scripts.logger_setup import logger
import scripts.dataio as IO
from scripts.unit_conversion import UnitSystemConverter
from scripts.convention_conversion import ConventionConverter

pn.extension('tabulator','plotly')

dm = IO.DataManager()

# Define the main application template
template = pn.template.FastListTemplate(
    title='GripLab',
    #sidebar_width=300,
    header_background='#2A3F5F',
    header_color='white',
    accent_base_color='#2A3F5F',
    theme='dark',
)

class callback:
    def import_data(clicks):
        # Open file dialog for user to select a data file
        file_path = Path(Tk_utils.select_file(filetypes=[('MATLAB/ASCII Data Files',
                                                          '*.mat *.dat *.txt')], 
                                              initialdir='.'),)
        
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
        
        # Determine file type and import data accordingly
        if file_path.suffix.lower() == '.mat':
            data = IO.import_mat(file_path, name)
        elif file_path.suffix.lower() in ['.dat', '.txt']:
            data = IO.import_dat(file_path, name)
        else:
            logger.error("Unsupported file type selected.")
            return

        # Add the imported dataset to the DataManager
        dm.add_dataset(name,data)

        # Update the data table to reflect the newly added dataset
        data_table.value = pd.DataFrame({'Dataset': dm.list_datasets()})

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

        fig = px.scatter()

        for name in names:
            dataset_unit = UnitSystemConverter.convert_dataset(dm.get_dataset(name),
                                                               to_system=unit_select.value)
            dataset = ConventionConverter.convert_dataset_convention(dataset_unit,
                                                                     target_convention=sign_select.value)
            
            fig.add_scatter(x=dataset.data[:, dataset.channels.index(x_channel)],
                            y=dataset.data[:, dataset.channels.index(y_channel)],
                            name=name,
                            #mode='markers', # 'markers' mode seems to be memory intensive
                            )
            
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
        fig.update_traces(hovertemplate = f"{x_channel}: %{{x}} {x_unit}<br>{y_channel}: %{{y}} {y_unit}<extra></extra>",)
        plotly_pane.object = fig



## Sidebar Widgets
import_button = pn.widgets.Button(name='Import Data', button_type='primary')
pn.bind(callback.import_data, import_button.param.clicks, watch=True)

data_table = pn.widgets.Tabulator(pd.DataFrame(columns=['Dataset']), 
                                  show_index=False, 
                                  configuration={'columnDefaults':{'headerSort':False}},
                                  selectable='checkbox',
                                  sizing_mode='stretch_both',
                                  min_height=400
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
color_select = pn.widgets.Select(name='Color', options=[], 
                                 sizing_mode='stretch_width',
                                 disabled=True)

plot_data_button = pn.widgets.Button(name='Plot Data', button_type='primary')
pn.bind(callback.plot_data, plot_data_button.param.clicks, watch=True)

template.main.objects = [pn.Column(plotly_pane,
                         pn.Row(pn.Column(plot_radio_group,
                         pn.Row(x_select, y_select, z_select, color_select)),
                                plot_data_button))]

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
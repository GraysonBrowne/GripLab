# main.py
import panel as pn
from panel.io import hold
import numpy as np
import pandas as pd
import plotly.express as px

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

sidebar_height = """
#sidebar > ul
{height: calc(100% - 2em);}
"""
modal_width = """
#pn-Modal {
    --dialog-width: auto;
}"""

modal_content = """
.pn-modal-content {
    position: relative;
    top: -30px;
}
"""

modal_close_pos = """
.pn-modal-close {
    position: relative;
    left: calc(100% - 40px);
    top: -17px;
}
"""
table_buttons=["https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css"]
pn.extension('tabulator','plotly', raw_css=[sidebar_height], css_files=table_buttons, notifications=True)
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True.
    local_path = Path(sys.executable).parent
else:
    # If the application is run directly
    local_path = Path(__file__).parent

try:
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

except Exception as e:
    config = {
        'theme': 'dark',
        'unit_system': 'USCS',
        'sign_convention': 'ISO',
        'demo_mode': False,
        'plotting': {
            'colorway': 'G10',
            'colormap': 'Inferno',
        },
        'paths': {
            'data_dir': str(local_path),
        }
    }

dm = IO.DataManager()

# Define the main application template
template = pn.template.FastListTemplate(
    title='GripLab',
    sidebar_width=420,
    accent="#2A3F5F",
    theme=config['theme'],
    raw_css=[modal_width,modal_close_pos,modal_content],
)

# Define colorway for plots https://plotly.com/python/discrete-color/#color-sequences-in-plotly-express
color = config['plotting']['colorway']
colorway = px.colors.qualitative.__getattribute__(color) if hasattr(px.colors.qualitative, color) else px.colors.qualitative.G10

# ------------------------------
# 1. WIDGETS
# ------------------------------

######### Header #########
menu_items = [('Sign Convention','signcon'),('GitHub Repository','readme'),
              ('Discussion Board','discuss'),('Report An Issue','issue')]
help_menu_button = pn.widgets.MenuButton(name="Help", items=menu_items, 
                                         button_type='primary', width=100)
settings_button = pn.widgets.Button(name="Settings", 
                                         button_type='primary', width=100)
# Header layout
template.header.append(pn.Row(pn.layout.HSpacer(), settings_button, help_menu_button))

######### Sidebar #########
import_button = pn.widgets.Button(name='Import Data', button_type='primary')
data_table = pn.widgets.Tabulator(pd.DataFrame(columns=['Dataset','']),
                                  buttons = {'trash': '<i class="fa fa-trash"></i>'},
                                  show_index=False, 
                                  configuration={'columnDefaults':{'headerSort':False}},
                                  selectable='checkbox',
                                  sizing_mode='stretch_both',
                                  min_height=150,
                                  editors={'': None,'trash': None},
                                  widths={'Dataset': 279, '': 40,'trash': 40},
                                  )
model_table = pn.widgets.Tabulator(pd.DataFrame(columns=['Model','']), 
                                  show_index=False, 
                                  configuration={'columnDefaults':{'headerSort':False}},
                                  selectable='checkbox',
                                  sizing_mode='stretch_both',
                                  min_height=150,
                                  editors={'Model':None,'': None},
                                  widths={'Model': 300, '': 20},
                                  )
plot_settings_button = pn.widgets.Button(name='⚙️', button_type='default', width=43, margin=(5,0,5,15))
plot_data_button = pn.widgets.Button(name='Plot Data', button_type='primary',sizing_mode='stretch_width', 
                                     margin=(5,10,5,7))
plot_radio_group = pn.widgets.RadioBoxGroup(name='Plot Type', 
                                       options=['2D', '2D Color', '3D', '3D Color'], 
                                       inline=True)
# Define plot states for enabling/disabling axis selectors
plot_states = {
    "2D":       {"z": True,  "c": True},
    "2D Color": {"z": True,  "c": False},
    "3D":       {"z": False, "c": True},
    "3D Color": {"z": False, "c": False},
}
x_select = pn.widgets.Select(name='X-Axis', options=[], 
                             sizing_mode='stretch_width')
y_select = pn.widgets.Select(name='Y-Axis', options=[], 
                             sizing_mode='stretch_width')
z_select = pn.widgets.Select(name='Z-Axis', options=[], 
                             sizing_mode='stretch_width',
                             disabled=plot_states[plot_radio_group.value]["z"])
color_select = pn.widgets.Select(name='Colorbar', options=[], 
                                 sizing_mode='stretch_width',
                                 disabled=plot_states[plot_radio_group.value]["c"])
cmd_select_1 = pn.widgets.Select(name='Conditional Parsing', options=[], 
                                 sizing_mode='stretch_width', min_width=80)
cmd_select_2 = pn.widgets.Select(name=' ', options=[], 
                                 sizing_mode='stretch_width', min_width=80, margin=(9,10,5,10))
cmd_select_3 = pn.widgets.Select(name=' ', options=[], 
                                 sizing_mode='stretch_width', min_width=80, margin=(9,10,5,10))
cmd_select_4 = pn.widgets.Select(name=' ', options=[], 
                                 sizing_mode='stretch_width', min_width=80, margin=(9,10,5,10))
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
node_count_text = pn.widgets.StaticText(name="Node Count", value="0", sizing_mode='stretch_width',)
# data info widgets
data_select = pn.widgets.Select(name='Dataset', options=[],sizing_mode='stretch_width',)
data_name_text_input = pn.widgets.TextInput(name='Name',sizing_mode='stretch_width',
                                            disabled=True)
node_color_picker = pn.widgets.ColorPicker(name='Color', disabled=True)
tire_id_text_input = pn.widgets.TextInput(name='Tire ID',sizing_mode='stretch_width',
                                          disabled=True)
rim_width_text_input = pn.widgets.IntInput(name='Rim Width [in]', width=100,
                                           disabled=True)
notes_area_input = pn.widgets.TextAreaInput(name='Notes',sizing_mode='stretch_width',
                                            disabled=True)
update_data_button = pn.widgets.Button(name='Update Dataset', button_type='primary',
                                       sizing_mode='stretch_width',disabled=True)

# Sidebar layout
plot_data_tab = pn.Column(pn.Row(plot_radio_group,plot_settings_button,plot_data_button), 
                                  pn.Row(pn.GridBox(x_select, y_select, z_select, 
                                                    color_select, ncols=2, 
                                                    sizing_mode='stretch_width'),
                                         pn.Column(downsample_slider, node_count_text, width=150)),
                                  pn.GridBox(cmd_select_1, cmd_select_2,cmd_select_3, cmd_select_4,
                                  cmd_multi_select_1, cmd_multi_select_2, cmd_multi_select_3, cmd_multi_select_4, ncols=4),
                                  name = "Plot Data",)
data_info_tab = pn.Column(data_select, 
                          pn.Row(data_name_text_input, node_color_picker,),
                          pn.Row(tire_id_text_input, rim_width_text_input,),
                          notes_area_input,
                          update_data_button,
                          name = 'Data Info',)
info_tab = pn.layout.Tabs(plot_data_tab,data_info_tab,sizing_mode='stretch_width')
template.sidebar.append(pn.Column(import_button,
                                  data_table,
                                  #model_table,
                                  pn.layout.Divider(),
                                  info_tab
                                  ))

######### Modals #########
# Settings widgets
default_theme_select = pn.widgets.Select(name='Default Theme', 
                                         options={'Light':'default','Dark':'dark'}, 
                                         value=config['theme'],
                                         description="Sets the default theme on application start.",
                                         sizing_mode='stretch_width')
colorway_dict ={'G10'    :px.colors.qualitative.G10,
                'Plotly' :px.colors.qualitative.Plotly,
                'D3'     :px.colors.qualitative.D3,
                'T10'    :px.colors.qualitative.T10,
                'Set1'   :px.colors.qualitative.Set1,
                'Dark2'  :px.colors.qualitative.Dark2,}
colorway_select = pn.widgets.ColorMap(name='Color Sequence', options= colorway_dict,
                                      value=colorway_dict[config['plotting']['colorway']],
                                      ncols =1,width=200)

demo_switch = pn.widgets.Switch(name='Demo Mode', value=config['demo_mode'])
data_dir_button = pn.widgets.Button(name='Set Directory', button_type='default', margin=(28,5,2,15))
data_dir_input = pn.widgets.TextInput(name='Data Directory', value=config['paths']['data_dir'], sizing_mode='stretch_width')
unit_select = pn.widgets.Select(name='Unit System', options=['USCS', 'Metric'], value=config['unit_system'], 
                                description="USCS: lb, ft-lb, in, psi, mph, deg F \n\r" \
                                "Metric: N, N-m, cm, kPa, kph, deg C",
                                sizing_mode='stretch_width')
sign_select = pn.widgets.Select(name='Sign Convention', 
                                options=['SAE', 'Adapted SAE', 'ISO', 'Adapted ISO'], 
                                value=config['sign_convention'],
                                description="SAE: As supplied from TTC \n\r" \
                                "Adapted SAE: Used in Pacejka 2012 \n\r" \
                                "ISO: Used in most commercial sim tools (ADAMS, MF-Tyre/MF-Swift, ect.) \n\r" \
                                "Adapted ISO: Used in Besselink 2000",
                                sizing_mode='stretch_width')
save_settings_button = pn.widgets.Button(name='Save Settings', button_type='primary',margin=(10,15,0,15), width=200)
# Remove confirmation widgets
confirm_remove_data = pn.pane.HTML("""""", styles={"font-size":"16px",}, margin=(0,15,0,15))
cancel_remove_button = pn.widgets.Button(name='Cancel', button_type='default',margin=(10,10,0,10), width=200)
confirm_remove_button = pn.widgets.Button(name='Remove Dataset', button_type='primary',margin=(10,10,0,10), width=200)
# Plot settings widgets
title_text_input = pn.widgets.TextInput(name='Title', value='', placeholder='Tire ID',sizing_mode='stretch_width')
subtitle_text_input = pn.widgets.TextInput(name='Subtitle', value='', placeholder='SA:() | SR:() | IA:() | FZ:() | P:() | V:() | Rim Width:()',
                                           sizing_mode='stretch_width')
x_label_text_input = pn.widgets.TextInput(name='X-Axis Label', value='', placeholder='Channel [unit]',sizing_mode='stretch_width')
y_label_text_input = pn.widgets.TextInput(name='Y-Axis Label', value='', placeholder='Channel [unit]',sizing_mode='stretch_width')
z_label_text_input = pn.widgets.TextInput(name='Z-Axis Label', value='', placeholder='Channel [unit]',sizing_mode='stretch_width',
                                          disabled=plot_states[plot_radio_group.value]["z"])
c_label_text_input = pn.widgets.TextInput(name='Colorbar Label', value='', placeholder='Channel [unit]',sizing_mode='stretch_width',
                                          disabled=plot_states[plot_radio_group.value]["c"])
font_size_input = pn.widgets.IntSlider(name='Font Size', value=18, start=4, end=32,
                                         step=1, sizing_mode='stretch_width')
marker_size_input = pn.widgets.IntSlider(name='Marker Size', value=10, start=2, end=18, 
                                         step=1, sizing_mode='stretch_width')
color_map_options = {'Jet':['#010179','#022291','#0450b2',
                            '#0aa5c1','#4ffdc8','#c8ff3a',
                            '#ffaf02','#fc1d00','#c10000',
                            '#810001'],
                     'Inferno':px.colors.sequential.Inferno,
                     'Viridis':px.colors.sequential.Viridis,
                     }
color_map = pn.widgets.ColorMap(name='Color Map',options=color_map_options,
                                value = color_map_options[config['plotting']['colormap']],
                                ncols =1,width=200,)
# Modal layouts
settings_layout = pn.Column(pn.pane.HTML("""<h1>Settings</h1>""", styles={"height":"40px",
                                                                          "line-height":"0px",
                                                                          "margin-top":"0px",
                                                                          "margin-bottom":"0px",},),
                               pn.Row(default_theme_select, colorway_select, pn.Column(pn.widgets.StaticText(value="Demo Mode"),
                                                                                                  demo_switch)),
                               pn.Row(unit_select, sign_select),
                               pn.Row(data_dir_button,data_dir_input),
                               pn.Row(pn.layout.HSpacer(),save_settings_button),
                               width = 800,margin=(0,20),)
remove_data_layout = pn.Column(pn.pane.HTML("""<h1>Remove Dataset?</h1>""", styles={"height":"40px",
                                                                          "line-height":"0px",
                                                                          "margin-top":"0px",
                                                                          "margin-bottom":"0px",}),
                               confirm_remove_data,
                               pn.Row(pn.layout.HSpacer(),confirm_remove_button,cancel_remove_button),
                               width = 440,
                               margin=(0,20),)
plot_settings_layout = pn.Column(pn.pane.HTML("""<h1>Plot Settings</h1>""", styles={"height":"40px",
                                                                          "line-height":"0px",
                                                                          "margin-top":"0px",
                                                                          "margin-bottom":"0px",}),
                                 title_text_input, subtitle_text_input, 
                                 x_label_text_input,  y_label_text_input, 
                                 z_label_text_input,  
                                 c_label_text_input, color_map, font_size_input, marker_size_input,
                                 width = 450,
                                 margin=(0,20,0,20),)
modal_objects = pn.Column()
template.modal.append(modal_objects)


######### Main #########
# Bind the plotly theme to the panel theme
px.defaults.template = "plotly_dark" if template.theme.name == "DarkTheme" else "plotly_white"
plotly_pane = pn.pane.Plotly(px.scatter(), sizing_mode='stretch_both')
# Main layout
template.main.append(pn.Column(plotly_pane))

# ------------------------------
# 2. CALLBACKS
# ------------------------------
def settings_menu(event):
    modal_objects.objects = [settings_layout]
    template.open_modal()

pn.bind(settings_menu, settings_button.param.clicks, watch=True)

def update_theme(event):
    logger.debug(f"Theme selection changed: {event}")
    config['theme'] = event

pn.bind(update_theme, default_theme_select.param.value, watch=True)

def update_colorway(event):
    selection = list(colorway_dict.keys())[list(colorway_dict.values()).index(event)]
    logger.debug(f"Colorway selection changed: {selection}")
    config['plotting']['colorway'] = selection
    
pn.bind(update_colorway, colorway_select.param.value, watch=True)

def update_colormap(event):
    selection = list(color_map_options.keys())[list(color_map_options.values()).index(event)]
    logger.debug(f"Colormap selection changed: {selection}")
    config['plotting']['colormap'] = selection

pn.bind(update_colormap, color_map.param.value, watch=True)

def update_demo_mode(event):
    logger.debug(f"Demo mode toggled: {event}")
    if event:
        data_table.value = pd.DataFrame({'Dataset': dm.list_demo_names(),
                                            '': ['']*len(dm.list_demo_names())})
        data_select.options = [''] + dm.list_demo_names()
    else:
        data_table.value = pd.DataFrame({'Dataset': dm.list_datasets(),
                                           '': ['']*len(dm.list_datasets())})
        data_select.options = [''] + dm.list_datasets()
    config['demo_mode'] = event

pn.bind(update_demo_mode, demo_switch.param.value, watch=True)

def update_unit_system(event):
    logger.debug(f"Unit system selection changed: {event}")
    config['unit_system'] = event

pn.bind(update_unit_system, unit_select.param.value, watch=True)

def update_sign_convention(event):
    logger.debug(f"Sign convention selection changed: {event}")
    config['sign_convention'] = event

pn.bind(update_sign_convention, sign_select.param.value, watch=True)

def update_data_dir(event):
    logger.debug(f"Data directory input changed: {event}")
    config['paths']['data_dir'] = event

pn.bind(update_data_dir, data_dir_input.param.value_input, watch=True)

def get_data_dir(clicks):
    # Open directory dialog for user to select a data directory
    directory = Tk_utils.select_dir(initialdir=config['paths']['data_dir'],)
    if directory:
        data_dir_input.value = directory
        config['paths']['data_dir'] = directory
        logger.info(f"Data directory set to: {directory}")

pn.bind(get_data_dir, data_dir_button.param.clicks, watch=True)

def save_settings(clicks):
    try:
        with open("config.yaml", 'w') as f:
            yaml.dump(config, f)
        logger.info(f"Settings saved to config.yaml: {config}")
        template.close_modal()
    except Exception as e:
        logger.error(f"Error saving settings: {e}", exc_info=True)

pn.bind(save_settings, save_settings_button.param.clicks, watch=True)

def help_selection(clicked):
    logger.debug(f"Help menu clicked: {clicked}")
    match clicked:
        case 'signcon':
            logger.info("Opening Sign Convention Documentation...")
            webbrowser.open_new(str(Path('docs/Sign_Convention.pdf')))
        case 'readme':
            logger.info("Opening GitHub Repository...")
            webbrowser.open_new("https://github.com/GraysonBrowne/GripLab/blob/main/README.md")
        case 'discuss':
            logger.info("Opening Discussion Board...")
            webbrowser.open_new("https://github.com/GraysonBrowne/GripLab/discussions")
        case 'issue':
            logger.info("Opening Issue Reporting Page...")
            webbrowser.open_new("https://github.com/GraysonBrowne/GripLab/issues")

pn.bind(help_selection, help_menu_button.param.clicked, watch=True)

import_tracker = 0
def import_data(clicks):
    global import_tracker
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

        demo_copy = 0
        demo_name = 'Demo data'
        while demo_name in dm.list_demo_names():
            if demo_copy == 0:
                demo_name = 'Demo data'
            demo_copy += 1
            demo_name = f"{'Demo data'} ({demo_copy})"

        # If no file was selected, exit the function
        if str(file_path) == '.':
            return
        
        # Assign a color to the dataset based on the number of existing datasets
        colorway = px.colors.qualitative.__getattribute__(config['plotting']['colorway'])
        color = colorway[import_tracker % len(colorway)]

        # Determine file type and import data accordingly
        if file_path.suffix.lower() == '.mat':
            data = IO.import_mat(file_path, name, color, demo_name)
        elif file_path.suffix.lower() in ['.dat', '.txt']:
            data = IO.import_dat(file_path, name, color, demo_name)
        else:
            logger.error("Unsupported file type selected.")
            return

        # Add the imported dataset to the DataManager
        dm.add_dataset(name,data)

        # Update the data table to reflect the newly added dataset
        if config['demo_mode']:
            data_table.value = pd.DataFrame({'Dataset': dm.list_demo_names(),
                                               '': ['']*len(dm.list_demo_names())})
        else:
            data_table.value = pd.DataFrame({'Dataset': dm.list_datasets(),
                                               '': ['']*len(dm.list_datasets())})

        # Select the newly added dataset in the data table
        selected = data_table.selection
        if selected == []:
            data_table.selection = [data_table.value.index[-1]]
        else:
            data_table.selection = selected + [data_table.value.index[-1]]

        # Update channel selection options based on the imported data
        channels = dm.get_channels(dm.list_datasets())
        x_select.options = channels
        y_select.options = channels
        z_select.options = channels
        color_select.options = channels

        # Update command channel options
        update_cmd_options(event=None)

        # Update data info options
        if demo_switch.value:
            data_select.options = [''] + dm.list_demo_names()
        else:
            data_select.options = [''] + dm.list_datasets()

        import_tracker += 1
        logger.info(f"Data imported from {file_path.name}: {data}")

pn.bind(import_data, import_button.param.clicks, watch=True)

def cancel_data_removal(clicks):
    logger.info("Data removal cancelled by user.")
    template.close_modal()

pn.bind(cancel_data_removal, cancel_remove_button.param.clicks, watch=True)

def remove_data(clicks):
    dm.remove_dataset(channel_removal_tracker)
    logger.debug(f"Datasets after removal: {dm.list_datasets()}")
    # Update the data table to reflect the removed dataset
    data_table.value = pd.DataFrame({'Dataset': dm.list_datasets(),
                                        '': ['']*len(dm.list_datasets())})
    logger.debug(f"Data table updated: {data_table.value}")
    # Update channel selection options based on remaining data
    channels = dm.get_channels(dm.list_datasets())
    logger.debug(f"Available channels after removal: {channels}")
    x_select.options = channels
    y_select.options = channels
    z_select.options = channels
    color_select.options = channels
    logger.debug(f"Axis selectors updated: x:{x_select.options}, y:{y_select.options}, z:{z_select.options}, color:{color_select.options}")
    # Update command channel options
    update_cmd_options(event=None)
    logger.info(f"Dataset removed: {channel_removal_tracker}")
    template.close_modal()

pn.bind(remove_data, confirm_remove_button.param.clicks, watch=True)

@hold()
def update_plot_type(event):
    # Enable/disable axis selectors based on the selected plot type
    states = plot_states.get(event)
    z_select.disabled = states["z"]
    color_select.disabled = states["c"]
    z_label_text_input.disabled = states["z"]
    c_label_text_input.disabled = states["c"]

pn.bind(update_plot_type, plot_radio_group.param.value, watch=True)

def open_plot_settings(event):
    logger.info("Opening plot settings.")
    modal_objects.objects = [plot_settings_layout]
    template.open_modal()

pn.bind(open_plot_settings, plot_settings_button.param.clicks, watch=True)

def update_scatter_plot(clicks):
    if data_table.selection == []:
        logger.warning("No datasets selected to plot.")
        pn.state.notifications.warning('Select a dataset to plot.', duration=4000)
        return
    plotly_pane.object, node_count = PlottingUtils.plot_data(data_table,dm, x_select,
                                                    y_select, z_select,
                                                    color_select, unit_select,
                                                    sign_select, plot_radio_group,
                                                    color_map, downsample_slider,
                                                    cmd_select_1, cmd_select_2,
                                                    cmd_select_3, cmd_select_4,
                                                    cmd_multi_select_1, cmd_multi_select_2,
                                                    cmd_multi_select_3, cmd_multi_select_4,
                                                    config['demo_mode'], title_text_input.value,
                                                    subtitle_text_input.value,
                                                    x_label_text_input.value,
                                                    y_label_text_input.value,
                                                    z_label_text_input.value,
                                                    c_label_text_input.value,
                                                    font_size_input.value,
                                                    marker_size_input.value)
    
    node_count_text.value = str(node_count)

pn.bind(update_scatter_plot, plot_data_button.param.clicks, watch=True)

@hold()
def update_cmd_options(event):
    try:
        # Update command channel options to prevent duplicate selections
        channels = dm.get_channels(dm.list_datasets())
        cmd_channels = [chan for chan in channels if chan.startswith('Cmd')]
        selectors = [cmd_select_1, cmd_select_2, cmd_select_3, cmd_select_4]
        selected = [sel.value for sel in selectors]

        multi_selectors = [cmd_multi_select_1, cmd_multi_select_2, cmd_multi_select_3, cmd_multi_select_4]
        data_selection = data_table.selection
        names = [dm.list_datasets()[idx] for idx in data_selection]
        # Update options for each selector
        for i, sel in enumerate(selectors):
            excluded = set(selected) - {selected[i]}
            sel.options = [""] + [chan for chan in cmd_channels if chan not in excluded]
            data = []
            for name in names:
                dataset = dm.get_dataset(name)
                dataset = UnitSystemConverter.convert_dataset(dataset, to_system=unit_select.value)
                dataset = ConventionConverter.convert_dataset_convention(dataset, target_convention=sign_select.value)
                data.extend(dataset.data[:,dataset.channels.index(sel.value)] if sel.value in dataset.channels else [])
            cmd_data = sorted(np.unique(data).astype(np.int64).tolist(), key=abs)
            cmd_options = {chan: i for i, chan in enumerate([v for v in cmd_data])}
            temp_value = multi_selectors[i].value
            logger.debug(f"cmd options: {cmd_options}")
            multi_selectors[i].options = cmd_options
            multi_selectors[i].value = temp_value
            logger.debug(f"temp value: {temp_value}")
            multi_selectors[i].param.trigger('value')
    except Exception as e:
        logger.error(f"Error updating command options: {e}", exc_info=True)

pn.bind(update_cmd_options, cmd_select_1.param.value, watch=True)
pn.bind(update_cmd_options, cmd_select_2.param.value, watch=True)
pn.bind(update_cmd_options, cmd_select_3.param.value, watch=True)
pn.bind(update_cmd_options, cmd_select_4.param.value, watch=True)
pn.bind(update_cmd_options, unit_select.param.value, watch=True)
pn.bind(update_cmd_options, sign_select.param.value, watch=True)

@hold()
def unpack_data_info(event):
    """
    Populate or reset the data info widgets when a dataset is selected.

    Parameters
    ----------
    event : str
        The dataset identifier (empty string means reset).
    """
    if demo_switch.value:
        widget_map = {
            "data_name_text_input": ("demo_name", data_name_text_input, ""),
            "node_color_picker": ("node_color", node_color_picker, "#000000"),
            "tire_id_text_input": ("demo_tire_id", tire_id_text_input, ""),
            "rim_width_text_input": ("demo_rim_width", rim_width_text_input, 0),
            "notes_area_input": ("demo_notes", notes_area_input, ""),
        }
    else:
        widget_map = {
            "data_name_text_input": ("name", data_name_text_input, ""),
            "node_color_picker": ("node_color", node_color_picker, "#000000"),
            "tire_id_text_input": ("tire_id", tire_id_text_input, ""),
            "rim_width_text_input": ("rim_width", rim_width_text_input, 0),
            "notes_area_input": ("notes", notes_area_input, ""),
        }

    if not event:
        logger.info("Resetting data info widgets (no dataset selected).")
        for _, widget, default in widget_map.values():
            widget.value = default
            widget.disabled = True
        update_data_button.disabled = True
        return

    try:
        if demo_switch.value:
            idx = dm.list_demo_names().index(event)
            name = dm.list_datasets()[idx]
            dataset = dm.get_dataset(name)
        else:
            dataset = dm.get_dataset(event)
        logger.info("Populating data info widgets for dataset: %s", event)

        for attr, widget, _ in widget_map.values():
            widget.value = getattr(dataset, attr)
            widget.disabled = False

        update_data_button.disabled = False

    except Exception as e:
        logger.error("Failed to unpack dataset '%s': %s", event, e, exc_info=True)
        # fallback: reset to safe state
        for _, widget, default in widget_map.values():
            widget.value = default
            widget.disabled = True
        update_data_button.disabled = True

pn.bind(unpack_data_info, data_select.param.value, watch=True)

@hold()
def update_data_info(clicks):
    """
    Update dataset attributes based on widget values and refresh the data table.

    Parameters
    ----------
    clicks : int
        Number of times the update button was clicked (unused, but required by callback signature).
    """

    try:
        
        # Map dataset attributes to widgets
        if demo_switch.value:
            idx = dm.list_demo_names().index(data_select.value)
            name = dm.list_datasets()[idx]
            dataset = dm.get_dataset(name)
            og_name = dataset.demo_name
            widget_map = {
                "demo_name": data_name_text_input,
                "node_color": node_color_picker,
                "demo_tire_id": tire_id_text_input,
                "demo_rim_width": rim_width_text_input,
                "demo_notes": notes_area_input,
            }
        else:
            dataset = dm.get_dataset(data_select.value)
            og_name = dataset.name
            widget_map = {
                "name": data_name_text_input,
                "node_color": node_color_picker,
                "tire_id": tire_id_text_input,
                "rim_width": rim_width_text_input,
                "notes": notes_area_input,
            }
        logger.debug(f"node color:{widget_map['node_color'].value}")
        for attr, widget in widget_map.items():
            setattr(dataset, attr, widget.value)

        if demo_switch.value:
            # Update data manager
            dm.update_demo_name(og_name, dataset.demo_name)
            logger.info("Updated dataset '%s' with new widget values.", dataset.demo_name)

            # Refresh the data table
            datasets = dm.list_demo_names()
            data_table.value = pd.DataFrame({
                "Dataset": datasets,
                "": ["" for _ in datasets]
            })
        else:
            # Update data manager
            dm.update_dataset(og_name, dataset.name)
            logger.info("Updated dataset '%s' with new widget values.", dataset.name)
            
            # Refresh the data table
            datasets = dm.list_datasets()
            data_table.value = pd.DataFrame({
                "Dataset": datasets,
                "": ["" for _ in datasets]
            })
        logger.debug("Data table refreshed with %d datasets.", len(datasets))

        # Update data_select widget
        data_select.options = [""] + datasets
        if demo_switch.value:
            data_select.value = dataset.demo_name
        else:
            data_select.value = dataset.name

    except Exception as e:
        logger.error("Failed to update dataset '%s': %s", data_select.value, e, exc_info=True)
    
pn.bind(update_data_info, update_data_button.param.clicks, watch=True)

###### Tabulator functions #########
 # Color the dataset rows in the data table
def cell_color(column):
    if column.name == '':
        background_color = dm.list_colors()
    else:
        background_color = [''] * len(column)
    return [f'background-color: {color}' for color in background_color]

data_table.style.apply(cell_color)

# Handle row button clicks in the data table
channel_removal_tracker = ''
def confirm_data_removal(event):
    global channel_removal_tracker
    channel_removal_tracker = dm.list_datasets()[event.row]
    confirm_remove_data.object = f"""<p>Are you sure that you want to remove
        <b>{channel_removal_tracker}</b> from the session?</p>"""
    modal_objects.objects = [remove_data_layout]
    template.open_modal()

data_table.on_click(confirm_data_removal, column='trash')

# Open data info layout on color cell slection
def open_data_info(event):
    info_tab.active = 1
    if demo_switch.value:
        data_select.value = dm.list_demo_names()[event.row]
    else:
        data_select.value = dm.list_datasets()[event.row]

data_table.on_click(open_data_info, column='')

# Edit dataset name from data table
@hold()
def edit_data_name(event):
    if demo_switch.value:
        data_select.value = dm.list_demo_names()[event.row]
    else:
        data_select.value = dm.list_datasets()[event.row]
    data_name_text_input.value = event.value
    update_data_info(clicks=None)

data_table.on_edit(edit_data_name)
# ------------------------------
# 3. SERVE
# ------------------------------
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
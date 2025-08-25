# main.py
import panel as pn
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path
from scripts.tk_utilities import Tk_utils 
from scripts.logger_setup import logger
import scripts.dataio as IO

pn.extension('tabulator','plotly')

dm = IO.DataManager()

class callback:
    def import_data(clicks):
        # Open file dialog for user to select a data file
        file_path = Path(Tk_utils.select_file(filetypes=[('Valid File Types',
                                                          '*.mat *.dat *.txt')], 
                                              initialdir='.'),)
        
        name = file_path.stem

        # Handle duplicate dataset names
        if name in dm.list_datasets():
            dm._datasets[name].copy += 1
            name = f"{name} ({dm._datasets[name].copy})"
        
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
        logger.info(f"Data imported from {file_path.name}: {data}")

## Sidebar Widgets
import_button = pn.widgets.Button(name='Import Data', button_type='primary')
pn.bind(callback.import_data, import_button.param.clicks, watch=True)

data_table = pn.widgets.Tabulator(pd.DataFrame(columns=['Dataset']), 
                                  show_index=False, 
                                  configuration={'columnDefaults':{'headerSort':False}},
                                  selectable='checkbox',
                                  sizing_mode='stretch_width',
                                  )

unit_select = pn.widgets.Select(name='Units', options=['USCS', 'Metric'], value='USCS', 
                                description="USCS: lb, ft-lb, in, psi, mph, deg F \n\r" \
                                "Metric: N, N-m, cm, kPa, kph, deg C",
                                sizing_mode='stretch_width')
sign_select = pn.widgets.Select(name='Sign Convention', 
                                options=['SAE', 'Apdapted SAE', 'ISO', 'Adapted ISO'], 
                                value='ISO',
                                description="SAE: As supplied from TTC \n\r" \
                                "Adapted SAE: Used in Pacejka 2012 \n\r" \
                                "ISO: Standard used in most sim tools (ADAMS, MF-Tyre/MF-Swift, ect.) \n\r" \
                                "Adapted ISO: Used in Besselink 2000",
                                sizing_mode='stretch_width')

## Main pane
px.defaults.template = "plotly_dark" if pn.config.theme == "dark" else "plotly_white"
fig = pn.pane.Plotly(px.scatter(), sizing_mode='stretch_both')

# Define the main application template
template = pn.template.FastListTemplate(
    title='GripLab',
    sidebar=[import_button, 
             data_table, 
             pn.Row(unit_select, sign_select)],
    main=[fig],
    #sidebar_width=300,
    header_background='#2A3F5F',
    header_color='white',
    accent_base_color='#2A3F5F',
    theme='dark',
)

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
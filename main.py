# main.py
import panel as pn
import sys
from pathlib import Path
from scripts.tk_utilities import Tk_utils 
from scripts.logger_setup import logger
import scripts.dataio as IO

pn.extension('tabulator')

dm = IO.DataManager()

class callback:
    def import_data(event):
        # Open file dialog for user to select a data file
        file_path = Path(Tk_utils.select_file(filetypes=[('Valid File Types',
                                                          '*.mat *.dat *.txt')], 
                                              initialdir='.'),)
        
        # If no file was selected, exit the function
        if str(file_path) == '.':
            return
        
        # Determine file type and import data accordingly
        if file_path.suffix.lower() == '.mat':
            data = import_mat(file_path)
        elif file_path.suffix.lower() in ['.dat', '.txt']:
            data = import_dat(file_path)
        else:
            logger.error("Unsupported file type selected.")
            return

        # Add the imported dataset to the DataManager
        dm.add_dataset(name,data)
        logger.info(f"Data imported from {file_path.name}: {data}")

import_button = pn.widgets.Button(name='Import Data', button_type='primary')
pn.bind(callback.import_data, import_button, watch=True)

# Define the main application template
template = pn.template.FastGridTemplate(
    title='GripLab',
    sidebar=[import_button],
    sidebar_width=300,
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
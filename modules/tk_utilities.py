from tkinter import Tk, filedialog
from logger_setup import logger

class Tk_utils:
    def select_file(filetypes,initialdir,icon=''):
        try:
            root = Tk()
            root.iconbitmap(icon)
            root.withdraw()  # Hide the root window
            root.call('wm', 'attributes', '.', '-topmost', True)  # Bring the dialog to the front
            file_path = filedialog.askopenfilename(
                title="Select Data File(s)",
                initialdir=initialdir,
                filetypes=filetypes
            )
            root.destroy()  # Destroy the root window after use
            if file_path:
                logger.info(f"File(s) selected: {file_path}")
            else:
                logger.info("No file selected.")
            return file_path
        except Exception as e:
            logger.error(f"Error selecting file: {e}")

    def select_dir(initialdir,icon=''):
        try:
            root = Tk()
            root.iconbitmap(icon)
            root.withdraw()  # Hide the root window
            root.call('wm', 'attributes', '.', '-topmost', True)  # Bring the dialog to the front
            dir_path = filedialog.askdirectory(
                title="Select Directory",
                initialdir=initialdir
            )
            root.destroy()  # Destroy the root window after use
            if dir_path:
                logger.info(f"Directory selected: {dir_path}")
            else:
                logger.info("No directory selected.")
            return dir_path
        except Exception as e:
            logger.error(f"Error selecting directory: {e}")

    def save_file(defaultextension,initialdir,icon=''):
        try:
            root = Tk()
            root.iconbitmap(icon)
            root.withdraw()  # Hide the root window
            root.call('wm', 'attributes', '.', '-topmost', True)  # Bring the dialog to the front
            file_path = filedialog.asksaveasfilename(
                title="Save File As",
                defaultextension=defaultextension,
                initialdir=initialdir
            )
            root.destroy()  # Destroy the root window after use
            if file_path:
                logger.info(f"File path to save: {file_path}")
            else:
                logger.info("Save operation cancelled.")
            return file_path
        except Exception as e:
            logger.error(f"Error saving file: {e}")
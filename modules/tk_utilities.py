from tkinter import Tk, filedialog
from logger_setup import logger

class Tk_utils:
    def select_file(filetypes,initialdir,icon=''):
        """
        Opens a file selection dialog for the user to choose a file.

        Args:
            filetypes (list of tuple): List of (label, pattern) tuples specifying allowed file types, e.g., [("Text files", "*.txt")].
            initialdir (str): The initial directory that the dialog opens in.
            icon (str, optional):  Path to the icon file for the dialog window. Defaults to ''.

        Returns:
            str: The path to the selected file, or an empty string if no file was selected.

        Logs:
            Logs the selected file path or a message if no file was selected.
            Logs an error message if an exception occurs during the selection process.
        """
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
        """
        Opens a directory selection dialog and returns the selected directory path.

        Args:
            initialdir (str): The initial directory that the dialog opens in.
            icon (str, optional): Path to the icon file for the dialog window. Defaults to ''.

        Returns:
            str: The path of the selected directory, or an empty string if no directory was selected.

        Logs:
            Logs the selected directory path or a message if no directory was selected.
            Logs an error message if an exception occurs during the selection process.
        """
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
        """
        Opens a file save dialog using Tkinter and returns the selected file path.

        Args:
            defaultextension (str): The default file extension to use in the save dialog (e.g., '.txt').
            initialdir (str): The initial directory that the dialog opens in.
            icon (str, optional): Path to the icon file for the Tkinter window. Defaults to ''.

        Returns:
            str: The file path selected by the user, or an empty string if the operation is cancelled.

        Logs:
            Logs the selected file path or cancellation, and logs errors if any occur during the process.
        """
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
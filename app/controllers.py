# app/controllers.py
"""Business logic controllers for GripLab application."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import plotly.express as px

import core.dataio as IO
from utils.logger import logger
from core.plotting import PlottingUtils


class DataController:
    """Controller for data management operations."""
    
    def __init__(self, data_manager: IO.DataManager, config):
        self.dm = data_manager
        self.config = config
        self.import_counter = 0
        
    def import_data(self, file_paths: List[str]) -> List[str]:
        """Import data files and return list of imported dataset names."""
        imported_names = []
        
        for file_path in file_paths:
            path = Path(file_path)
            if str(path) == ".":
                continue
                
            name = self._generate_unique_name(path.stem)
            demo_name = self._generate_unique_demo_name()
            color = self._get_next_color()
            
            # Import based on file type
            try:
                if path.suffix.lower() == ".mat":
                    dataset = IO.import_mat(path, name, color, demo_name)
                elif path.suffix.lower() in [".dat", ".txt"]:
                    dataset = IO.import_dat(path, name, color, demo_name)
                else:
                    logger.error(f"Unsupported file type: {path.suffix}")
                    continue
                
                self.dm.add_dataset(name, dataset)
                imported_names.append(name)
                self.import_counter += 1
                logger.info(f"Imported dataset: {dataset}")
                
            except Exception as e:
                logger.error(f"Failed to import {path}: {e}", exc_info=True)
        
        return imported_names
    
    def remove_dataset(self, name: str) -> bool:
        """Remove a dataset from the manager."""
        try:
            self.dm.remove_dataset(name)
            logger.info(f"Removed dataset: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove dataset {name}: {e}", exc_info=True)
            return False
    
    def update_dataset_info(self, dataset_name: str, updates: Dict[str, Any], is_demo: bool = False) -> bool:
        """Update dataset information."""
        try:
            if is_demo:
                # Handle demo mode updates
                idx = self.dm.list_demo_names().index(dataset_name)
                name = self.dm.list_datasets()[idx]
                dataset = self.dm.get_dataset(name)
                original_name = dataset.demo_name
                
                # Update demo attributes
                for key, value in updates.items():
                    if hasattr(dataset, f"demo_{key}"):
                        setattr(dataset, f"demo_{key}", value)
                    else:
                        setattr(dataset, key, value)
                
                if 'name' in updates:
                    self.dm.update_demo_name(original_name, updates['name'])
            else:
                # Handle regular mode updates
                dataset = self.dm.get_dataset(dataset_name)
                original_name = dataset.name
                
                # Update attributes
                for key, value in updates.items():
                    setattr(dataset, key, value)
                
                if 'name' in updates and updates['name'] != original_name:
                    self.dm.update_dataset(original_name, updates['name'])
            
            logger.info(f"Updated dataset: {dataset_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update dataset {dataset_name}: {e}", exc_info=True)
            return False
    
    def get_dataset_info(self, dataset_name: str, is_demo: bool = False) -> Optional[Dict[str, Any]]:
        """Get dataset information."""
        try:
            if is_demo:
                idx = self.dm.list_demo_names().index(dataset_name)
                name = self.dm.list_datasets()[idx]
                dataset = self.dm.get_dataset(name)
                
                return {
                    'name': dataset.demo_name,
                    'tire_id': dataset.demo_tire_id,
                    'rim_width': dataset.demo_rim_width,
                    'notes': dataset.demo_notes,
                    'node_color': dataset.node_color
                }
            else:
                dataset = self.dm.get_dataset(dataset_name)
                
                return {
                    'name': dataset.name,
                    'tire_id': dataset.tire_id,
                    'rim_width': dataset.rim_width,
                    'notes': dataset.notes,
                    'node_color': dataset.node_color
                }
        except Exception as e:
            logger.error(f"Failed to get dataset info for {dataset_name}: {e}", exc_info=True)
            return None
    
    def _generate_unique_name(self, base_name: str) -> str:
        """Generate a unique dataset name."""
        name = base_name
        counter = 0
        while name in self.dm.list_datasets():
            counter += 1
            name = f"{base_name} ({counter})"
        return name
    
    def _generate_unique_demo_name(self) -> str:
        """Generate a unique demo dataset name."""
        base = "Demo data"
        name = base
        counter = 0
        while name in self.dm.list_demo_names():
            counter += 1
            name = f"{base} ({counter})"
        return name
    
    def _get_next_color(self) -> str:
        """Get the next color from the configured colorway."""
        colorway = px.colors.qualitative.__getattribute__(self.config.colorway)
        return colorway[self.import_counter % len(colorway)]


class PlotController:
    """Controller for plotting operations."""
    
    def __init__(self, data_manager: IO.DataManager, config):
        self.dm = data_manager
        self.config = config
    
    def create_plot(self, plot_params: Dict[str, Any]) -> tuple:
        """Create a plot based on the provided parameters."""
        try:
            fig, node_count = PlottingUtils.plot_data(
                plot_params['data_table'],
                self.dm,
                plot_params['x_select'],
                plot_params['y_select'],
                plot_params['z_select'],
                plot_params['color_select'],
                plot_params['unit_select'],
                plot_params['sign_select'],
                plot_params['plot_radio_group'],
                plot_params['color_map'],
                plot_params['downsample_slider'],
                plot_params['cmd_select_1'],
                plot_params['cmd_select_2'],
                plot_params['cmd_select_3'],
                plot_params['cmd_select_4'],
                plot_params['cmd_multi_select_1'],
                plot_params['cmd_multi_select_2'],
                plot_params['cmd_multi_select_3'],
                plot_params['cmd_multi_select_4'],
                plot_params['axis_visibility'],
                plot_params.get('title_text', ''),
                plot_params.get('subtitle_text', ''),
                plot_params.get('x_label_text', ''),
                plot_params.get('y_label_text', ''),
                plot_params.get('z_label_text', ''),
                plot_params.get('c_label_text', ''),
                plot_params.get('font_size', 18),
                plot_params.get('marker_size', 10)
            )
            return fig, node_count
        except Exception as e:
            logger.error(f"Error creating plot: {e}", exc_info=True)
            return None, 0
    
    def get_plot_parameters(self, widgets, config) -> Dict[str, Any]:
        """Collect plot parameters from widgets."""
        return {
            'data_table': widgets['data_table'],
            'x_select': widgets['plot_controls'].x_axis,
            'y_select': widgets['plot_controls'].y_axis,
            'z_select': widgets['plot_controls'].z_axis,
            'color_select': widgets['plot_controls'].color_axis,
            'unit_select': widgets['settings'].unit_select,
            'sign_select': widgets['settings'].sign_select,
            'plot_radio_group': widgets['plot_controls'].plot_type,
            'color_map': widgets['plot_settings'].color_map,
            'downsample_slider': widgets['plot_controls'].downsample_slider,
            'cmd_select_1': widgets['plot_controls'].cmd_selects[0],
            'cmd_select_2': widgets['plot_controls'].cmd_selects[1],
            'cmd_select_3': widgets['plot_controls'].cmd_selects[2],
            'cmd_select_4': widgets['plot_controls'].cmd_selects[3],
            'cmd_multi_select_1': widgets['plot_controls'].cmd_multi_selects[0],
            'cmd_multi_select_2': widgets['plot_controls'].cmd_multi_selects[1],
            'cmd_multi_select_3': widgets['plot_controls'].cmd_multi_selects[2],
            'cmd_multi_select_4': widgets['plot_controls'].cmd_multi_selects[3],
            'axis_visibility': config.demo_mode,
            'title_text': widgets['plot_settings'].title.value,
            'subtitle_text': widgets['plot_settings'].subtitle.value,
            'x_label_text': widgets['plot_settings'].x_label.value,
            'y_label_text': widgets['plot_settings'].y_label.value,
            'z_label_text': widgets['plot_settings'].z_label.value,
            'c_label_text': widgets['plot_settings'].c_label.value,
            'font_size': widgets['plot_settings'].font_size.value,
            'marker_size': widgets['plot_settings'].marker_size.value
        }
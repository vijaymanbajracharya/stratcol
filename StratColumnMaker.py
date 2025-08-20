import json
import sys
import pdb
import StratColumn as sc
import os

from Lithology import RockCategory, RockProperties, RockType
from Deposition import DepositionalEnvironment
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLineEdit, QLabel, QComboBox, QSpinBox, 
                               QTableWidget, QTableWidgetItem, QColorDialog, QMessageBox,
                               QDoubleSpinBox, QCheckBox, QToolBar, QToolButton, QMenu, QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QAction
from functools import partial
from app import ScalingMode
from Layer import Layer

DEFAULT_THICKNESS = 1000
DEFAULT_YOUNG_AGE = 0.0
DEFAULT_OLD_AGE = 4567.0
DEFAULT_FORMATION_TOP = 0

def populate_rock_type_combo(combo_box):
    """Populate QComboBox with rock types grouped by category"""
    combo_box.clear()
    
    # # Add items grouped by category
    # for category in RockCategory:
    #     if category == RockCategory.OTHER:
    #         continue
        
    #     # Add rocks in this category
    #     rocks = RockProperties.get_rocks_by_category(category)
    #     for rock in sorted(rocks, key=lambda x: x.value):
    #         display_name = RockProperties.get_display_name(rock)
    #         combo_box.addItem(display_name)
    #         combo_box.setItemData(combo_box.count() - 1, rock)
    
    # other_rocks = RockProperties.get_rocks_by_category(RockCategory.OTHER)
    # for rock in sorted(other_rocks, key=lambda x: x.value):
    #     display_name = RockProperties.get_display_name(rock)
    #     combo_box.addItem(display_name)
    #     combo_box.setItemData(combo_box.count() - 1, rock)

    rocks = RockProperties.get_rocks_by_alphabetic_order()
    for rock in rocks:
        display_name = RockProperties.get_display_name(rock)
        combo_box.addItem(display_name)
        combo_box.setItemData(combo_box.count() - 1, rock)

def populate_dep_env_combo(combo_box):
    """Populate QComboBox with depositional environments"""
    combo_box.clear()

    # Sort by display_name alphabetically
    for env in sorted(DepositionalEnvironment, key=lambda e: e.display_name):
        combo_box.addItem(env.display_name)
        combo_box.setItemData(combo_box.count() - 1, env)

class StratColumnMaker(QMainWindow):
    display_options_changed = Signal(dict)
    show_uncomformity_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stratigraphic Column Maker")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create toolbar
        self.create_toolbar()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QHBoxLayout(central_widget)

        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel, 1)

        # Stratigraphic column
        self.strat_column = sc.StratColumn()
        layout.addWidget(self.strat_column, 2)

        # Activate toolbar
        self.toolbar.setEnabled(True)
        
    
    def create_toolbar(self):
        """Create the main toolbar with dropdown menus"""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setEnabled(False)
        self.addToolBar(self.toolbar)

        # File menu dropdown
        file_button = QToolButton()
        file_button.setText("File")
        file_button.setPopupMode(QToolButton.InstantPopup)
        
        file_menu = QMenu(self)
        
        new_action = QAction("New Column", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_column)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_column)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_column)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_as_column)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export Image...", self)
        export_action.triggered.connect(self.export_image)
        file_menu.addAction(export_action)

        file_button.setMenu(file_menu)
        self.toolbar.addWidget(file_button)

        # View
        view_button = QToolButton()
        view_button.setEnabled(False)
        view_button.setText("View")
        view_button.setPopupMode(QToolButton.InstantPopup)
        
        view_menu = QMenu(self)

        sort_action = QAction("Sort By", self)
        sort_action.triggered.connect(self.sort_column)
        view_menu.addAction(sort_action)
        
        show_action = QAction("Show Layers", self)
        show_action.triggered.connect(self.show_column)
        view_menu.addAction(show_action)
        
        view_button.setMenu(view_menu)
        self.toolbar.addWidget(view_button)

        # Help
        help_button = QToolButton()
        help_button.setEnabled(False)
        help_button.setText("Help")
        help_button.setPopupMode(QToolButton.InstantPopup)
        
        help_menu = QMenu(self)
        
        help_button.setMenu(help_menu)
        self.toolbar.addWidget(help_button)

    def sort_column(self):
        pass

    def show_column(self):
        pass
    
    def new_column(self):
        for _ in range(0, len(self.strat_column.layers)):
            self.strat_column.remove_layer(len(self.strat_column.layers) - 1)
        
        self.update_layer_table()

    def open_column(self):
        """Open a column file, clearing current layers and updating file path"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Stratigraphic Column",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return  # User cancelled the dialog
        
        try:
            # Load the file data
            with open(file_path, "r", encoding='utf-8') as f:
                data = json.load(f)

            # Extract layers and metadata separately
            layers_data = data.get("layers", [])
            metadata = data.get("metadata", {})

            # Clear all current layers before adding new ones
            for _ in range(len(self.strat_column.layers)):
                self.strat_column.remove_layer(len(self.strat_column.layers) - 1)

            # Convert each dict into a Layer and add to column
            layers = [Layer.from_dict(layer_dict) for layer_dict in layers_data]
            
            for layer in layers:
                self.strat_column.add_layer(layer)

            # Update the layer table display
            self.update_layer_table()

            # Update the current file path to the opened file
            self.current_file_path = file_path

            # Reset input fields to defaults
            self.name_input.clear()
            self.thickness_input.setValue(DEFAULT_THICKNESS)
            self.formation_top_input.setValue(self.strat_column.max_depth)
            self.young_age_input.setValue(DEFAULT_YOUNG_AGE)
            self.old_age_input.setValue(DEFAULT_OLD_AGE)
            
            # Show success message
            QMessageBox.information(
                self,
                "Open Successful",
                f"Stratigraphic column loaded from:\n{os.path.abspath(file_path)}\n\nLoaded {len(layers)} layers."
            )
            
        except FileNotFoundError:
            QMessageBox.critical(
                self,
                "Open Error",
                f"File not found:\n{file_path}"
            )
        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self,
                "Open Error",
                f"Invalid JSON file format:\n{str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Open Error",
                f"Failed to open stratigraphic column:\n{str(e)}"
            )
        

    def save_column(self):
        """Save the current column - uses Save As if no file exists, otherwise overwrites"""
        # Check if we have a previously saved file path
        if not hasattr(self, 'current_file_path') or not self.current_file_path:
            # No previous save location, so call Save As
            self.save_as_column()
            return
        
        try:
            # We have a previous save location, so overwrite it
            # Collect all layer data
            column_data = {
                "layers": [],
                "metadata": {
                    "version": "1.0",
                    "created_with": "Stratigraphic Column Maker",
                    "total_layers": len(self.strat_column.layers)
                }
            }
            
            # Convert each layer to dictionary format
            for layer in self.strat_column.layers:
                layer_dict = layer.to_dict()
                column_data["layers"].append(layer_dict)
            
            # Save to the existing file path
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                json.dump(column_data, f, indent=2, ensure_ascii=False)
            
            # Show success message
            QMessageBox.information(
                self, 
                "Save Successful", 
                f"Stratigraphic column saved to:\n{os.path.abspath(self.current_file_path)}"
            )
            
        except Exception as e:
            # Handle any errors that occur during saving
            QMessageBox.critical(
                self, 
                "Save Error", 
                f"Failed to save stratigraphic column:\n{str(e)}"
            )

    def save_as_column(self):
        """Save the current column to a user-selected location"""
        try:
            # Get the save file path from user
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Stratigraphic Column As...",
                os.path.expanduser("~/strat_column.json"),  # Default filename in home directory
                "JSON files (*.json);;All files (*.*)"
            )
            
            # If user cancelled the dialog
            if not file_path:
                return
            
            # Ensure the file has a .json extension if none provided
            if not file_path.lower().endswith('.json'):
                file_path += '.json'
            
            # Collect all layer data
            column_data = {
                "layers": [],
                "metadata": {
                    "version": "1.0",
                    "created_with": "Stratigraphic Column Maker",
                    "total_layers": len(self.strat_column.layers)
                }
            }
            
            # Convert each layer to dictionary format
            for layer in self.strat_column.layers:
                layer_dict = layer.to_dict()
                column_data["layers"].append(layer_dict)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save to JSON file with proper formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(column_data, f, indent=2, ensure_ascii=False)
            
            # Show success message
            QMessageBox.information(
                self, 
                "Save Successful", 
                f"Stratigraphic column saved successfully to:\n{os.path.abspath(file_path)}"
            )
            
            # Optional: Store the current file path for future save operations
            self.current_file_path = file_path
            
        except Exception as e:
            # Handle any errors that occur during saving
            QMessageBox.critical(
                self, 
                "Save Error", 
                f"Failed to save stratigraphic column:\n{str(e)}"
            )

    def export_image(self):
        """Export column as image using file dialog"""
        try:
            # Create the pixmap from the widget
            pixmap = self.strat_column.grab()
            
            # Open file dialog to choose save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Stratigraphic Column",
                "strat_column.png",  # Default filename
                "PNG files (*.png);;All files (*.*)"
            )
            
            # Check if user canceled the dialog
            if not file_path:
                return
            
            # Ensure the file has .png extension
            if not file_path.lower().endswith('.png'):
                file_path += '.png'
            
            # Save the pixmap
            success = pixmap.save(file_path, "PNG")
            
            if success:
                # Show success message with full path
                abs_path = os.path.abspath(file_path)
                QMessageBox.information(self, "Save Successful", 
                                    f"Stratigraphic column saved to:\n{abs_path}")
            else:
                QMessageBox.warning(self, "Save Warning", 
                                "File may not have been saved properly.")
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error", 
                                f"Failed to save file:\n{str(e)}")

    def validate_start(self, start_value):
        end_value = self.old_age_input.value()
        if start_value >= end_value:
            self.old_age_input.setValue(round(start_value + 0.1, 1))
        self.old_age_input.setMinimum(round(start_value + 0.1, 1))

    def validate_end(self, end_value):
        start_value = self.young_age_input.value()
        if end_value <= start_value:
            self.young_age_input.setValue(round(end_value - 0.1, 1))
        self.young_age_input.setMaximum(round(end_value - 0.1, 1))
    
    def create_control_panel(self):
        """Create the control panel with input fields and buttons"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        form_layout = QHBoxLayout()
        
        # Layer input section
        layout.addWidget(QLabel("Add New Layer:"))
        
        # Layer name
        layout.addWidget(QLabel("Formation Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Barren Measures")
        layout.addWidget(self.name_input)
        
        # Rock type
        layout.addWidget(QLabel("Rock Type:"))
        self.rock_type_combo = QComboBox()
        populate_rock_type_combo(self.rock_type_combo)
        layout.addWidget(self.rock_type_combo)

        # Depositional Environment
        layout.addWidget(QLabel("Depositional Environment:"))
        self.dep_env_combo = QComboBox()
        populate_dep_env_combo(self.dep_env_combo)
        layout.addWidget(self.dep_env_combo)
        
        # Thickness
        layout.addWidget(QLabel("Thickness (m):"))
        self.thickness_input = QSpinBox()
        self.thickness_input.setRange(1, 10000)
        self.thickness_input.setValue(DEFAULT_THICKNESS)
        layout.addWidget(self.thickness_input)

        # Formation Top
        layout.addWidget(QLabel("Formation Top (m):"))
        self.formation_top_input = QSpinBox()
        self.formation_top_input.setRange(0, 999999)
        self.formation_top_input.setValue(DEFAULT_FORMATION_TOP)
        layout.addWidget(self.formation_top_input)

        # Stratigraphic Age
        form_layout.addWidget(QLabel("Youngest Stratigraphic Age (Ma):"))

        self.young_age_input = QDoubleSpinBox()
        self.young_age_input.setDecimals(1)
        self.young_age_input.setRange(0.0, DEFAULT_OLD_AGE)
        self.young_age_input.setSingleStep(0.1)
        self.young_age_input.setValue(DEFAULT_YOUNG_AGE)

        form_layout.addWidget(self.young_age_input)

        form_layout.addWidget(QLabel("Oldest Stratigraphic Age (Ma):"))
        self.old_age_input = QDoubleSpinBox()
        self.old_age_input.setDecimals(1)
        self.old_age_input.setRange(0.0, DEFAULT_OLD_AGE)
        self.old_age_input.setSingleStep(0.1)
        self.old_age_input.setValue(DEFAULT_OLD_AGE)
        
        form_layout.addWidget(self.old_age_input)

        layout.addLayout(form_layout)

        self.young_age_input.valueChanged.connect(self.validate_start)
        self.old_age_input.valueChanged.connect(self.validate_end)

        # Eras, Periods, Epochs, Ages
        layout.addWidget(QLabel("Display Options:"))
        checkbox_layout = QHBoxLayout()
        
        self.checkbox_eras = QCheckBox("Show Eras")
        self.checkbox_periods = QCheckBox("Show Periods") 
        self.checkbox_epochs = QCheckBox("Show Epochs")
        self.checkbox_ages = QCheckBox("Show Ages")

        # Default state
        self.checkbox_eras.setChecked(False)
        self.checkbox_periods.setChecked(False)
        self.checkbox_epochs.setChecked(True)
        self.checkbox_ages.setChecked(True)

        # Connect to update method that will trigger repaints
        self.checkbox_eras.stateChanged.connect(self.on_chrono_checkbox_changed)
        self.checkbox_periods.stateChanged.connect(self.on_chrono_checkbox_changed)
        self.checkbox_epochs.stateChanged.connect(self.on_chrono_checkbox_changed)
        self.checkbox_ages.stateChanged.connect(self.on_chrono_checkbox_changed)
        
        checkbox_layout.addWidget(self.checkbox_eras)
        checkbox_layout.addWidget(self.checkbox_periods)
        checkbox_layout.addWidget(self.checkbox_epochs)
        checkbox_layout.addWidget(self.checkbox_ages)

        layout.addLayout(checkbox_layout)

        # Scaling mode layout
        # Plot by formation top, thickness, time
        scaling_mode_layout = QHBoxLayout()
        scaling_mode_layout.setSpacing(0)
        scaling_mode_layout.addWidget(QLabel("Sort stratigraphic column by:"))
        self.scaling_mode_combo_box = QComboBox()

        for mode in ScalingMode:
            self.scaling_mode_combo_box.addItem(str(mode.value))
            self.scaling_mode_combo_box.setItemData(self.scaling_mode_combo_box.count() - 1, mode)
        
        self.scaling_mode_combo_box.currentTextChanged.connect(self.on_scaling_mode_changed)
        
        scaling_mode_layout.addWidget(self.scaling_mode_combo_box)
        layout.addLayout(scaling_mode_layout)

        # Uncomformity mode
        uncomformity_layout = QHBoxLayout()
        uncomformity_label = QLabel("Show uncomformity")
        self.checkbox_uncomformity = QCheckBox()
        self.checkbox_uncomformity.setChecked(True)
        self.checkbox_uncomformity.stateChanged.connect(self.on_uncomformity_checkbox_changed)

        uncomformity_layout.addWidget(uncomformity_label)
        uncomformity_layout.addWidget(self.checkbox_uncomformity)
        uncomformity_layout.addStretch()  # Pushes content to the left

        layout.addLayout(uncomformity_layout)

        # Add layer button
        add_button = QPushButton("Add Layer")
        add_button.clicked.connect(self.add_layer)
        layout.addWidget(add_button)
        
        layout.addWidget(QLabel(""))  # Spacer
        
        # Layer list
        layout.addWidget(QLabel("Current Layers:"))
        self.layer_table = QTableWidget()
        self.layer_table.setColumnCount(4)
        self.layer_table.setHorizontalHeaderLabels(["Name", "Thickness", "Type", "Action"])
        layout.addWidget(self.layer_table)
        
        return panel
    
    def add_layer(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter a layer name")
            return
        
        selected_rock = self.rock_type_combo.currentData()
        if isinstance(selected_rock, RockType):
            pattern = RockProperties.get_pattern(selected_rock)
        
        thickness = self.thickness_input.value()
        formation_top = self.formation_top_input.value()
        young_age = self.young_age_input.value()
        old_age = self.old_age_input.value()
        
        selected_dep_env = self.dep_env_combo.currentData()

        layer = Layer(name, thickness, selected_rock, formation_top, young_age, old_age, selected_dep_env)
        
        self.strat_column.add_layer(layer)
        self.update_layer_table()

        self.name_input.clear()
        self.thickness_input.setValue(DEFAULT_THICKNESS)
        self.formation_top_input.setValue(self.strat_column.max_depth)
        self.young_age_input.setValue(DEFAULT_YOUNG_AGE)
        self.old_age_input.setValue(DEFAULT_OLD_AGE)

    def get_chrono_display_options(self):
        """Return the current state of all checkboxes as a dictionary"""
        return {
            'show_eras': self.checkbox_eras.isChecked(),
            'show_periods': self.checkbox_periods.isChecked(),
            'show_epochs': self.checkbox_epochs.isChecked(),
            'show_ages': self.checkbox_ages.isChecked()
        }
    
    def on_chrono_checkbox_changed(self):
        """Called when chrono checkbox state changes"""
        options = self.get_chrono_display_options()
        self.display_options_changed.emit(options)

    def on_uncomformity_checkbox_changed(self):
        """Called when uncomformity checkbox state chages"""
        self.show_uncomformity_changed.emit(self.checkbox_uncomformity.isChecked())

    def on_scaling_mode_changed(self, value):
        """Handle scaling mode change"""       
        # Get the selected ScalingMode enum
        current_mode = self.scaling_mode_combo_box.currentData()
        self.strat_column.update_scaling_mode(current_mode)

    def update_layer_table(self):
        self.layer_table.setRowCount(len(self.strat_column.layers))
        
        for i, layer in enumerate(self.strat_column.layers):
            self.layer_table.setItem(i, 0, QTableWidgetItem(layer.name))
            self.layer_table.setItem(i, 1, QTableWidgetItem(f"{layer.thickness}m"))
            self.layer_table.setItem(i, 2, QTableWidgetItem(layer.rock_type_display_name))
            
            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(partial(self.remove_layer, i))
            self.layer_table.setCellWidget(i, 3, remove_btn)
    
    def remove_layer(self, index):
        """Remove a layer from the column"""
        self.strat_column.remove_layer(index)
        self.update_layer_table()
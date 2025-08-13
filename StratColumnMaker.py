import json
import sys
import pdb
import StratColumn as sc
import Layer
import os

from Lithology import RockCategory, RockProperties, RockType
from Deposition import DepositionalEnvironment
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLineEdit, QLabel, QComboBox, QSpinBox, 
                               QTableWidget, QTableWidgetItem, QColorDialog, QMessageBox,
                               QDoubleSpinBox, QCheckBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from functools import partial
from app import ScalingMode

DEFAULT_THICKNESS = 1000
DEFAULT_YOUNG_AGE = 0.0
DEFAULT_OLD_AGE = 4567.0
DEFAULT_FORMATION_TOP = 0

def populate_rock_type_combo(combo_box):
    """Populate QComboBox with rock types grouped by category"""
    combo_box.clear()
    
    # Add items grouped by category
    for category in RockCategory:
        if category == RockCategory.OTHER:
            continue
        
        # Add rocks in this category
        rocks = RockProperties.get_rocks_by_category(category)
        for rock in sorted(rocks, key=lambda x: x.value):
            display_name = RockProperties.get_display_name(rock)
            combo_box.addItem(display_name)
            combo_box.setItemData(combo_box.count() - 1, rock)
    
    other_rocks = RockProperties.get_rocks_by_category(RockCategory.OTHER)
    for rock in sorted(other_rocks, key=lambda x: x.value):
        display_name = RockProperties.get_display_name(rock)
        combo_box.addItem(display_name)
        combo_box.setItemData(combo_box.count() - 1, rock)

def populate_dep_env_combo(combo_box):
    """Populate QComboBox with depositional environments"""
    combo_box.clear()

    # Add items from json
    for env in DepositionalEnvironment:
        combo_box.addItem(env.display_name)
        combo_box.setItemData(combo_box.count() - 1, env)

class StratColumnMaker(QMainWindow):
    display_options_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stratigraphic Column Maker")
        self.setGeometry(100, 100, 1200, 800)
        
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
        self.checkbox_eras.stateChanged.connect(self.on_checkbox_changed)
        self.checkbox_periods.stateChanged.connect(self.on_checkbox_changed)
        self.checkbox_epochs.stateChanged.connect(self.on_checkbox_changed)
        self.checkbox_ages.stateChanged.connect(self.on_checkbox_changed)
        
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
        
        # File operations
        save_button = QPushButton("Save Column")
        save_button.clicked.connect(self.save_column)
        layout.addWidget(save_button)
        
        load_button = QPushButton("Load Column")
        load_button.clicked.connect(self.load_column)
        layout.addWidget(load_button)
        
        clear_button = QPushButton("Clear All")
        clear_button.clicked.connect(self.clear_all)
        layout.addWidget(clear_button)
        
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

        layer = Layer.Layer(name, thickness, selected_rock, formation_top, young_age, old_age, selected_dep_env)
        
        self.strat_column.add_layer(layer)
        self.update_layer_table()

        self.name_input.clear()
        self.thickness_input.setValue(DEFAULT_THICKNESS)
        self.formation_top_input.setValue(self.strat_column.max_depth)
        self.young_age_input.setValue(DEFAULT_YOUNG_AGE)
        self.old_age_input.setValue(DEFAULT_OLD_AGE)

    def get_display_options(self):
        """Return the current state of all checkboxes as a dictionary"""
        return {
            'show_eras': self.checkbox_eras.isChecked(),
            'show_periods': self.checkbox_periods.isChecked(),
            'show_epochs': self.checkbox_epochs.isChecked(),
            'show_ages': self.checkbox_ages.isChecked()
        }
    
    def on_checkbox_changed(self):
        """Called when any checkbox state changes"""
        options = self.get_display_options()
        self.display_options_changed.emit(options)

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
    
    def save_column(self):
        pixmap = self.strat_column.grab()
    
        # Save as PNG
        os.makedirs("output", exist_ok=True)
        pixmap.save("output\\strat_column.png", "PNG")
    
    def load_column(self):
        pass
    
    def clear_all(self):
        pass
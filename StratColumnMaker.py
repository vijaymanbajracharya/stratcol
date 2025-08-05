import json
import sys
import pdb
import StratColumn as sc
import Layer

from Lithology import RockCategory, RockProperties, RockType
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLineEdit, QLabel, QComboBox, QSpinBox, 
                               QTableWidget, QTableWidgetItem, QColorDialog, QMessageBox,
                               QDoubleSpinBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from functools import partial

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

class StratColumnMaker(QMainWindow):
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
        
        # Color selection
        self.color_button = QPushButton("Select Color")
        self.color_button.clicked.connect(self.select_color)
        self.selected_color = QColor(200, 200, 200)
        self.update_color_button()
        layout.addWidget(self.color_button)
        
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
        
    def update_color_button(self):
        """Update the color button to show selected color"""
        self.color_button.setStyleSheet(
            f"background-color: {self.selected_color.name()}; "
            f"color: {'white' if self.selected_color.lightness() < 128 else 'black'};"
        )
    
    def select_color(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor(self.selected_color, self)
        if color.isValid():
            self.selected_color = color
            self.update_color_button()
    
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

        layer = Layer.Layer(name, thickness, selected_rock, formation_top, young_age, old_age)
        
        self.strat_column.add_layer(layer)
        self.update_layer_table()

        self.name_input.clear()
        self.thickness_input.setValue(DEFAULT_THICKNESS)
        self.formation_top_input.setValue(DEFAULT_FORMATION_TOP)
        self.young_age_input.setValue(DEFAULT_YOUNG_AGE)
        self.old_age_input.setValue(DEFAULT_OLD_AGE)

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
    
    def add_example_layers(self):
        pass
    
    def save_column(self):
        pass
    
    def load_column(self):
        pass
    
    def clear_all(self):
        pass
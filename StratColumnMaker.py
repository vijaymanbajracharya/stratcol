import json
import StratColumn as sc

from Lithology import RockCategory, RockProperties
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem, QColorDialog, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

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
        self.setGeometry(100, 100, 800, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QHBoxLayout(central_widget)

        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel, 1)
    
    def create_control_panel(self):
        """Create the control panel with input fields and buttons"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
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
        self.thickness_input.setRange(1, 1000)
        self.thickness_input.setValue(10)
        layout.addWidget(self.thickness_input)
        
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
        self.layer_table.setHorizontalHeaderLabels(["Name", "Type", "Thickness", "Action"])
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
        pass

    def update_layer_table(self):
        pass
    
    def remove_layer(self, index):
        pass
    
    def add_example_layers(self):
        pass
    
    def save_column(self):
        pass
    
    def load_column(self):
        pass
    
    def clear_all(self):
        pass
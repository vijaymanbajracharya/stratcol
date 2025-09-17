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
                               QDoubleSpinBox, QCheckBox, QToolBar, QToolButton, QMenu, QFileDialog, QSpacerItem, QSizePolicy, QWidget, QDialog,
                               QDialogButtonBox)
from PySide6.QtCore import Qt, Signal, QPoint, QSize
from PySide6.QtGui import QAction, QPainter, QPixmap, QRegion
from PySide6.QtSvg import QSvgGenerator
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

class LayerEditDialog(QDialog):
    def __init__(self, layer, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Layer")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.layer = layer
        self.setup_ui()

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
    
    def accept(self):
        """Override accept to update layer with new values before closing"""
        # Update layer properties with values from input fields
        self.layer.name = self.name_input.text().strip()
        
        # Update rock type
        selected_rock = self.rock_type_combo.currentData()
        if isinstance(selected_rock, RockType):
            self.layer.rock_type = selected_rock
        
        # Update depositional environment
        selected_dep_env = self.dep_env_combo.currentData()
        if isinstance(selected_dep_env, DepositionalEnvironment):
            self.layer.dep_env = selected_dep_env
        
        # Update thickness
        self.layer.thickness = self.thickness_input.value()
        
        # Update min/max thickness
        if self.min_thickness_input.isEnabled():
            self.layer.min_thickness = self.min_thickness_input.value()
        else:
            self.layer.min_thickness = None
            
        if self.max_thickness_input.isEnabled():
            self.layer.max_thickness = self.max_thickness_input.value()
        else:
            self.layer.max_thickness = None
        
        # Update formation top
        if self.formation_top_input.isEnabled():
            self.layer.formation_top = self.formation_top_input.value()
        else:
            self.layer.formation_top = None
        
        # Update ages
        self.layer.young_age = self.young_age_input.value()
        self.layer.old_age = self.old_age_input.value()
        
        # Validate that we have a layer name
        if not self.layer.name:
            QMessageBox.warning(self, "Warning", "Please enter a layer name")
            return
        
        # Call parent accept to close dialog
        super().accept()
    
    def reject(self):
        return super().reject()
            
        
    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)
        form_layout = QHBoxLayout()
        thickness_range_layout = QHBoxLayout()
        
        # Layer name
        layout.addWidget(QLabel("Formation Name:"))
        self.name_input = QLineEdit()
        self.name_input.setText(self.layer.name)
        layout.addWidget(self.name_input)
        
        # Rock type
        layout.addWidget(QLabel("Rock Type:"))
        self.rock_type_combo = QComboBox()
        populate_rock_type_combo(self.rock_type_combo)
        self.rock_type_combo.setCurrentText(RockProperties.get_display_name(self.layer.rock_type))
        layout.addWidget(self.rock_type_combo)

        # Depositional Environment
        layout.addWidget(QLabel("Depositional Environment:"))
        self.dep_env_combo = QComboBox()
        populate_dep_env_combo(self.dep_env_combo)
        self.dep_env_combo.setCurrentText(self.layer.dep_env.display_name)
        layout.addWidget(self.dep_env_combo)
        
        # Thickness
        layout.addWidget(QLabel("Thickness (m):"))
        self.thickness_input = QSpinBox()
        self.thickness_input.setStyleSheet("QSpinBox:disabled { color: transparent; }")
        self.thickness_input.setRange(1, 10000)
        self.thickness_input.setValue(self.layer.thickness)

        layout.addWidget(self.thickness_input)

        # Min max thickness
        thickness_range_layout.addWidget(QLabel("Minimum Thickness (m):"))
        
        self.min_thickness_input = QSpinBox()
        self.min_thickness_input.setStyleSheet("QSpinBox:disabled { color: transparent; }")
        self.min_thickness_input.setRange(1, 10000)
        self.min_thickness_input.setSingleStep(1)

        if self.layer.min_thickness is not None:
            self.min_thickness_input.setValue(self.layer.min_thickness)
        else:
            self.min_thickness_input.setEnabled(False)

        thickness_range_layout.addWidget(self.min_thickness_input)

        thickness_range_layout.addWidget(QLabel("Maximum Thickness (m):"))
        self.max_thickness_input = QSpinBox()
        self.max_thickness_input.setStyleSheet("QSpinBox:disabled { color: transparent; }")
        self.max_thickness_input.setRange(1, 10000)
        self.max_thickness_input.setSingleStep(1)

        if self.layer.max_thickness is not None:
            self.max_thickness_input.setValue(self.layer.max_thickness)
        else:
            self.max_thickness_input.setEnabled(False)
        
        thickness_range_layout.addWidget(self.max_thickness_input)

        layout.addLayout(thickness_range_layout)

        # Formation Top
        layout.addWidget(QLabel("Formation Top (m):"))
        self.formation_top_input = QSpinBox()
        self.formation_top_input.setStyleSheet("QSpinBox:disabled { color: transparent; }")
        self.formation_top_input.setRange(0, 999999)

        if self.layer.formation_top is not None:
            self.formation_top_input.setValue(self.layer.formation_top)
        else:
            self.formation_top_input.setEnabled(False)

        layout.addWidget(self.formation_top_input)

        # Stratigraphic Age
        form_layout.addWidget(QLabel("Youngest Stratigraphic Age (Ma):"))

        self.young_age_input = QDoubleSpinBox()
        self.young_age_input.setDecimals(1)
        self.young_age_input.setRange(0.0, DEFAULT_OLD_AGE)
        self.young_age_input.setSingleStep(0.1)
        self.young_age_input.setValue(self.layer.young_age)

        form_layout.addWidget(self.young_age_input)

        form_layout.addWidget(QLabel("Oldest Stratigraphic Age (Ma):"))
        self.old_age_input = QDoubleSpinBox()
        self.old_age_input.setDecimals(1)
        self.old_age_input.setRange(0.0, DEFAULT_OLD_AGE)
        self.old_age_input.setSingleStep(0.1)
        self.old_age_input.setValue(self.layer.old_age)
        
        form_layout.addWidget(self.old_age_input)

        layout.addLayout(form_layout)

        self.young_age_input.valueChanged.connect(self.validate_start)
        self.old_age_input.valueChanged.connect(self.validate_end)
        
        # Button box with Accept and Cancel
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)

class StratColumnMaker(QMainWindow):
    age_display_options_changed = Signal(dict)
    show_formation_gap_changed = Signal(bool)
    display_age_range_changed = Signal(float, float)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stratigraphic Column Maker")
        self.setGeometry(100, 100, 1200, 800)
        self.showMaximized()
        self.strat_column = None
        
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

        # Set default scaling mode
        default_scaling_mode = ScalingMode.CHRONOLOGY

        # Find the index of the item with the desired data
        for i in range(self.scaling_mode_combo_box.count()):
            if self.scaling_mode_combo_box.itemData(i) == default_scaling_mode:
                self.scaling_mode_combo_box.setCurrentIndex(i)
                break

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
            self.reset_input_fields()
            
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
                os.path.expanduser("~/strat_column.json"),
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
            
            self.current_file_path = file_path
            
        except Exception as e:
            # Handle any errors that occur during saving
            QMessageBox.critical(
                self, 
                "Save Error", 
                f"Failed to save stratigraphic column:\n{str(e)}"
            )

    def export_image(self):
        """Export column as high-resolution image with PNG and SVG options"""
        try:
            # Single file dialog with multiple format options
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "Export Stratigraphic Column",
                "strat_column",  # Default filename without extension
                "High-Resolution PNG (*.png);;Vector SVG (*.svg);;All files (*.*)"
            )
            
            if not file_path:
                return
            
            # Determine export format based on selected filter
            if "PNG" in selected_filter:
                # Ensure PNG extension
                if not file_path.lower().endswith('.png'):
                    file_path += '.png'
                self._export_high_res_png(file_path)
                
            elif "SVG" in selected_filter:
                # Ensure SVG extension
                if not file_path.lower().endswith('.svg'):
                    file_path += '.svg'
                self._export_vector_svg(file_path)
                
            else:
                # Handle "All files" - determine by file extension
                if file_path.lower().endswith('.svg'):
                    self._export_vector_svg(file_path)
                elif file_path.lower().endswith('.png'):
                    self._export_high_res_png(file_path)
                else:
                    # Default to PNG if no recognized extension
                    file_path += '.png'
                    self._export_high_res_png(file_path)
                    
        except Exception as e:
            QMessageBox.critical(self, "Export Error", 
                                f"Failed to export file:\n{str(e)}")

    def _export_high_res_png(self, file_path):
        """Export as high-resolution PNG with customizable DPI"""
        
        try:
            # Get DPI/scale factor from user
            scale_factor = 3.0
            
            # Get original widget size
            original_size = self.strat_column.size()
            
            # Calculate high-resolution dimensions
            high_res_width = int(original_size.width() * scale_factor)
            high_res_height = int(original_size.height() * scale_factor)
            high_res_size = QSize(high_res_width, high_res_height)
            
            # Create high-resolution pixmap
            pixmap = QPixmap(high_res_size)
            pixmap.fill()
            
            # Create painter for high-resolution rendering
            painter = QPainter(pixmap)
            
            # Enable high-quality rendering
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # Scale the painter for high-resolution output
            painter.scale(scale_factor, scale_factor)
            
            # Render the widget to the high-resolution pixmap
            self.strat_column.render(
                painter, 
                QPoint(), 
                self.strat_column.rect(),
                QWidget.RenderFlag.DrawWindowBackground | QWidget.RenderFlag.DrawChildren
            )
            
            painter.end()
            
            # Save the pixmap as PNG
            success = pixmap.save(file_path, "PNG", 95)
            
            if success:
                # Show success message with file info
                file_size = os.path.getsize(file_path)
                file_size_mb = file_size / (1024 * 1024)
                abs_path = os.path.abspath(file_path)
                
                QMessageBox.information(
                    self, 
                    "Export Successful", 
                    f"High-resolution PNG saved successfully!\n\n"
                    f"Path: {abs_path}\n"
                    f"Resolution: {high_res_width} × {high_res_height} pixels\n"
                    f"File size: {file_size_mb:.2f} MB"
                )
            else:
                QMessageBox.warning(
                    self, 
                    "Export Warning", 
                    "Failed to save PNG file. Please check file permissions and disk space."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Export Error", 
                f"Failed to export high-resolution PNG:\n{str(e)}"
            )
            raise

    def _export_vector_svg(self, file_path):
        """Export as scalable vector graphics (SVG)"""
        
        # Create SVG generator
        generator = QSvgGenerator()
        generator.setFileName(file_path)
        generator.setSize(self.strat_column.size())
        generator.setViewBox(self.strat_column.rect())
        generator.setTitle("Stratigraphic Column")
        generator.setDescription("Vector export of stratigraphic column")
        
        # Create painter and render
        painter = QPainter()
        if painter.begin(generator):
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            
            # Render the widget to SVG
            self.strat_column.render(painter, QPoint(), QRegion(), QWidget.RenderFlag.DrawWindowBackground | QWidget.RenderFlag.DrawChildren)
            painter.end()
            
            # Show success message
            abs_path = os.path.abspath(file_path)
            QMessageBox.information(self, "Export Successful", 
                                f"Vector SVG saved to:\n{abs_path}")
        else:
            QMessageBox.warning(self, "Export Warning", 
                            "Failed to initialize SVG painter.")

    def reset_input_fields(self):
        current_mode = self.scaling_mode_combo_box.currentData()

        self.name_input.clear()
        self.thickness_input.setValue(DEFAULT_THICKNESS)
        self.min_thickness_input.setValue(DEFAULT_THICKNESS)
        self.max_thickness_input.setValue(DEFAULT_THICKNESS)

        if isinstance(self.strat_column, sc.StratColumn):
            self.formation_top_input.setValue(self.strat_column.max_depth)
        else:
            self.formation_top_input.setValue(DEFAULT_FORMATION_TOP)

        self.young_age_input.setValue(DEFAULT_YOUNG_AGE)
        self.old_age_input.setValue(DEFAULT_OLD_AGE)

        if current_mode == ScalingMode.CHRONOLOGY:
            self.checkbox_formation_gap.setEnabled(False)
            self.formation_top_input.setEnabled(False)
            self.thickness_input.setEnabled(False)
            self.max_thickness_input.setEnabled(True)
            self.min_thickness_input.setEnabled(True)
        elif current_mode == ScalingMode.THICKNESS:
            self.checkbox_formation_gap.setEnabled(True)
            self.formation_top_input.setEnabled(False)
            self.thickness_input.setEnabled(True)
            self.max_thickness_input.setEnabled(False)
            self.min_thickness_input.setEnabled(False)
        else:
            self.checkbox_formation_gap.setEnabled(True)
            self.formation_top_input.setEnabled(True)
            self.thickness_input.setEnabled(True)
            self.max_thickness_input.setEnabled(False)
            self.min_thickness_input.setEnabled(False)

        
        
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
        thickness_range_layout = QHBoxLayout()
        render_range_layout = QHBoxLayout()
        
        # Layer input section
        layout.addWidget(QLabel("<b>Add New Layer:</b>"))
        
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
        self.thickness_input.setStyleSheet("QSpinBox:disabled { color: transparent; }")
        self.thickness_input.setRange(1, 10000)
        self.thickness_input.setValue(DEFAULT_THICKNESS)
        layout.addWidget(self.thickness_input)

        # Min max thickness for ScalingMode.CHRONOLOGY
        thickness_range_layout.addWidget(QLabel("Minimum Thickness (m):"))

        self.min_thickness_input = QSpinBox()
        self.min_thickness_input.setStyleSheet("QSpinBox:disabled { color: transparent; }")
        self.min_thickness_input.setRange(1, 10000)
        self.min_thickness_input.setSingleStep(1)
        self.min_thickness_input.setValue(DEFAULT_THICKNESS)

        thickness_range_layout.addWidget(self.min_thickness_input)

        thickness_range_layout.addWidget(QLabel("Maximum Thickness (m):"))
        self.max_thickness_input = QSpinBox()
        self.max_thickness_input.setStyleSheet("QSpinBox:disabled { color: transparent; }")
        self.max_thickness_input.setRange(1, 10000)
        self.max_thickness_input.setSingleStep(1)
        self.max_thickness_input.setValue(DEFAULT_THICKNESS)
        
        thickness_range_layout.addWidget(self.max_thickness_input)

        layout.addLayout(thickness_range_layout)

        # Formation Top
        layout.addWidget(QLabel("Formation Top (m):"))
        self.formation_top_input = QSpinBox()
        self.formation_top_input.setStyleSheet("QSpinBox:disabled { color: transparent; }")
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

        # Spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        layout.addWidget(QLabel("<b>Modify Display Options:</b>"))

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

        # Formation gap display mode
        formation_gap_layout = QHBoxLayout()
        formation_gap_label = QLabel("Show Formation Gaps")
        self.checkbox_formation_gap = QCheckBox()
        self.checkbox_formation_gap.setChecked(True)
        self.checkbox_formation_gap.stateChanged.connect(self.on_formation_gap_checkbox_changed)

        formation_gap_layout.addWidget(formation_gap_label)
        formation_gap_layout.addWidget(self.checkbox_formation_gap)
        formation_gap_layout.addStretch() 
        layout.addLayout(formation_gap_layout)
        
        # Render region based on age range
        render_range_layout.addWidget(QLabel("Display from age (Ma):"))

        self.display_from_age_input = QDoubleSpinBox()
        self.display_from_age_input.setDecimals(1)
        self.display_from_age_input.setRange(0.0, DEFAULT_OLD_AGE)
        self.display_from_age_input.setSingleStep(0.1)
        self.display_from_age_input.setValue(DEFAULT_YOUNG_AGE)

        render_range_layout.addWidget(self.display_from_age_input)

        render_range_layout.addWidget(QLabel("Display to age (Ma):"))
        self.display_to_age_input = QDoubleSpinBox()
        self.display_to_age_input.setDecimals(1)
        self.display_to_age_input.setRange(0.0, DEFAULT_OLD_AGE)
        self.display_to_age_input.setSingleStep(0.1)
        self.display_to_age_input.setValue(DEFAULT_OLD_AGE)
        
        render_range_layout.addWidget(self.display_to_age_input)

        self.display_from_age_input.editingFinished.connect(self.on_display_age_range_changed)
        self.display_to_age_input.editingFinished.connect(self.on_display_age_range_changed)

        self.display_from_age_input.valueChanged.connect(self.on_value_changed_from_arrows_display_age_range)
        self.display_to_age_input.valueChanged.connect(self.on_value_changed_from_arrows_display_age_range)

        layout.addLayout(render_range_layout)

        # Eras, Periods, Epochs, Ages
        checkbox_layout = QHBoxLayout()
        
        self.checkbox_eras = QCheckBox("Show Eras")
        self.checkbox_periods = QCheckBox("Show Periods") 
        self.checkbox_epochs = QCheckBox("Show Epochs")
        self.checkbox_ages = QCheckBox("Show Ages")

        # Default state
        self.checkbox_eras.setChecked(True)
        self.checkbox_periods.setChecked(True)
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

        # Spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Add layer button
        add_button = QPushButton("Add Layer")
        add_button.clicked.connect(self.add_layer)
        layout.addWidget(add_button)
        
        layout.addWidget(QLabel(""))
        
        # Layer list
        layout.addWidget(QLabel("Current Layers:"))
        self.layer_table = QTableWidget()
        self.layer_table.setColumnCount(5)
        self.layer_table.setHorizontalHeaderLabels(["Name", "Thickness", "Type", "Visibility", "Action"])
        self.layer_table.verticalHeader().setDefaultSectionSize(60)
        layout.addWidget(self.layer_table)

        self.reset_input_fields()
        
        return panel
    
    def add_layer(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter a layer name")
            return
        
        selected_rock = self.rock_type_combo.currentData()
        if isinstance(selected_rock, RockType):
            pattern = RockProperties.get_pattern(selected_rock)
        
        if self.scaling_mode_combo_box.currentData() == ScalingMode.FORMATION_TOP_THICKNESS or self.scaling_mode_combo_box.currentData() == ScalingMode.THICKNESS:
            thickness = self.thickness_input.value()

        if self.scaling_mode_combo_box.currentData() == ScalingMode.FORMATION_TOP_THICKNESS:
            formation_top = self.formation_top_input.value()
        else:
            formation_top = None

        young_age = self.young_age_input.value()
        old_age = self.old_age_input.value()
        
        selected_dep_env = self.dep_env_combo.currentData()

        min_thickness = None
        max_thickness = None

        if self.min_thickness_input.isEnabled() and self.max_thickness_input.isEnabled():
            min_thickness = self.min_thickness_input.value()
            max_thickness = self.max_thickness_input.value()

        if self.scaling_mode_combo_box.currentData() == ScalingMode.CHRONOLOGY:
            thickness = (min_thickness + max_thickness) / 2.0

        layer = Layer(name, thickness, selected_rock, formation_top, young_age, old_age, selected_dep_env, min_thickness=min_thickness, max_thickness=max_thickness)

        self.strat_column.add_layer(layer)
        self.update_layer_table()

        self.reset_input_fields()

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
        self.age_display_options_changed.emit(options)

    def on_formation_gap_checkbox_changed(self):
        """Called when formation gap checkbox state chages"""
        self.show_formation_gap_changed.emit(self.checkbox_formation_gap.isChecked())

    def on_display_age_range_changed(self):
        """Emit the display age range changed signal with current values"""
        from_age = self.display_from_age_input.value()
        to_age = self.display_to_age_input.value()
        self.display_age_range_changed.emit(from_age, to_age)
    
    def on_value_changed_from_arrows_display_age_range(self):
        # Only emit if the spinbox doesn't have focus
        sender = self.sender()
        if not sender.lineEdit().hasFocus():
            self.on_display_age_range_changed()

    def on_scaling_mode_changed(self, value):
        """Handle scaling mode change"""       
        # Get the selected ScalingMode enum
        current_mode = self.scaling_mode_combo_box.currentData()
        
        self.reset_input_fields()
        
        self.strat_column.update_scaling_mode(current_mode)

    def update_layer_table(self):
        self.layer_table.setRowCount(len(self.strat_column.layers))
        
        for i, layer in enumerate(self.strat_column.layers):
            self.layer_table.setItem(i, 0, QTableWidgetItem(layer.name))
            self.layer_table.setItem(i, 1, QTableWidgetItem(f"{layer.thickness}m"))
            self.layer_table.setItem(i, 2, QTableWidgetItem(layer.rock_type_display_name))

            # Visibility checkbox - centered in cell
            visibility_checkbox = QCheckBox()

            if layer.visible:
                visibility_checkbox.setChecked(True)
            
            visibility_checkbox.clicked.connect(partial(self.toggle_visibility_layer, i))

            # Create a widget to hold the checkbox and center it
            visibility_checkbox_widget = QWidget()
            visibility_checkbox_layout = QHBoxLayout(visibility_checkbox_widget)
            visibility_checkbox_layout.addWidget(visibility_checkbox)
            visibility_checkbox_layout.setAlignment(Qt.AlignCenter)
            visibility_checkbox_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for tighter fit

            self.layer_table.setCellWidget(i, 3, visibility_checkbox_widget)
            
            # Action buttons layout
            action_widget = QWidget()
            action_btn_layout = QVBoxLayout(action_widget)

            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(partial(self.edit_layer, i))

            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(partial(self.remove_layer, i))

            action_btn_layout.addWidget(edit_btn)
            action_btn_layout.addWidget(remove_btn)

            # Remove margins for a cleaner look
            action_btn_layout.setContentsMargins(0, 0, 0, 0)
            action_btn_layout.setSpacing(0)
            action_btn_layout.setAlignment(Qt.AlignCenter)

            # Set the widget to the table cell
            self.layer_table.setCellWidget(i, 4, action_widget)
            
    def edit_layer(self, index):
        """Edit a layer from the column"""
        if index < 0 or index >= len(self.strat_column.layers):
            return
        
        # Create and show the edit dialog
        layer = self.strat_column.layers[index]
        dialog = LayerEditDialog(layer, self)
        
        if dialog.exec() == QDialog.Accepted:
            self.strat_column.update()
            self.update_layer_table()
        else:
            pass

    def remove_layer(self, index):
        """Remove a layer from the column"""
        self.strat_column.remove_layer(index)
        self.update_layer_table()
        self.reset_input_fields()

    def toggle_visibility_layer(self, index):
        """Toggle layer visibility"""
        self.strat_column.toggle_visibility_layer(index)
import Layer
import pdb
import os
import re

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QPixmap
from PySide6.QtCore import Qt, QRectF
from ChronostratigraphicMapper import ChronostratigraphicMapper as chronomap
from Lithology import RockCategory, RockProperties, RockType

from enum import Enum

DEFAULT_COLUMN_SIZE = 100

class StratigraphicAgeTypes(Enum):
    ERAS = 'eras'
    PERIODS = 'periods'
    EPOCHS = 'epochs'
    AGES = 'ages'

class StratColumn(QWidget):
    def __init__(self):
        super().__init__()
        self.layers = []  # List of layer dictionaries
        self.setMinimumSize(500, 600)  # Increased width for era column
        self.chronomap = chronomap()
        self.texture_brushes = None
        self.load_texture(scale_factor=0.10, crop_pixels=16)
        self.display_options = {
            'show_eras': False,
            'show_periods': False,
            'show_epochs': True,
            'show_ages': True
        }
    
    def update_display_options(self, options):
        """Slot to receive display option updates"""
        self.display_options = options
        self.update()

    def add_layer(self, layer: Layer):
        self.layers.append(layer)
        # Trigger paint event
        self.update()
        
    def remove_layer(self, index):
        if 0 <= index < len(self.layers):
            del self.layers[index]
            self.update()
    
    def get_texture_brush(self, texture_id):
        """Get a specific texture brush by ID"""
        return self.texture_brushes.get(texture_id, None)

    def load_texture(self, scale_factor=1.0, crop_pixels=5):
        """Load and cache the texture brush with scaling and cropping"""
        self.texture_brushes = {}  # Dictionary to store all textures
        patterns_dir = "assets/patterns"
        
        # Check if directory exists
        if not os.path.exists(patterns_dir):
            print(f"Directory {patterns_dir} not found")
            return

        # Get all PNG files in the directory
        for filename in os.listdir(patterns_dir):
            if filename.lower().endswith('.png') and 'texture_' in filename:
                # Extract number from filename using regex
                match = re.search(r'texture_(\d+)\.png', filename)
                if match:
                    texture_number = match.group(1)
                    texture_path = os.path.join(patterns_dir, filename)
                    
                    # Load the texture
                    texture_pixmap = QPixmap(texture_path)
                    if not texture_pixmap.isNull():
                        # Crop pixels from each border
                        cropped_pixmap = texture_pixmap.copy(
                            crop_pixels,  # x offset
                            crop_pixels,  # y offset
                            texture_pixmap.width() - (crop_pixels * 2),   # new width
                            texture_pixmap.height() - (crop_pixels * 2)   # new height
                        )
                        
                        if scale_factor != 1.0:
                            # Scale the cropped texture
                            scaled_pixmap = cropped_pixmap.scaled(
                                int(cropped_pixmap.width() * scale_factor),
                                int(cropped_pixmap.height() * scale_factor),
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation
                            )
                            self.texture_brushes[texture_number] = QBrush(scaled_pixmap)
                        else:
                            self.texture_brushes[texture_number] = QBrush(cropped_pixmap)
                        
                        print(f"Loaded texture_{texture_number}.png")
                    else:
                        print(f"Failed to load {filename}")

    def paintEvent(self, event):
        """Draw the stratigraphic column with era display"""
        painter = QPainter(self)

        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            if not self.layers:
                painter.drawText(self.rect().center(), "No layers added")
                return
            
            # Column dimensions
            era_col_width = DEFAULT_COLUMN_SIZE  # Width for era column
            period_col_width = DEFAULT_COLUMN_SIZE # Width for period column
            epoch_col_width = DEFAULT_COLUMN_SIZE # Width for epoch column
            age_col_width = DEFAULT_COLUMN_SIZE # Width for age column
            col_width = DEFAULT_COLUMN_SIZE      # Width for main column
            pattern_col_width = DEFAULT_COLUMN_SIZE # Width for pattern column
            

            # Calculate x positions based on enabled options
            current_x = 0

            # Era column
            if self.display_options['show_eras']:
                era_col_x = current_x
                current_x += era_col_width
            else:
                era_col_x = None

            # Period column
            if self.display_options['show_periods']:
                period_col_x = current_x
                current_x += period_col_width
            else:
                period_col_x = None

            # Epoch column
            if self.display_options['show_epochs']:
                epoch_col_x = current_x
                current_x += epoch_col_width
            else:
                epoch_col_x = None

            # Age column
            if self.display_options['show_ages']:
                age_col_x = current_x
                current_x += age_col_width
            else:
                age_col_x = None

            # Main column always comes after all geological time columns
            col_x = current_x

            # Pattern column comes after main column
            pattern_col_x = col_x + col_width

            start_y = 50
            
            # Calculate total thickness for scaling
            total_thickness = sum(layer.thickness for layer in self.layers)
            available_height = self.height() - 150
            scale = available_height / total_thickness if total_thickness > 0 else 1
            
            current_y = start_y
            cumulative_depth = 0
            
            # Draw title
            painter.setPen(QPen(Qt.black, 1))
            title_font = QFont()
            title_font.setPointSize(14)
            title_font.setBold(True)
            painter.setFont(title_font)
            painter.drawText(0, 30, "Stratigraphic Column")

            # Draw each layer
            for i, layer in enumerate(self.layers):
                # Fetch required data
                layer_name = layer.name
                layer_thickness = layer.thickness
                layer_rock_type = layer.rock_type
                layer_formation_top = layer.formation_top
                layer_young_age = layer.young_age
                layer_old_age = layer.old_age
                layer_strat_ages = self.chronomap.map_age_to_chronostratigraphy(layer_young_age, layer_old_age)
                layer_height = layer_thickness * scale
                
                # Draw era column for this layer
                if era_col_x is not None:
                    self.draw_age_column(painter, layer, layer_strat_ages, 
                                        era_col_x, current_y, era_col_width, layer_height, StratigraphicAgeTypes.ERAS.value)
                
                # Draw period column for this layer
                if period_col_x is not None:
                    self.draw_age_column(painter, layer, layer_strat_ages, 
                                        period_col_x, current_y, period_col_width, layer_height, StratigraphicAgeTypes.PERIODS.value)
                    
                # Draw epoch column for this layer
                if epoch_col_x is not None:
                    self.draw_age_column(painter, layer, layer_strat_ages, 
                                        epoch_col_x, current_y, epoch_col_width, layer_height, StratigraphicAgeTypes.EPOCHS.value)
                    
                # Draw age column for this layer
                if age_col_x is not None:
                    self.draw_age_column(painter, layer, layer_strat_ages, 
                                        age_col_x, current_y, age_col_width, layer_height, StratigraphicAgeTypes.AGES.value)
                
                # Draw main layer rectangle
                painter.setPen(QPen(Qt.black, 1))
                painter.setBrush(QBrush(Qt.NoBrush))
                painter.drawRect(col_x, current_y, col_width, layer_height)
                
                # Draw layer label
                painter.setPen(QPen(Qt.black, 1))
                font = QFont()
                font.setPointSize(10)
                painter.setFont(font)
                
                text_rect = painter.boundingRect(col_x + 5, current_y + 5, 
                                            col_width - 10, layer_height - 10,
                                            Qt.AlignLeft | Qt.AlignTop,
                                            f"{layer_name}\n{layer.rock_type_display_name}\n{layer_thickness}m")
                
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop,
                            f"{layer_name}\n{layer.rock_type_display_name}\n{layer_thickness}m")
                
                # Draw pattern column for this layer
                self.draw_pattern_column(painter, layer, 
                                   pattern_col_x, current_y, pattern_col_width, layer_height, RockProperties.get_pattern(layer_rock_type))
            
                current_y += layer_height
            
            # Draw depth scale (position it after the main column)
            painter.setPen(QPen(Qt.black, 2))
            scale_x = pattern_col_x + pattern_col_width + 20
            painter.drawLine(scale_x, start_y, scale_x, current_y)
            
            # Add scale markers
            if total_thickness > 0:
                depth = 0
                y_pos = start_y
                
                for layer in self.layers:
                    layer_height = layer.thickness * scale
                    painter.drawLine(scale_x, y_pos, scale_x + 10, y_pos)
                    painter.drawText(scale_x + 15, y_pos + 5, f"{depth:.1f}m")
                    depth += layer.thickness
                    y_pos += layer_height
                
                # Final depth marker
                painter.drawLine(scale_x, y_pos, scale_x + 10, y_pos)
                painter.drawText(scale_x + 15, y_pos + 5, f"{depth:.1f}m")
                
        finally:
            painter.end()
    
    def draw_pattern_column(self, painter, layer, x, y, width, height, texture_id=0):
        """Draw the pattern column for a single layer"""
        painter.setPen(QPen(Qt.black, 1))

        # Get the specific texture brush
        texture_brush = self.get_texture_brush(texture_id)
        
        if texture_brush:
            painter.setBrush(texture_brush)
        else:
            painter.setBrush(QBrush(Qt.NoBrush))
        
        painter.drawRect(x, y, width, height)
        
    def draw_age_column(self, painter, layer, layer_strat_ages, x, y, width, height, age_name):
        """Draw the age column for a single layer"""
        # Get ages from the layer's stratigraphic ages
        ages = layer_strat_ages.get(age_name, [])
        
        if not ages:
            # Draw empty rectangle if no ages
            painter.setPen(QPen(Qt.gray, 1))
            painter.setBrush(QBrush(Qt.NoBrush))
            painter.drawRect(x, y, width, height)
            return
        
        # Layer's age range
        layer_young = layer.young_age
        layer_old = layer.old_age
        layer_age_range = layer_old - layer_young
        
        if layer_age_range <= 0:
            return
        
        # Draw each age proportionally
        for age in ages:
            age_name = age.get('name', 'Unknown')
            age_young = age.get('start_age', layer_young)
            age_old = age.get('end_age', layer_old)
            
            # Calculate the overlap between layer and age
            overlap_young = max(layer_young, age_young)
            overlap_old = min(layer_old, age_old)
            
            if overlap_old <= overlap_young:
                continue
            
            # Calculate proportional position and height within the layer
            # Position from top of layer (young age is at top)
            top_proportion = (overlap_young - layer_young) / layer_age_range
            bottom_proportion = (overlap_old - layer_young) / layer_age_range
            
            age_y = y + (top_proportion * height)
            age_height = (bottom_proportion - top_proportion) * height
            
            # Draw age rectangle with color
            color = QColor(age.get('color', '#c8c8c8'))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawRect(QRectF(x, age_y, width, age_height))
            
            # Draw age label if there's enough space
            if age_height > 15:
                font = QFont()
                font.setPointSize(9)
                painter.setFont(font)
                painter.setPen(QPen(Qt.black, 1))
                
                # Center the text in the age rectangle
                text_rect = QRectF(x + 5, age_y + 2, width - 10, age_height - 4)
                painter.drawText(text_rect, Qt.AlignCenter, age_name)
                
                # Add age labels if space permits
                if age_height > 30:
                    font.setPointSize(8)
                    painter.setFont(font)
                    painter.setPen(QPen(Qt.black, 1))
                    age_text = f"{overlap_young}-{overlap_old} Ma"
                    painter.drawText(text_rect, Qt.AlignBottom | Qt.AlignCenter, age_text)
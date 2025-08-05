import Layer
import pdb

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QPixmap
from PySide6.QtCore import Qt, QRectF
from ChronostratigraphicMapper import ChronostratigraphicMapper as chronomap

class StratColumn(QWidget):
    def __init__(self):
        super().__init__()
        self.layers = []  # List of layer dictionaries
        self.setMinimumSize(500, 600)  # Increased width for era column
        self.chronomap = chronomap()
        self.texture_brush = None
        self.load_texture("assets\\texture_601.png", scale_factor=0.15, crop_pixels=16)
    

    def add_layer(self, layer: Layer):
        self.layers.append(layer)
        # Trigger paint event
        self.update()
        
    def remove_layer(self, index):
        if 0 <= index < len(self.layers):
            del self.layers[index]
            self.update()
            
    def load_texture(self, texture_path, scale_factor=1.0, crop_pixels=5):
        """Load and cache the texture brush with scaling and cropping"""
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
                self.texture_brush = QBrush(scaled_pixmap)
            else:
                self.texture_brush = QBrush(cropped_pixmap)

    def paintEvent(self, event):
        """Draw the stratigraphic column with era display"""
        painter = QPainter(self)

        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            if not self.layers:
                painter.drawText(self.rect().center(), "No layers added")
                return
            
            # Column dimensions
            era_col_width = 120  # Width for era column
            col_width = 250      # Width for main column
            era_col_x = 0       # Era column starts at left margin
            col_x = era_col_x + era_col_width  # Main column immediately after era column (no gap)

            pattern_col_width = 120
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
            painter.drawText(era_col_x, 30, "Stratigraphic Column")

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
                
                # Draw era column for this layer (now on the left)
                self.draw_era_column(painter, layer, layer_strat_ages, 
                                    era_col_x, current_y, era_col_width, layer_height)
                
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
                                   pattern_col_x, current_y, pattern_col_width, layer_height)
            
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
    
    def draw_pattern_column(self, painter, layer, x, y, width, height):
        """Draw the pattern column for a single layer"""
        painter.setPen(QPen(Qt.black, 1))
        
        if self.texture_brush:
            painter.setBrush(self.texture_brush)
        else:
            painter.setBrush(QBrush(Qt.NoBrush))
        
        painter.drawRect(x, y, width, height)

    def draw_era_column(self, painter, layer, layer_strat_ages, x, y, width, height):
        """Draw the era column for a single layer"""
        # Get eras from the layer's stratigraphic ages
        eras = layer_strat_ages.get('eras', [])
        
        if not eras:
            # Draw empty rectangle if no eras
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
        
        # Draw each era proportionally
        for era in eras:
            era_name = era.get('name', 'Unknown')
            era_young = era.get('start_age', layer_young)
            era_old = era.get('end_age', layer_old)
            
            # Calculate the overlap between layer and era
            overlap_young = max(layer_young, era_young)
            overlap_old = min(layer_old, era_old)
            
            if overlap_old <= overlap_young:
                continue
            
            # Calculate proportional position and height within the layer
            # Position from top of layer (young age is at top)
            top_proportion = (overlap_young - layer_young) / layer_age_range
            bottom_proportion = (overlap_old - layer_young) / layer_age_range
            
            era_y = y + (top_proportion * height)
            era_height = (bottom_proportion - top_proportion) * height
            
            # Draw era rectangle with color
            color = QColor(era.get('color', '#c8c8c8'))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawRect(QRectF(x, era_y, width, era_height))
            
            # Draw era label if there's enough space
            if era_height > 15:
                font = QFont()
                font.setPointSize(9)
                painter.setFont(font)
                painter.setPen(QPen(Qt.black, 1))
                
                # Center the text in the era rectangle
                text_rect = QRectF(x + 5, era_y + 2, width - 10, era_height - 4)
                painter.drawText(text_rect, Qt.AlignCenter, era_name)
                
                # Add age labels if space permits
                if era_height > 30:
                    font.setPointSize(8)
                    painter.setFont(font)
                    painter.setPen(QPen(Qt.black, 1))
                    age_text = f"{overlap_young:.1f}-{overlap_old:.1f} Ma"
                    painter.drawText(text_rect, Qt.AlignBottom | Qt.AlignCenter, age_text)
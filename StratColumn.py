import Layer
import pdb

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush
from PySide6.QtCore import Qt

class StratColumn(QWidget):
    def __init__(self):
        super().__init__()
        self.layers = []  # List of layer dictionaries
        self.setMinimumSize(300, 600)
        
    def add_layer(self, layer: Layer):
        self.layers.append(layer)

        # Trigger paint event
        self.update()
        
    def remove_layer(self, index):
        if 0 <= index < len(self.layers):
            del self.layers[index]
            self.update()
            
    def paintEvent(self, event):
        """Draw the stratigraphic column"""
        painter = QPainter(self)

        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            if not self.layers:
                painter.drawText(self.rect().center(), "No layers added")
                return
            
            # Column dimensions
            col_width = 250
            col_x = 50
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
            painter.drawText(col_x, 30, "Stratigraphic Column")

             # Draw each layer
            for i, layer in enumerate(self.layers):
                layer_height = layer.thickness * scale
                
                # Draw layer rectangle
                painter.setPen(QPen(Qt.black, 1))
                painter.drawRect(col_x, current_y, col_width, layer_height)
                
                # Draw layer label
                painter.setPen(QPen(Qt.black, 1))
                font = QFont()
                font.setPointSize(10)
                painter.setFont(font)
                
                text_rect = painter.boundingRect(col_x + 5, current_y + 5, 
                                            col_width - 10, layer_height - 10,
                                            Qt.AlignLeft | Qt.AlignTop,
                                            f"{layer.name}\n{layer.rock_type_display_name}\n{layer.thickness}m")
                
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop,
                            f"{layer.name}\n{layer.rock_type_display_name}\n{layer.thickness}m")
                
                current_y += layer_height
            
            # Draw scale
            painter.setPen(QPen(Qt.black, 2))
            scale_x = col_x + col_width + 20
            painter.drawLine(scale_x, start_y, scale_x, current_y)
            
            # Add scale markers every 10m or appropriate interval
            if total_thickness > 0:
                interval = max(1, int(total_thickness / 10))
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

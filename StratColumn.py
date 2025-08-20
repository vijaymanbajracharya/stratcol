import Layer
import pdb
import os
import re
import sys

from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QPixmap
from PySide6.QtCore import Qt, QRectF, QRect
from ChronostratigraphicMapper import ChronostratigraphicMapper as chronomap
from Lithology import RockCategory, RockProperties, RockType
from app import ScalingMode

from enum import Enum
from utils import get_resource_path

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
        self.max_depth = 0.0
        self.display_options = {
            'show_eras': False,
            'show_periods': False,
            'show_epochs': True,
            'show_ages': True
        }
        self.scaling_mode = ScalingMode.FORMATION_TOP_THICKNESS
        self.show_uncomformity = True
    
    def update_scaling_mode(self, scaling_mode):
        '''Change scaling mode'''
        self.scaling_mode = scaling_mode
        self.update()

    def update_display_options(self, options):
        """Slot to receive display option updates"""
        self.display_options = options
        self.update()
    
    def update_uncomformity(self, show_uncomformity):
        self.show_uncomformity = show_uncomformity
        self.update()

    def check_layer_overlap(self, new_layer):
        """Check if a new layer would overlap with existing layers"""
        new_top = new_layer.formation_top
        new_bottom = new_layer.formation_top + new_layer.thickness
        
        for existing_layer in self.layers:
            existing_top = existing_layer.formation_top
            existing_bottom = existing_layer.formation_top + existing_layer.thickness
            
            # Check for overlap: layers overlap if one starts before the other ends
            if (new_top < existing_bottom and new_bottom > existing_top):
                return True, existing_layer
        
        return False, None

    def add_layer(self, layer: Layer):
        # Check for overlaps before adding
        has_overlap, overlapping_layer = self.check_layer_overlap(layer)
        
        if has_overlap:
            # Show warning dialog
            msg = QMessageBox()
            msg.setWindowTitle("Layer Overlap Warning")
            msg.setText(f"The new layer '{layer.name}' (top: {layer.formation_top}m, thickness: {layer.thickness}m) "
                       f"would overlap with existing layer '{overlapping_layer.name}' "
                       f"(top: {overlapping_layer.formation_top}m, thickness: {overlapping_layer.thickness}m).")
            msg.setInformativeText("The layer will not be added. Please adjust the formation top or thickness.")
            msg.setIcon(QMessageBox.Warning)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            return False
        
        self.layers.append(layer)
        # Sort layers by formation_top (shallowest first)
        self.layers.sort(key=lambda l: l.formation_top)

        _, max_depth = self.get_depth_range()
        self.max_depth = max_depth

        # Trigger paint event
        self.update()
        return True
        
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
        
        # Use the resource path helper function
        patterns_dir = get_resource_path("assets/patterns")
        
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
    def get_depth_range(self):
        """Calculate the total depth range needed for display"""
        if not self.layers:
            raise Exception("Attempted to find depth when no layers exist")
        
        min_depth = min(layer.formation_top for layer in self.layers)
        max_depth = max(layer.formation_top + layer.thickness for layer in self.layers)
        
        return min_depth, max_depth
    
    def get_age_range(self):
        """Calculate the total age range needed for display"""
        if not self.layers:
            raise Exception("Attempted to find age when no layers exist")
        
        all_ages = []
        for layer in self.layers:
            all_ages.extend([layer.young_age, layer.old_age])
        
        return min(all_ages), max(all_ages)
    
    def paint_scaling_mode_0(self, painter):
        # Column dimensions
        era_col_width = DEFAULT_COLUMN_SIZE  # Width for era column
        period_col_width = DEFAULT_COLUMN_SIZE # Width for period column
        epoch_col_width = DEFAULT_COLUMN_SIZE # Width for epoch column
        age_col_width = DEFAULT_COLUMN_SIZE # Width for age column
        col_width = DEFAULT_COLUMN_SIZE      # Width for main column
        pattern_col_width = DEFAULT_COLUMN_SIZE # Width for pattern column
        depositional_col_width = DEFAULT_COLUMN_SIZE # Width for depositional environment column
        
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

        # Depositional column comes after pattern column
        depoitional_col_x = pattern_col_x + pattern_col_width

        start_y = 50
        available_height = self.height() - 150
        
        # Get depth range and calculate scaling
        min_depth, max_depth = self.get_depth_range()
        total_depth_range = max_depth - min_depth
        
        if total_depth_range <= 0:
            total_depth_range = 1  # Avoid division by zero
        
        scale = available_height / total_depth_range
        
        # Draw title
        painter.setPen(QPen(Qt.black, 1))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(0, 30, "Stratigraphic Column")

        # Sort layers by formation_top to ensure proper order
        sorted_layers = sorted(self.layers, key=lambda l: l.formation_top)
        
        # Draw column backgrounds (empty spaces)
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QBrush(Qt.white))
        
        # Draw background for all columns
        column_positions = []
        if era_col_x is not None:
            column_positions.append((era_col_x, era_col_width))
        if period_col_x is not None:
            column_positions.append((period_col_x, period_col_width))
        if epoch_col_x is not None:
            column_positions.append((epoch_col_x, epoch_col_width))
        if age_col_x is not None:
            column_positions.append((age_col_x, age_col_width))
        column_positions.append((col_x, col_width))
        column_positions.append((pattern_col_x, pattern_col_width))
        column_positions.append((depoitional_col_x, depositional_col_width))
        
        # Calculate total height based on show_uncomformity setting
        if self.show_uncomformity:
            # Use actual depth range for scaling
            total_display_height = available_height
            scale = available_height / total_depth_range
        else:
            # Use cumulative thickness for scaling (no gaps)
            total_thickness = sum(layer.thickness for layer in sorted_layers)
            if total_thickness <= 0:
                total_thickness = 1  # Avoid division by zero
            scale = available_height / total_thickness
            total_display_height = available_height
        
        for col_x_pos, col_width_pos in column_positions:
            painter.drawRect(col_x_pos, start_y, col_width_pos, total_display_height)

        # Draw each layer at its correct position
        current_sequential_y = start_y  # For sequential positioning when show_uncomformity is False
        
        for layer in sorted_layers:
            if self.show_uncomformity:
                # Calculate layer position based on formation_top (with gaps for unconformities)
                layer_top_y = start_y + ((layer.formation_top - min_depth) * scale)
                layer_height = layer.thickness * scale
            else:
                # Position layers sequentially without gaps
                layer_top_y = current_sequential_y
                layer_height = layer.thickness * scale
                current_sequential_y += layer_height
            
            # Get layer data
            layer_name = layer.name
            layer_thickness = layer.thickness
            layer_rock_type = layer.rock_type
            layer_formation_top = layer.formation_top
            layer_young_age = layer.young_age
            layer_old_age = layer.old_age
            layer_strat_ages = self.chronomap.map_age_to_chronostratigraphy(layer_young_age, layer_old_age)
            
            # Draw era column for this layer
            if era_col_x is not None:
                self.draw_age_column(painter, layer, layer_strat_ages, 
                                    era_col_x, layer_top_y, era_col_width, layer_height, StratigraphicAgeTypes.ERAS.value)
            
            # Draw period column for this layer
            if period_col_x is not None:
                self.draw_age_column(painter, layer, layer_strat_ages, 
                                    period_col_x, layer_top_y, period_col_width, layer_height, StratigraphicAgeTypes.PERIODS.value)
                
            # Draw epoch column for this layer
            if epoch_col_x is not None:
                self.draw_age_column(painter, layer, layer_strat_ages, 
                                    epoch_col_x, layer_top_y, epoch_col_width, layer_height, StratigraphicAgeTypes.EPOCHS.value)
                
            # Draw age column for this layer
            if age_col_x is not None:
                self.draw_age_column(painter, layer, layer_strat_ages, 
                                    age_col_x, layer_top_y, age_col_width, layer_height, StratigraphicAgeTypes.AGES.value)
            
            # Draw main layer rectangle
            painter.setPen(QPen(Qt.black, 2))
            painter.setBrush(QBrush(Qt.white))
            painter.drawRect(col_x, layer_top_y, col_width, layer_height)
            
            # Draw layer label
            painter.setPen(QPen(Qt.black, 1))
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            
            text_rect = QRect(col_x + 5, layer_top_y + 5, col_width - 10, layer_height - 10)
            
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                        f"{layer_name}\n{layer.rock_type_display_name}\n{layer_thickness}m\nTop: {layer_formation_top}m")
            
            # Draw pattern column for this layer
            self.draw_pattern_column(painter, layer, 
                                pattern_col_x, layer_top_y, pattern_col_width, layer_height, RockProperties.get_pattern(layer_rock_type))
            
            # Draw the depositional environment for this layer
            self.draw_depositional_environment_column(painter, layer, 
                                                depoitional_col_x, layer_top_y, depositional_col_width, layer_height)
        
        # Draw depth scale (position it after the pattern column)
        painter.setPen(QPen(Qt.black, 2))
        scale_x = depoitional_col_x + depositional_col_width + 20
        painter.drawLine(scale_x, start_y, scale_x, start_y + total_display_height)
        
        # Add scale markers showing actual formation depths for each layer
        painter.setPen(QPen(Qt.black, 1))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        
        # Draw depth markers for each layer individually
        current_sequential_y_for_markers = start_y  # Track sequential position for markers
        
        if self.show_uncomformity:
            # When showing unconformities, use actual positions
            for layer in sorted_layers:
                layer_top_y_marker = start_y + ((layer.formation_top - min_depth) * scale)
                layer_height_marker = layer.thickness * scale
                layer_bottom_depth = layer.formation_top + layer.thickness
                layer_bottom_y_marker = layer_top_y_marker + layer_height_marker
                
                # Draw marker at top of layer (formation_top)
                painter.drawLine(scale_x, layer_top_y_marker, scale_x + 10, layer_top_y_marker)
                painter.drawText(scale_x + 15, layer_top_y_marker + 5, f"{layer.formation_top:.0f}m")
                
                # Draw marker at bottom of layer (formation_top + thickness)
                painter.drawLine(scale_x, layer_bottom_y_marker, scale_x + 10, layer_bottom_y_marker)
                painter.drawText(scale_x + 15, layer_bottom_y_marker + 5, f"{layer_bottom_depth:.0f}m")
        else:
            # When not showing unconformities, position markers at sequential positions
            # but ensure no overlap by using minimum spacing
            min_text_spacing = 15  # Minimum pixels between text labels
            last_text_y = start_y - min_text_spacing  # Track last text position
            
            for layer in sorted_layers:
                layer_height_marker = layer.thickness * scale
                layer_bottom_depth = layer.formation_top + layer.thickness
                
                # Draw marker at top of layer
                painter.drawLine(scale_x, current_sequential_y_for_markers, scale_x + 10, current_sequential_y_for_markers)
                
                # Position text to avoid overlap
                desired_text_y = current_sequential_y_for_markers + 5
                if desired_text_y < last_text_y + min_text_spacing:
                    text_y = last_text_y + min_text_spacing
                else:
                    text_y = desired_text_y
                
                painter.drawText(scale_x + 15, text_y, f"{layer.formation_top:.0f}m")
                last_text_y = text_y
                
                # Move to bottom of current layer
                current_sequential_y_for_markers += layer_height_marker
                
                # Draw marker at bottom of layer
                painter.drawLine(scale_x, current_sequential_y_for_markers, scale_x + 10, current_sequential_y_for_markers)
                
                # Position bottom text to avoid overlap
                desired_text_y = current_sequential_y_for_markers + 5
                if desired_text_y < last_text_y + min_text_spacing:
                    text_y = last_text_y + min_text_spacing
                else:
                    text_y = desired_text_y
                
                painter.drawText(scale_x + 15, text_y, f"{layer_bottom_depth:.0f}m")
                last_text_y = text_y

    def paint_scaling_mode_1(self, painter):
        # Column dimensions
        era_col_width = DEFAULT_COLUMN_SIZE  # Width for era column
        period_col_width = DEFAULT_COLUMN_SIZE # Width for period column
        epoch_col_width = DEFAULT_COLUMN_SIZE # Width for epoch column
        age_col_width = DEFAULT_COLUMN_SIZE # Width for age column
        col_width = DEFAULT_COLUMN_SIZE      # Width for main column
        pattern_col_width = DEFAULT_COLUMN_SIZE # Width for pattern column
        depositional_col_width = DEFAULT_COLUMN_SIZE # Width for depositional environment column
        
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

        # Depositional column comes after pattern column
        depoitional_col_x = pattern_col_x + pattern_col_width

        start_y = 50
        available_height = self.height() - 150
        
        # Sort layers by age - youngest (lowest age value) at top, oldest at bottom
        sorted_layers = sorted(self.layers, key=lambda l: l.young_age)
        
        # Calculate total age span across all layers (ignoring gaps)
        total_age_span = sum(layer.old_age - layer.young_age for layer in sorted_layers)
        
        if total_age_span <= 0:
            total_age_span = 1  # Avoid division by zero
        
        scale = available_height / total_age_span
        
        # Draw title
        painter.setPen(QPen(Qt.black, 1))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(0, 30, "Stratigraphic Column")
        
        # Draw column backgrounds (empty spaces)
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QBrush(Qt.white))
        
        # Draw background for all columns
        column_positions = []
        if era_col_x is not None:
            column_positions.append((era_col_x, era_col_width))
        if period_col_x is not None:
            column_positions.append((period_col_x, period_col_width))
        if epoch_col_x is not None:
            column_positions.append((epoch_col_x, epoch_col_width))
        if age_col_x is not None:
            column_positions.append((age_col_x, age_col_width))
        column_positions.append((col_x, col_width))
        column_positions.append((pattern_col_x, pattern_col_width))
        
        for col_x_pos, col_width_pos in column_positions:
            painter.drawRect(col_x_pos, start_y, col_width_pos, available_height)

        # Draw each layer consecutively, ignoring age gaps
        current_y = start_y
        
        for layer in sorted_layers:
            # Calculate layer height based on age span (old_age - young_age)
            layer_age_span = layer.old_age - layer.young_age
            layer_height = layer_age_span * scale
            
            # Ensure minimum height for visibility
            if layer_height < 5:
                layer_height = 5
            
            layer_top_y = current_y
            
            # Get layer data
            layer_name = layer.name
            layer_rock_type = layer.rock_type
            layer_young_age = layer.young_age
            layer_old_age = layer.old_age
            layer_strat_ages = self.chronomap.map_age_to_chronostratigraphy(layer_young_age, layer_old_age)
            
            # Draw era column for this layer
            if era_col_x is not None:
                self.draw_age_column(painter, layer, layer_strat_ages, 
                                    era_col_x, layer_top_y, era_col_width, layer_height, StratigraphicAgeTypes.ERAS.value)
            
            # Draw period column for this layer
            if period_col_x is not None:
                self.draw_age_column(painter, layer, layer_strat_ages, 
                                    period_col_x, layer_top_y, period_col_width, layer_height, StratigraphicAgeTypes.PERIODS.value)
                
            # Draw epoch column for this layer
            if epoch_col_x is not None:
                self.draw_age_column(painter, layer, layer_strat_ages, 
                                    epoch_col_x, layer_top_y, epoch_col_width, layer_height, StratigraphicAgeTypes.EPOCHS.value)
                
            # Draw age column for this layer
            if age_col_x is not None:
                self.draw_age_column(painter, layer, layer_strat_ages, 
                                    age_col_x, layer_top_y, age_col_width, layer_height, StratigraphicAgeTypes.AGES.value)
            
            # Draw main layer rectangle
            painter.setPen(QPen(Qt.black, 2))
            painter.setBrush(QBrush(Qt.white))
            painter.drawRect(col_x, layer_top_y, col_width, layer_height)
            
            # Draw layer label
            painter.setPen(QPen(Qt.black, 1))
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            
            text_rect = QRect(col_x + 5, layer_top_y + 5, col_width - 10, layer_height - 10)
            
            # Display age information instead of depth/thickness
            age_span_text = f"{layer_young_age:.1f} - {layer_old_age:.1f} Ma"
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                        f"{layer_name}\n{layer.rock_type_display_name}\n{age_span_text}")
            
            # Draw pattern column for this layer
            self.draw_pattern_column(painter, layer, 
                                pattern_col_x, layer_top_y, pattern_col_width, layer_height, RockProperties.get_pattern(layer_rock_type))
            
            # Draw the depositional environment for this layer
            self.draw_depositional_environment_column(painter, layer, 
                                                depoitional_col_x, layer_top_y, depositional_col_width, layer_height)
            
            # Move to next position for the next layer
            current_y += layer_height
    
    def paintEvent(self, event):
        """Draw the stratigraphic column with era display and formation tops"""
        painter = QPainter(self)

        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            if not self.layers:
                painter.drawText(self.rect().center(), "No layers added")
                return
            
            if self.scaling_mode == ScalingMode.FORMATION_TOP_THICKNESS:
                self.paint_scaling_mode_0(painter)
            elif self.scaling_mode == ScalingMode.CHRONOLOGY:
                self.paint_scaling_mode_1(painter)
            else:
                pass
                
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
            # Draw empty rectangle if no ages (will show background)
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
            if age_height > 15 and age_height <= 45:
                font = QFont()
                font.setPointSize(9)
                painter.setFont(font)
                painter.setPen(QPen(Qt.black, 1))
                
                # Center the text in the age rectangle
                text_rect = QRectF(x + 5, age_y + 2, width - 10, age_height - 4)
                painter.drawText(text_rect, Qt.AlignCenter, age_name)
            elif age_height > 45:
                font = QFont()
                
                # Center the text in the age rectangle
                third_height = age_height / 3
                top_rect = QRectF(x + 5, age_y + 2, width - 10, third_height)
                middle_rect = QRectF(x + 5, age_y + third_height, width - 10, third_height)
                bottom_rect = QRectF(x + 5, age_y + 2*third_height, width - 10, third_height)

                # Add age labels if space permits
                font.setPointSize(8)
                painter.setFont(font)
                painter.setPen(QPen(Qt.black, 1))
                age_text = f"{overlap_young} Ma"
                painter.drawText(top_rect, Qt.AlignCenter, age_text)

                font.setPointSize(9)
                painter.setFont(font)
                painter.setPen(QPen(Qt.black, 1))
                painter.drawText(middle_rect, Qt.AlignCenter, age_name)
                
                # Add age labels if space permits
                font.setPointSize(8)
                painter.setFont(font)
                painter.setPen(QPen(Qt.black, 1))
                age_text = f"{overlap_old} Ma"
                painter.drawText(bottom_rect, Qt.AlignCenter, age_text)
            else:
                pass
    
    def draw_depositional_environment_column(self, painter, layer, x, y, width, height):
        layer_dep_env_name = layer.dep_env.display_name
        layer_dep_env_color = layer.dep_env.color
        painter.setBrush(QBrush(QColor(layer_dep_env_color)))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(x, y, width, height)

        text_rect = QRect(x + 5, y + 5, width - 10, height - 10)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                            f"{layer_dep_env_name.upper()}")

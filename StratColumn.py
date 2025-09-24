import Layer
import pdb
import os
import re
import sys
import math

from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QPixmap, QPainterPath
from PySide6.QtCore import Qt, QRectF, QRect
from ChronostratigraphicMapper import ChronostratigraphicMapper as chronomap
from Lithology import RockCategory, RockProperties, RockType
from app import ScalingMode
from Deposition import DepositionalEnvironment

from enum import Enum
from utils import get_resource_path

DEFAULT_COLUMN_SIZE = 120
DEFAULT_YOUNG_AGE = 0.0
DEFAULT_OLD_AGE = 4567.0

def get_contrasting_color_from_hex(hex_color):
    """Return white QColor for dark backgrounds, black QColor for light backgrounds"""
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    
    # Convert hex to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Calculate luminance using standard formula
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    
    # Return white for dark backgrounds (luminance < 0.5), black for light
    return QColor(255, 255, 255) if luminance < 0.5 else QColor(0, 0, 0)

class StratigraphicAgeTypes(Enum):
    ERAS = 'eras'
    PERIODS = 'periods'
    EPOCHS = 'epochs'
    AGES = 'ages'

class StratColumn(QWidget):
    def __init__(self):
        super().__init__()
        self.layers = []  
        self.setMinimumSize(500, 600)  
        self.chronomap = chronomap()
        self.texture_brushes = None
        self.load_texture(scale_factor=0.10, crop_pixels=16)
        self.max_depth = 0.0
        self.max_age = 0.0
        self.display_options = {
            'show_eras': True,
            'show_periods': True,
            'show_epochs': True,
            'show_ages': True
        }
        self.scaling_mode = ScalingMode.CHRONOLOGY
        self.show_formation_gap = True
        self.display_age_range = (DEFAULT_YOUNG_AGE, DEFAULT_OLD_AGE)
    
    def update_scaling_mode(self, scaling_mode):
        '''Change scaling mode'''
        self.scaling_mode = scaling_mode
        self.update()

    def update_age_display_options(self, options):
        """Slot to receive display option updates"""
        self.display_options = options
        self.update()
    
    def update_formation_gap(self, show_formation_gap):
        self.show_formation_gap = show_formation_gap
        self.update()

    def update_display_age_range(self, from_age, to_age):
        self.display_age_range = (from_age, to_age)
        self.update()

    def check_layer_overlap(self, new_layer):
        """Check if a new layer would overlap with existing layers"""
        new_top = new_layer.formation_top
        new_bottom = new_layer.formation_top + new_layer.thickness
        
        for existing_layer in self.layers:
            existing_top = existing_layer.formation_top
            existing_bottom = existing_layer.formation_top + existing_layer.thickness
            
            # Check for overlap
            if (new_top < existing_bottom and new_bottom > existing_top):
                return True, existing_layer
        
        return False, None

    def add_layer(self, layer: Layer):
        # Check for overlaps before adding
        if self.scaling_mode == ScalingMode.FORMATION_TOP_THICKNESS:
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

        # Trigger paint event
        self.update()
        return True
    
    def edit_layer(self, index):
        pass
    
    def remove_layer(self, index):
        if 0 <= index < len(self.layers):
            del self.layers[index]
            self.update()
    
    def toggle_visibility_layer(self, index):
        if 0 <= index < len(self.layers):
            self.layers[index].toggle_visibility()
            self.update() 

    def get_texture_brush(self, texture_id):
        """Get a specific texture brush by ID"""
        return self.texture_brushes.get(texture_id, None)

    def load_texture(self, scale_factor=1.0, crop_pixels=5):
        """Load and cache the texture brush with scaling and cropping"""
        self.texture_brushes = {} 
        
        patterns_dir = get_resource_path("assets/patterns")
        
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
    def get_depth_range(self, visible_layers):
        """Calculate the total depth range needed for display"""
        if not self.layers:
            return 0, 0
        
        min_depth = min(layer.formation_top for layer in visible_layers)
        max_depth = max(layer.formation_top + layer.thickness for layer in visible_layers)
        
        return min_depth, max_depth
    
    def get_age_range(self, visible_layers):
        """Calculate the total age range needed for display"""
        if not self.layers:
            return 0.0, 0.0
        
        all_ages = []
        for layer in visible_layers:
            all_ages.extend([layer.young_age, layer.old_age])
        
        return min(all_ages), max(all_ages)
    
    def layer_intersects_age_range_partial(self, layer, from_age, to_age):
        # Layer intersects if:
        # - Layer's young age is less than display range's old age AND
        # - Layer's old age is greater than display range's young age
        return layer.young_age < to_age and layer.old_age > from_age
    
    def layer_intersects_age_range_full(self, layer, from_age, to_age):     
        # Layer must be completely within the age range
        return layer.young_age >= from_age and layer.old_age <= to_age
    
    def paint_scaling_mode_0(self, painter):       
        # Filter for only visible layers AND layers within the display age range
        from_age, to_age = self.display_age_range
        visible_layers = [
            layer for layer in self.layers 
            if layer.visible and self.layer_intersects_age_range_full(layer, from_age, to_age)
        ]

        # If no visible layers, don't render anything
        if not visible_layers:
            return
        
        # Check if any layer lacks formation_top information
        layers_without_formation_top = [layer for layer in visible_layers if layer.formation_top is None]
        if layers_without_formation_top:
            # Draw error message
            painter.setPen(QPen(Qt.black, 1))
            painter.drawText(self.rect().center(), "No formation top information in layers")
            return
    
        # Column dimensions
        era_col_width = DEFAULT_COLUMN_SIZE  # Width for era column
        period_col_width = DEFAULT_COLUMN_SIZE # Width for period column
        epoch_col_width = DEFAULT_COLUMN_SIZE # Width for epoch column
        age_col_width = DEFAULT_COLUMN_SIZE # Width for age column
        col_width = DEFAULT_COLUMN_SIZE      # Width for main column
        pattern_col_width = DEFAULT_COLUMN_SIZE # Width for pattern column
        depositional_col_width = DEFAULT_COLUMN_SIZE # Width for depositional environment column
        
        # Check if we should show depositional environment column
        # Only show if at least one layer has something other than UNKNOWN_NONE
        show_depositional_column = any(
            hasattr(layer, 'dep_env') and 
            layer.dep_env is not None and
            layer.dep_env != DepositionalEnvironment.UNKNOWN_NONE
            for layer in visible_layers
        )

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
        if show_depositional_column:
            depoitional_col_x = pattern_col_x + pattern_col_width
        else:
            depoitional_col_x = None

        start_y = 50
        available_height = self.height() - 150
        
        # Get depth range and calculate scaling
        min_depth, max_depth = self.get_depth_range(visible_layers)
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
        sorted_layers = sorted(visible_layers, key=lambda l: l.formation_top)
        
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
        if depoitional_col_x is not None:
            column_positions.append((depoitional_col_x, depositional_col_width))
        
        # Calculate total height based on show_formation_gap setting
        if self.show_formation_gap:
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
        current_sequential_y = start_y  # For sequential positioning when show_formation_gap is False
        
        for layer in sorted_layers:
            if self.show_formation_gap:
                # Calculate layer position based on formation_top (with gaps for formation gaps)
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
            painter.setPen(QPen(Qt.black, 1))
            painter.setBrush(QBrush(Qt.white))
            painter.drawRect(col_x, layer_top_y, col_width, layer_height)
            
            # Draw layer label
            painter.setPen(QPen(Qt.black, 1))
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            
            text_rect = QRect(col_x + 5, layer_top_y + 5, col_width - 10, layer_height - 10)
            
            if self.scaling_mode == ScalingMode.FORMATION_TOP_THICKNESS:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                        f"{layer_name}\n{layer.rock_type_display_name}\n{layer_thickness}m\nTop: {layer_formation_top}m")
            else:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                        f"{layer_name}\n{layer.rock_type_display_name}\n{layer_thickness}m")
            
            # Draw pattern column for this layer
            self.draw_pattern_column(painter, layer, 
                                pattern_col_x, layer_top_y, pattern_col_width, layer_height, RockProperties.get_pattern(layer_rock_type))
            
            # Draw the depositional environment for this layer
            if depoitional_col_x is not None:
                self.draw_depositional_environment_column(painter, layer, depoitional_col_x, layer_top_y, depositional_col_width, layer_height)
        
        if self.scaling_mode == ScalingMode.FORMATION_TOP_THICKNESS:
            # Draw depth scale (position it after the pattern column)
            painter.setPen(QPen(Qt.black, 1))

            if depoitional_col_x is not None:
                scale_x = depoitional_col_x + depositional_col_width + 20
            else:
                scale_x = pattern_col_x + pattern_col_width + 20

            painter.drawLine(scale_x, start_y, scale_x, start_y + total_display_height)
            
            # Add scale markers showing actual formation depths for each layer
            painter.setPen(QPen(Qt.black, 1))
            font = QFont()
            font.setPointSize(9)
            painter.setFont(font)
            
            # Draw depth markers for each layer individually
            current_sequential_y_for_markers = start_y  # Track sequential position for markers
            
            if self.show_formation_gap:
                # When showing formation gaps, use actual positions
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
                # When not showing formation gaps, position markers at sequential positions
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

    def paint_scaling_mode_2(self, painter):       
        # Filter for only visible layers AND layers within the display age range
        from_age, to_age = self.display_age_range
        visible_layers = [
            layer for layer in self.layers 
            if layer.visible and self.layer_intersects_age_range_full(layer, from_age, to_age)
        ]

        # If no visible layers, don't render anything
        if not visible_layers:
            return

        # Column dimensions
        era_col_width = DEFAULT_COLUMN_SIZE  # Width for era column
        period_col_width = DEFAULT_COLUMN_SIZE # Width for period column
        epoch_col_width = DEFAULT_COLUMN_SIZE # Width for epoch column
        age_col_width = DEFAULT_COLUMN_SIZE # Width for age column
        col_width = DEFAULT_COLUMN_SIZE      # Width for main column
        pattern_col_width = DEFAULT_COLUMN_SIZE # Width for pattern column
        depositional_col_width = DEFAULT_COLUMN_SIZE # Width for depositional environment column
        
        # Check if we should show depositional environment column
        # Only show if at least one layer has something other than UNKNOWN_NONE
        show_depositional_column = any(
            hasattr(layer, 'dep_env') and 
            layer.dep_env is not None and
            layer.dep_env != DepositionalEnvironment.UNKNOWN_NONE
            for layer in visible_layers
        )

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
        if show_depositional_column:
            depoitional_col_x = pattern_col_x + pattern_col_width
        else:
            depoitional_col_x = None

        start_y = 50
        available_height = self.height() - 150
        
        # Draw title
        painter.setPen(QPen(Qt.black, 1))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(0, 30, "Stratigraphic Column")

        # Sort layers by age to ensure proper chronological order
        sorted_layers = sorted(visible_layers, key=lambda l: l.young_age)
        
        # Calculate total thickness for scaling
        total_thickness = sum(layer.thickness for layer in sorted_layers)
        if total_thickness <= 0:
            total_thickness = 1  # Avoid division by zero
        
        # Scale based on thickness only
        scale = available_height / total_thickness
        total_display_height = available_height
        
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
        
        if depoitional_col_x is not None:
            column_positions.append((depoitional_col_x, depositional_col_width))
        
        for col_x_pos, col_width_pos in column_positions:
            painter.drawRect(col_x_pos, start_y, col_width_pos, total_display_height)

        # Draw each layer sequentially based on chronological order
        current_y = start_y
        
        for layer in sorted_layers:
            # Calculate layer height based on thickness only
            layer_height = layer.thickness * scale
            layer_top_y = current_y
            
            # Get layer data
            layer_name = layer.name
            layer_thickness = layer.thickness
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
            painter.setPen(QPen(Qt.black, 1))
            painter.setBrush(QBrush(Qt.white))
            painter.drawRect(col_x, layer_top_y, col_width, layer_height)
            
            # Draw layer label
            painter.setPen(QPen(Qt.black, 1))
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            
            text_rect = QRect(col_x + 5, layer_top_y + 5, col_width - 10, layer_height - 10)
            
            # Display layer info with age information instead of formation depth
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                    f"{layer_name}\n{layer.rock_type_display_name}\n{layer_thickness}m\nAge: {layer_young_age}-{layer_old_age} Ma")
            
            # Draw pattern column for this layer
            self.draw_pattern_column(painter, layer, 
                                pattern_col_x, layer_top_y, pattern_col_width, layer_height, RockProperties.get_pattern(layer_rock_type))
            
            # Draw the depositional environment for this layer
            if depoitional_col_x is not None:
                self.draw_depositional_environment_column(painter, layer, depoitional_col_x, layer_top_y, depositional_col_width, layer_height)
            
            # Move to next layer position
            current_y += layer_height

    def paint_scaling_mode_1(self, painter):
        # Filter for only visible layers AND layers within the display age range
        from_age, to_age = self.display_age_range
        visible_layers = [
            layer for layer in self.layers 
            if layer.visible and self.layer_intersects_age_range_full(layer, from_age, to_age)
        ]
        
        # If no visible layers, don't render anything
        if not visible_layers:
            return
        
        # Column dimensions
        era_col_width = DEFAULT_COLUMN_SIZE  # Width for era column
        period_col_width = DEFAULT_COLUMN_SIZE # Width for period column
        epoch_col_width = DEFAULT_COLUMN_SIZE # Width for epoch column
        age_col_width = DEFAULT_COLUMN_SIZE # Width for age column
        col_width = DEFAULT_COLUMN_SIZE      # Width for main column
        pattern_col_width = DEFAULT_COLUMN_SIZE # Width for pattern column
        depositional_col_width = DEFAULT_COLUMN_SIZE # Width for depositional environment column
        
        # Helper function to check if a layer has valid depositional environment
        def has_valid_depositional_env(layer):
            if not hasattr(layer, 'dep_env'):
                return False
            dep_env = layer.dep_env
            if dep_env is None:
                return False
            # Handle both enum instances and string/dict representations
            if isinstance(dep_env, DepositionalEnvironment):
                return dep_env != DepositionalEnvironment.UNKNOWN_NONE
            elif isinstance(dep_env, str):
                return dep_env != 'UNKNOWN_NONE' and dep_env != 'Unknown/None'
            elif isinstance(dep_env, dict):
                return dep_env.get('name') != 'UNKNOWN_NONE' and dep_env.get('display_name') != 'Unknown/None'
            return False
        
        # Check if we should show depositional environment column
        # Only show if at least one layer has something other than UNKNOWN_NONE
        show_depositional_column = any(has_valid_depositional_env(layer) for layer in visible_layers)

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

        # Depositional column comes after pattern column (only if we're showing it)
        if show_depositional_column:
            depoitional_col_x = pattern_col_x + pattern_col_width
        else:
            depoitional_col_x = None

        start_y = 50
        available_height = self.height() - 150
        
        # Sort layers by age - youngest (lowest age value) at top, oldest at bottom
        sorted_layers = sorted(visible_layers, key=lambda l: l.young_age)
        
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
        if depoitional_col_x is not None:
            column_positions.append((depoitional_col_x, depositional_col_width))
        
        for col_x_pos, col_width_pos in column_positions:
            painter.drawRect(col_x_pos, start_y, col_width_pos, available_height)

        # Pre-calculate which layers have unconformities (age gaps)
        gap_threshold = 1.0  # Million years - adjust as needed
        layers_with_gaps = set()  # Will contain indices of layers that have gaps above them
        wavy_boundaries = []  # Store positions where wavy boundaries should be drawn
        
        for i in range(1, len(sorted_layers)):
            previous_layer = sorted_layers[i - 1]
            current_layer = sorted_layers[i]
            age_gap = current_layer.young_age - previous_layer.old_age
            
            if age_gap > gap_threshold:
                layers_with_gaps.add(i)

        # Calculate layer positions and store wavy boundary positions
        current_y = start_y
        layer_positions = []
        
        for i, layer in enumerate(sorted_layers):
            # Calculate layer height based on age span (old_age - young_age)
            layer_age_span = layer.old_age - layer.young_age
            layer_height = layer_age_span * scale
            
            # Ensure minimum height for visibility
            if layer_height < 5:
                layer_height = 5
            
            layer_top_y = current_y
            
            # Store layer position info
            has_gap_above = i in layers_with_gaps
            has_gap_below = (i + 1) in layers_with_gaps
            
            layer_positions.append({
                'layer': layer,
                'index': i,
                'top_y': layer_top_y,
                'height': layer_height,
                'has_gap_above': has_gap_above,
                'has_gap_below': has_gap_below
            })
            
            # Move to next position
            current_y += layer_height
            
            # Store wavy boundary position if there's a gap below
            if has_gap_below:
                age_gap = sorted_layers[i + 1].young_age - layer.old_age
                wavy_boundaries.append({
                    'y_position': current_y,
                    'age_gap': age_gap
                })

        # First pass: Draw all layer contents (fills, age columns, text)
        for layer_info in layer_positions:
            layer = layer_info['layer']
            layer_top_y = layer_info['top_y']
            layer_height = layer_info['height']
            has_gap_above = layer_info['has_gap_above']
            has_gap_below = layer_info['has_gap_below']
            
            # Get layer data
            layer_name = layer.name
            layer_rock_type = layer.rock_type
            layer_young_age = layer.young_age
            layer_old_age = layer.old_age
            layer_min_thickness = layer.min_thickness
            layer_max_thickness = layer.max_thickness
            layer_strat_ages = self.chronomap.map_age_to_chronostratigraphy(layer_young_age, layer_old_age)
            
            # Helper function to draw age column content
            def draw_age_column_content(col_x, col_width, age_type_name):
                if col_x is None:
                    return []
                
                ages = layer_strat_ages.get(age_type_name, [])
                if not ages:
                    return []
                
                layer_age_range = layer_old_age - layer_young_age
                if layer_age_range <= 0:
                    return []
                
                age_rectangles = []
                for age in ages:
                    age_name_text = age.get('name', 'Unknown')
                    age_young = age.get('start_age', layer_young_age)
                    age_old = age.get('end_age', layer_old_age)
                    
                    overlap_young = max(layer_young_age, age_young)
                    overlap_old = min(layer_old_age, age_old)
                    
                    if overlap_old <= overlap_young:
                        continue
                    
                    top_proportion = (overlap_young - layer_young_age) / layer_age_range
                    bottom_proportion = (overlap_old - layer_young_age) / layer_age_range
                    
                    age_y = layer_top_y + (top_proportion * layer_height)
                    age_height = (bottom_proportion - top_proportion) * layer_height
                    
                    age_rectangles.append({
                        'name': age_name_text,
                        'y': age_y,
                        'height': age_height,
                        'color': age.get('color', '#c8c8c8'),
                        'overlap_young': overlap_young,
                        'overlap_old': overlap_old
                    })
                    
                    # Fill age rectangle with color
                    color = QColor(age.get('color', '#c8c8c8'))
                    painter.setBrush(QBrush(color))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(QRectF(col_x, age_y, col_width, age_height))
                
                return age_rectangles
            
            # Draw all age columns content
            era_rects = draw_age_column_content(era_col_x, era_col_width, StratigraphicAgeTypes.ERAS.value)
            period_rects = draw_age_column_content(period_col_x, period_col_width, StratigraphicAgeTypes.PERIODS.value)
            epoch_rects = draw_age_column_content(epoch_col_x, epoch_col_width, StratigraphicAgeTypes.EPOCHS.value)
            age_rects = draw_age_column_content(age_col_x, age_col_width, StratigraphicAgeTypes.AGES.value)
            
            # Store age rectangles for text drawing
            layer_info['era_rects'] = era_rects
            layer_info['period_rects'] = period_rects
            layer_info['epoch_rects'] = epoch_rects
            layer_info['age_rects'] = age_rects
            
            # Fill main layer rectangle (no borders yet)
            painter.setBrush(QBrush(Qt.white))
            painter.setPen(Qt.NoPen)
            painter.drawRect(col_x, layer_top_y, col_width, layer_height)
            
            # Fill pattern column rectangle (no borders yet)
            texture_brush = self.get_texture_brush(RockProperties.get_pattern(layer_rock_type))
            if texture_brush:
                painter.setBrush(texture_brush)
            else:
                painter.setBrush(QBrush(Qt.NoBrush))
            painter.drawRect(pattern_col_x, layer_top_y, pattern_col_width, layer_height)
            
            # Fill depositional environment rectangle (no borders yet) - only if column is shown and layer has valid dep env
            if depoitional_col_x is not None and has_valid_depositional_env(layer):
                layer_dep_env_color = layer.dep_env.color
                painter.setBrush(QBrush(QColor(layer_dep_env_color)))
                painter.drawRect(depoitional_col_x, layer_top_y, depositional_col_width, layer_height)
            
            # Draw layer label
            painter.setPen(QPen(Qt.black, 1))
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            
            text_rect = QRect(col_x + 5, layer_top_y + 5, col_width - 10, layer_height - 10)
            
            # Display age information instead of depth/thickness
            age_span_text = f"{layer_young_age:.1f} - {layer_old_age:.1f} Ma"

            if layer_min_thickness is not None and layer_max_thickness is not None:
                thickness_span_text = f"{layer_min_thickness}m - {layer_max_thickness}m"
            else:
                thickness_span_text = ""
                
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                        f"{layer_name}\n{layer.rock_type_display_name}\n{thickness_span_text}\n{age_span_text}")
            
            # Draw depositional environment text - only if column is shown and layer has valid dep env
            if depoitional_col_x is not None and has_valid_depositional_env(layer):
                layer_dep_env_name = layer.dep_env.display_name
                layer_dep_env_color = layer.dep_env.color

                text_color = get_contrasting_color_from_hex(layer_dep_env_color) 
                painter.setPen(QPen(text_color, 1))  
                dep_text_rect = QRect(depoitional_col_x + 5, layer_top_y + 5, depositional_col_width - 10, layer_height - 10)
                painter.drawText(dep_text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                                    f"{layer_dep_env_name.upper()}")

            # Draw age column text labels
            def draw_age_text_labels(age_rectangles, col_x, col_width):
                if not age_rectangles or col_x is None:
                    return
                
                painter.setPen(QPen(Qt.black, 1))
                for age_rect in age_rectangles:
                    age_y = age_rect['y']
                    age_height = age_rect['height']
                    age_name_text = age_rect['name']
                    overlap_young = age_rect['overlap_young']
                    overlap_old = age_rect['overlap_old']

                    bg_color = age_rect.get('color', '#c8c8c8')

                    # Calculate contrasting text color
                    text_color = get_contrasting_color_from_hex(bg_color)
                    painter.setPen(QPen(text_color, 1))
                    
                    if age_height > 15 and age_height <= 45:
                        font = QFont()
                        font.setPointSize(9)
                        painter.setFont(font)
                        text_rect = QRectF(col_x + 5, age_y + 2, col_width - 10, age_height - 4)
                        painter.drawText(text_rect, Qt.AlignCenter, age_name_text)
                    elif age_height > 45:
                        font = QFont()
                        third_height = age_height / 3
                        top_rect = QRectF(col_x + 5, age_y + 2, col_width - 10, third_height)
                        middle_rect = QRectF(col_x + 5, age_y + third_height, col_width - 10, third_height)
                        bottom_rect = QRectF(col_x + 5, age_y + 2*third_height, col_width - 10, third_height)

                        font.setPointSize(8)
                        painter.setFont(font)
                        age_text = f"{overlap_young} Ma"
                        painter.drawText(top_rect, Qt.AlignCenter, age_text)

                        font.setPointSize(9)
                        painter.setFont(font)
                        painter.drawText(middle_rect, Qt.AlignCenter, age_name_text)
                        
                        font.setPointSize(8)
                        painter.setFont(font)
                        age_text = f"{overlap_old} Ma"
                        painter.drawText(bottom_rect, Qt.AlignCenter, age_text)
            
            # Draw text for all age columns
            draw_age_text_labels(era_rects, era_col_x, era_col_width)
            draw_age_text_labels(period_rects, period_col_x, period_col_width)
            draw_age_text_labels(epoch_rects, epoch_col_x, epoch_col_width)
            draw_age_text_labels(age_rects, age_col_x, age_col_width)

        # Second pass: Draw all wavy boundaries
        for boundary in wavy_boundaries:
            self.draw_wavy_boundary(painter, boundary['y_position'], column_positions, boundary['age_gap'])

        # Third pass: Draw all borders (avoiding wavy boundary areas)
        for layer_info in layer_positions:
            layer = layer_info['layer']
            layer_top_y = layer_info['top_y']
            layer_height = layer_info['height']
            has_gap_above = layer_info['has_gap_above']
            has_gap_below = layer_info['has_gap_below']
            
            # Helper function to draw age column borders
            def draw_age_column_borders(col_x, col_width, age_rectangles):
                if col_x is None:
                    return
                
                painter.setPen(QPen(Qt.black, 1))
                
                # Always draw left and right borders for the full height
                painter.drawLine(col_x, layer_top_y, col_x, layer_top_y + layer_height)
                painter.drawLine(col_x + col_width, layer_top_y, col_x + col_width, layer_top_y + layer_height)
                
                # Draw top border only if there's no gap above
                if not has_gap_above:
                    painter.drawLine(col_x, layer_top_y, col_x + col_width, layer_top_y)
                
                # Draw bottom border only if there's no gap below
                if not has_gap_below:
                    painter.drawLine(col_x, layer_top_y + layer_height, col_x + col_width, layer_top_y + layer_height)
                
                # Draw internal horizontal borders between age periods only if there are no gaps
                if not has_gap_above and not has_gap_below and len(age_rectangles) > 1:
                    sorted_rects = sorted(age_rectangles, key=lambda r: r['y'])
                    for i in range(len(sorted_rects) - 1):
                        current_rect = sorted_rects[i]
                        boundary_y = current_rect['y'] + current_rect['height']
                        painter.drawLine(col_x, boundary_y, col_x + col_width, boundary_y)
            
            # Draw borders for all age columns
            draw_age_column_borders(era_col_x, era_col_width, layer_info['era_rects'])
            draw_age_column_borders(period_col_x, period_col_width, layer_info['period_rects'])
            draw_age_column_borders(epoch_col_x, epoch_col_width, layer_info['epoch_rects'])
            draw_age_column_borders(age_col_x, age_col_width, layer_info['age_rects'])
            
            # Draw main column borders selectively
            painter.setPen(QPen(Qt.black, 1))
            
            # Always draw left and right borders
            painter.drawLine(col_x, layer_top_y, col_x, layer_top_y + layer_height)
            painter.drawLine(col_x + col_width, layer_top_y, col_x + col_width, layer_top_y + layer_height)
            
            # Draw top border only if there's no gap above
            if not has_gap_above:
                painter.drawLine(col_x, layer_top_y, col_x + col_width, layer_top_y)
            
            # Draw bottom border only if there's no gap below
            if not has_gap_below:
                painter.drawLine(col_x, layer_top_y + layer_height, col_x + col_width, layer_top_y + layer_height)
            
            # Draw pattern column borders selectively
            painter.setPen(QPen(Qt.black, 1))
            
            # Always draw left and right borders
            painter.drawLine(pattern_col_x, layer_top_y, pattern_col_x, layer_top_y + layer_height)
            painter.drawLine(pattern_col_x + pattern_col_width, layer_top_y, pattern_col_x + pattern_col_width, layer_top_y + layer_height)
            
            # Draw top border only if there's no gap above
            if not has_gap_above:
                painter.drawLine(pattern_col_x, layer_top_y, pattern_col_x + pattern_col_width, layer_top_y)
            
            # Draw bottom border only if there's no gap below
            if not has_gap_below:
                painter.drawLine(pattern_col_x, layer_top_y + layer_height, pattern_col_x + pattern_col_width, layer_top_y + layer_height)
            
            # Draw depositional environment column borders selectively - only if column is shown
            if depoitional_col_x is not None:
                # Always draw left and right borders
                painter.drawLine(depoitional_col_x, layer_top_y, depoitional_col_x, layer_top_y + layer_height)
                painter.drawLine(depoitional_col_x + depositional_col_width, layer_top_y, depoitional_col_x + depositional_col_width, layer_top_y + layer_height)
                
                # Always draw top and bottom borders for depositional environment column
                painter.drawLine(depoitional_col_x, layer_top_y, depoitional_col_x + depositional_col_width, layer_top_y)
                painter.drawLine(depoitional_col_x, layer_top_y + layer_height, depoitional_col_x + depositional_col_width, layer_top_y + layer_height)

    def draw_wavy_boundary(self, painter, y_position, column_positions, age_gap):
        """
        Draw a wavy line across all columns to indicate an unconformity (age gap).
    
        """
        
        # Save current painter state
        painter.save()
        
        # Set pen for wavy line
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(Qt.NoBrush)
        
        # Calculate total width across all columns
        if not column_positions:
            painter.restore()
            return
        
        leftmost_x = min(pos[0] for pos in column_positions)
        rightmost_x = max(pos[0] + pos[1] for pos in column_positions)
        total_width = rightmost_x - leftmost_x
        
        # Wave parameters
        wave_amplitude = 4 
        wave_frequency = 0.05 
        
        # Create the wavy path
        path = QPainterPath()
        
        # Start the path
        start_x = leftmost_x
        start_y = y_position
        path.moveTo(start_x, start_y)
        
        # Create wavy line by adding small line segments
        num_points = int(total_width / 2) 
        for i in range(1, num_points + 1):
            x = start_x + (i * total_width / num_points)
            # Create sine wave
            wave_offset = wave_amplitude * math.sin(2 * math.pi * wave_frequency * (x - start_x))
            y = start_y + wave_offset
            path.lineTo(x, y)
        
        # Draw the wavy path
        painter.strokePath(path, painter.pen())
        
        # Restore painter state
        painter.restore()
    
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
            elif self.scaling_mode == ScalingMode.THICKNESS:
                self.paint_scaling_mode_2(painter)
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
            # Draw empty rectangle if no ages
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
            # Position from top of layer 
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

                bg_color = age.get('color', '#c8c8c8')

                # Calculate contrasting text color
                text_color = get_contrasting_color_from_hex(bg_color)
                painter.setPen(QPen(text_color, 1))
                
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

                bg_color = age.get('color', '#c8c8c8')

                # Calculate contrasting text color
                text_color = get_contrasting_color_from_hex(bg_color)
                painter.setPen(QPen(text_color, 1))

                # Add age labels if space permits
                font.setPointSize(8)
                painter.setFont(font)
                age_text = f"{overlap_young} Ma"
                painter.drawText(top_rect, Qt.AlignCenter, age_text)

                font.setPointSize(9)
                painter.setFont(font)
                painter.drawText(middle_rect, Qt.AlignCenter, age_name)
                
                # Add age labels if space permits
                font.setPointSize(8)
                painter.setFont(font)
                age_text = f"{overlap_old} Ma"
                painter.drawText(bottom_rect, Qt.AlignCenter, age_text)
            else:
                pass
    
    def draw_depositional_environment_column(self, painter, layer, x, y, width, height):
        layer_dep_env_name = layer.dep_env.display_name
        layer_dep_env_color = layer.dep_env.color

        # Calculate contrasting text color
        
        painter.setBrush(QBrush(QColor(layer_dep_env_color)))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(x, y, width, height)

        text_color = get_contrasting_color_from_hex(layer_dep_env_color) 
        painter.setPen(QPen(text_color, 1))  
        text_rect = QRect(x + 5, y + 5, width - 10, height - 10)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                            f"{layer_dep_env_name.upper()}")

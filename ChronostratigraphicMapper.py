import json
import os
from typing import Dict, List, Tuple, Optional

class ChronostratigraphicMapper:
    """
    A comprehensive chronostratigraphic mapper that loads data from external JSON files.
    This design makes it easy to update geological time scale data without modifying code.
    """
    
    def __init__(self, data_directory: str = "chrono_data"):
        """
        Initialize the mapper with data from JSON files.
        
        Args:
            data_directory (str): Path to directory containing JSON data files
        """
        self.data_directory = data_directory
        self.eras = []
        self.periods = []
        self.epochs = []
        self.ages = []
        self.metadata = {}
        
        # Load data from files
        self._load_all_data()
    
    def _load_all_data(self):
        """Load all chronostratigraphic data from JSON files."""
        try:
            self.eras = self._load_json_file("eras.json")
            self.periods = self._load_json_file("periods.json")
            self.epochs = self._load_json_file("epochs.json")
            self.ages = self._load_json_file("ages.json")
            self.metadata = self._load_json_file("metadata.json")
        except FileNotFoundError:
            # If files don't exist, use built-in data and create files
            print(f"Data files not found in '{self.data_directory}'.")
    
    def _load_json_file(self, filename: str) -> List[Dict]:
        """Load data from a JSON file."""
        filepath = os.path.join(self.data_directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def map_age_to_chronostratigraphy(self, min_age_ma: float, max_age_ma: float) -> Dict[str, List[str]]:
        """
        Maps an age range to all chronostratigraphic units.
        
        Args:
            min_age_ma (float): Minimum age in millions of years ago (younger bound)
            max_age_ma (float): Maximum age in millions of years ago (older bound)
        
        Returns:
            dict: Dictionary containing lists of overlapping units
        
        Raises:
            ValueError: If min_age > max_age or if ages are negative
        """
        # Validate inputs
        if min_age_ma < 0 or max_age_ma < 0:
            raise ValueError("Ages cannot be negative")
        if min_age_ma > max_age_ma:
            raise ValueError("Minimum age cannot be greater than maximum age")
        
        def find_overlapping_units(units_list):
            """Helper function to find overlapping chronostratigraphic units"""
            overlapping = []
            for unit in units_list:
                unit_start = unit['start_age']
                unit_end = unit['end_age']
                # Check if the age range overlaps with this unit
                if min_age_ma < unit_end and max_age_ma > unit_start:
                    overlapping.append(unit)
            return overlapping
        
        # Find overlapping units for each hierarchical level
        result = {
            'eras': find_overlapping_units(self.eras),
            'periods': find_overlapping_units(self.periods),
            'epochs': find_overlapping_units(self.epochs),
            'ages': find_overlapping_units(self.ages)
        }
        
        return result

    def update_data_files(self):
        """Reload data from files (useful after manual edits)."""
        self._load_all_data()
        print("Data reloaded from files.")

# Example usage and testing
if __name__ == "__main__":
    # Create mapper instance
    mapper = ChronostratigraphicMapper()
    
    # Test mapping
    test_cases = [
        (0, 10),      # Recent
        (60, 70),     # K-Pg boundary
        (250, 260),   # P-Tr boundary
        (0, 100),     # Broad Cenozoic
    ]
    
    print("MAPPING EXAMPLES:")
    print("-" * 30)
    
    for min_age, max_age in test_cases:
        result = mapper.map_age_to_chronostratigraphy(min_age, max_age)
        print(f"Age range: {min_age}-{max_age} Ma")
        for level, units in result.items():
            if units:
                print(f"  {level}: {', '.join(units)}")
        print()
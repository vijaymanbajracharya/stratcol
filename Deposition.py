from enum import Enum, auto
from typing import List, Dict, Optional

from enum import Enum

class DepositionalEnvironment(Enum):
    CONTINENTAL = ("Continental", "#CC6600")
    HIGHLAND = ("Highland", "#E49EDD")
    EOLIAN = ("Eolian", "#FBE2D5")
    GLACIAL = ("Glacial", "#F2F2F2")
    LACUSTRINE = ("Lacustrine", "#92D050")
    FLUVIAL = ("Fluvial", "#DAF2D0")
    DELTAIC = ("Deltaic", "#FFFF00")
    COASTAL = ("Coastal", "#F7C7AC")
    OPEN_MARINE = ("Open marine", "#A6C9EC")
    SHALLOW_MARINE_SHELF = ("Shallow marine / Shelf", "#DAE9F8")
    SLOPE_MARINE = ("Slope marine", "#D0D0D0")
    DEEP_MARINE = ("Deep marine", "#4D93D9")
    
    def __init__(self, display_name, color):
        self.display_name = display_name
        self.color = color
    
    def __repr__(self):
        return f"{self.display_name} ({self.color})"

    def to_dict(self):
        return {"name": self.name, "display_name": self.display_name, "color": self.color}
    
    @classmethod
    def from_dict(cls, data: dict) -> Optional['DepositionalEnvironment']:
        """Recreate DepositionalEnvironment from dictionary"""
        if not data:
            return None
        # Prefer lookup by .name (exact enum key)
        if "name" in data:
            return cls[data["name"]]
        
        # Fallback: lookup by display_name
        if "display_name" in data:
            for env in cls:
                if env.display_name == data["display_name"]:
                    return env
        return None

# Usage examples:
if __name__ == "__main__":
    # Access the enum values
    continental = DepositionalEnvironment.CONTINENTAL
    print(f"Name: {continental.display_name}, Color: {continental.color}")
    
    # Iterate through all environments
    for env in DepositionalEnvironment:
        print(f"{env.name}: {env.display_name} - {env.color}")
    
    # Get by enum name
    marine = DepositionalEnvironment.DEEP_MARINE
    print(f"Deep marine color: {marine.color}")

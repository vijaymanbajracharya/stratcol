from enum import Enum, auto
from typing import List, Dict, Optional

class RockType(Enum):
    """Enum for different rock types with associated properties"""

    # Sedimentary rocks
    LIMESTONE = "limestone"
    SANDSTONE = "sandstone"
    SHALE = "shale"
    MUDSTONE = "mudstone"
    CONGLOMERATE = "conglomerate"
    DOLOSTONE = "dolostone"
    COAL = "coal"
    GYPSUM = "gypsum"

    # Igneous rocks
    GRANITE = "granite"
    BASALT = "basalt"

    # Metamorphic rocks
    QUARTZITE = "quartzite"

    # Other/Unknown
    UNKNOWN = "unknown"

class RockCategory(Enum):
    """Rock categories for grouping"""
    SEDIMENTARY = "sedimentary"
    IGNEOUS = "igneous"
    METAMORPHIC = "metamorphic"
    OTHER = "other"

class RockProperties:
    """Class to manage rock type properties and patterns"""
    
    # Rock categories mapping
    CATEGORIES = {
        # Sedimentary
        RockType.LIMESTONE: RockCategory.SEDIMENTARY,
        RockType.SANDSTONE: RockCategory.SEDIMENTARY,
        RockType.SHALE: RockCategory.SEDIMENTARY,
        RockType.MUDSTONE: RockCategory.SEDIMENTARY,
        RockType.CONGLOMERATE: RockCategory.SEDIMENTARY,
        RockType.DOLOSTONE: RockCategory.SEDIMENTARY,
        RockType.COAL: RockCategory.SEDIMENTARY,
        RockType.GYPSUM: RockCategory.SEDIMENTARY,
        RockType.GRANITE: RockCategory.IGNEOUS,
        RockType.BASALT: RockCategory.IGNEOUS,
        RockType.QUARTZITE: RockCategory.METAMORPHIC,
        RockType.UNKNOWN: RockCategory.OTHER,
    }

    PATTERNS = {
        RockType.LIMESTONE: "brick",
        RockType.SANDSTONE: "dots",
        RockType.SHALE: "horizontal_lines",
        RockType.MUDSTONE: "horizontal_lines",
        RockType.CONGLOMERATE: "circles",
        RockType.DOLOSTONE: "brick",
        RockType.COAL: "solid",
        RockType.GYPSUM: "chevron",       
        RockType.GRANITE: "plus",
        RockType.BASALT: "random_dashes",       
        RockType.QUARTZITE: "interlocking",       
        RockType.UNKNOWN: "question_marks",
    }

    @classmethod
    def get_category(cls, rock_type: RockType) -> RockCategory:
        """Get category for a rock type"""
        return cls.CATEGORIES.get(rock_type, RockCategory.OTHER)
    
    @classmethod
    def get_pattern(cls, rock_type: RockType) -> str:
        """Get pattern name for a rock type"""
        return cls.PATTERNS.get(rock_type, "none")
    
    @classmethod
    def get_rocks_by_category(cls, category: RockCategory) -> List[RockType]:
        """Get all rock types in a category"""
        return [rock for rock, cat in cls.CATEGORIES.items() if cat == category]
    
    @classmethod
    def get_display_name(cls, rock_type: RockType) -> str:
        """Get formatted display name for rock type"""
        return rock_type.value.replace('_', ' ').title()
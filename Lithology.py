from enum import Enum, auto
from typing import List, Dict, Optional

class RockType(Enum):
    """Enum for different rock types with associated properties"""

    # Sedimentary rocks
    CONGLOMERATE = "conglomerate"
    BRECCIA = "breccia"
    SANDSTONE = "sandstone"
    SANDSTONE_CROSSBEDDED = "sandstone_crossbedded"
    SANDSTONE_CALCAREOUS = "sandstone_calcareous"
    SILTSTONE = "siltstone"
    SHALE_MUDSTONE = "shale_mudstone"
    SHALE_CARBONACEOUS_BLACK_SHALE = "shale_carbonaceous_black_shale"
    SANDY_SHALE = "sandy_shale"
    SHALEY_SANDSTONE = "shaley_sandstone"
    LIMESTONE = "limestone"
    LIMESTONE_OOLITIC = "limestone_oolitic"
    SANDY_LIMESTONE = "sandy_limestone"
    DOLOSTONE = "dolostone"
    SHALE_CALCAREOUS_MARL = "shale_calcareous_marl"
    CHALK = "chalk"
    COAL = "coal"
    CHERT = "chert"
    INTERBEDDED_SANDSTONE_AND_SHALE = "interbedded_sandstone_and_shale"
    INTERBEDDED_LIMESTONE_AND_SHALE = "interbedded_limestone_and_shale"
    SALT_EVAPORITE = "salt_evaporite"
    OIL_SHALE = "oil_shale"
    TILLITE = "tillite"

    # Igneous rocks
    IGNEOUS_ROCK = "igneous_rock"
    GRANITE = "granite"
    VOLCANIC_ROCK = "volcanic_rock"

    # Metamorphic rocks
    METAMORPHIC_ROCK = "metamorphic_rock"
    GNEISS = "gneiss"
    QUARTZITE = "quartzite"
    SCHIST = "schist"

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
        RockType.CONGLOMERATE: RockCategory.SEDIMENTARY,
        RockType.BRECCIA: RockCategory.SEDIMENTARY,
        RockType.SANDSTONE: RockCategory.SEDIMENTARY,
        RockType.SANDSTONE_CROSSBEDDED: RockCategory.SEDIMENTARY,
        RockType.SANDSTONE_CALCAREOUS: RockCategory.SEDIMENTARY,
        RockType.SILTSTONE: RockCategory.SEDIMENTARY,
        RockType.SHALE_MUDSTONE: RockCategory.SEDIMENTARY,
        RockType.SHALE_CARBONACEOUS_BLACK_SHALE: RockCategory.SEDIMENTARY,
        RockType.SANDY_SHALE: RockCategory.SEDIMENTARY,
        RockType.SHALEY_SANDSTONE: RockCategory.SEDIMENTARY,
        RockType.LIMESTONE: RockCategory.SEDIMENTARY,
        RockType.LIMESTONE_OOLITIC: RockCategory.SEDIMENTARY,
        RockType.SANDY_LIMESTONE: RockCategory.SEDIMENTARY,
        RockType.DOLOSTONE: RockCategory.SEDIMENTARY,
        RockType.SHALE_CALCAREOUS_MARL: RockCategory.SEDIMENTARY,
        RockType.CHALK: RockCategory.SEDIMENTARY,
        RockType.COAL: RockCategory.SEDIMENTARY,
        RockType.CHERT: RockCategory.SEDIMENTARY,
        RockType.INTERBEDDED_SANDSTONE_AND_SHALE: RockCategory.SEDIMENTARY,
        RockType.INTERBEDDED_LIMESTONE_AND_SHALE: RockCategory.SEDIMENTARY,
        RockType.SALT_EVAPORITE: RockCategory.SEDIMENTARY,
        RockType.OIL_SHALE: RockCategory.SEDIMENTARY,
        RockType.TILLITE: RockCategory.SEDIMENTARY,

        RockType.IGNEOUS_ROCK: RockCategory.IGNEOUS,
        RockType.GRANITE: RockCategory.IGNEOUS,
        RockType.VOLCANIC_ROCK: RockCategory.IGNEOUS,

        RockType.METAMORPHIC_ROCK: RockCategory.METAMORPHIC,
        RockType.GNEISS: RockCategory.METAMORPHIC,
        RockType.QUARTZITE: RockCategory.METAMORPHIC,
        RockType.SCHIST: RockCategory.METAMORPHIC,
        RockType.UNKNOWN: RockCategory.OTHER,
    }

    PATTERNS = {
        RockType.CONGLOMERATE: "602",
        RockType.BRECCIA: "605",
        RockType.SANDSTONE: "607",
        RockType.SANDSTONE_CROSSBEDDED: "610",
        RockType.SANDSTONE_CALCAREOUS: "613",
        RockType.SILTSTONE: "616",
        RockType.SHALE_MUDSTONE: "620",
        RockType.SHALE_CARBONACEOUS_BLACK_SHALE: "624",
        RockType.SANDY_SHALE: "619",
        RockType.SHALEY_SANDSTONE: "612",
        RockType.LIMESTONE: "627",
        RockType.LIMESTONE_OOLITIC: "635",
        RockType.SANDY_LIMESTONE: "636",
        RockType.DOLOSTONE: "642",
        RockType.SHALE_CALCAREOUS_MARL: "623",
        RockType.CHALK: "626",
        RockType.COAL: "658",
        RockType.CHERT: "649",
        RockType.INTERBEDDED_SANDSTONE_AND_SHALE: "670",
        RockType.INTERBEDDED_LIMESTONE_AND_SHALE: "677",
        RockType.SALT_EVAPORITE: "668",
        RockType.OIL_SHALE: "625",
        RockType.TILLITE: "681",
        RockType.IGNEOUS_ROCK: "721",
        RockType.GRANITE: "718",
        RockType.VOLCANIC_ROCK: "724",
        RockType.METAMORPHIC_ROCK: "701",
        RockType.GNEISS: "708",
        RockType.QUARTZITE: "702",
        RockType.SCHIST: "705",
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
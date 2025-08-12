from Lithology import RockType, RockCategory, RockProperties
from Deposition import DepositionalEnvironment
from typing import Optional

class Layer:
    def __init__(self, name: str, thickness: float, rock_type: RockType, formation_top: Optional[int] = None, 
                 young_age: Optional[float] = None, old_age: Optional[float] = None, dep_env: Optional[DepositionalEnvironment] = None):
        self.name = name
        self.thickness = thickness
        self.rock_type = rock_type
        self.formation_top = formation_top
        self.young_age = young_age
        self.old_age = old_age
        self.dep_env = dep_env
    
    @property
    def category(self) -> RockCategory:
        """Get the rock category"""
        return RockProperties.get_category(self.rock_type)
    
    @property
    def pattern(self) -> str:
        """Get the geological pattern for this rock type"""
        return RockProperties.get_pattern(self.rock_type)
    
    @property
    def rock_type_display_name(self) -> str:
        """Get formatted display name"""
        return RockProperties.get_display_name(self.rock_type)

    def to_dict(self) -> dict:
        """Convert layer to dictionary for serialization"""
        return {
            'name': self.name,
            'thickness': self.thickness,
            'rock_type': self.rock_type.value,
            'formation_top': self.formation_top,
            'young_age': self.young_age,
            'old_age': self.old_age,
            'depositional_environment': self.dep_env
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Layer':
        """Create layer from dictionary"""
        rock_type = RockType(data['rock_type'])
        
        return cls(
            name=data['name'],
            thickness=data['thickness'],
            rock_type=rock_type,
            formation_top=data['formation_top'],
            young_age=data['young_age'],
            old_age=data['old_age']
        )
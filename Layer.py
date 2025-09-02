from Lithology import RockType, RockCategory, RockProperties
from Deposition import DepositionalEnvironment
from typing import Optional

class Layer:
    def __init__(self, name: str, thickness: float, rock_type: RockType, formation_top: Optional[int] = None, 
                 young_age: Optional[float] = None, old_age: Optional[float] = None, dep_env: Optional[DepositionalEnvironment] = None, visible: Optional[bool] = True,
                 min_thickness: Optional[float] = None, max_thickness: Optional[float] = None):
        self.name = name
        self.thickness = thickness
        self.rock_type = rock_type
        self.formation_top = formation_top
        self.young_age = young_age
        self.old_age = old_age
        self.dep_env = dep_env
        self.visible = visible
        self.min_thickness = min_thickness
        self.max_thickness = max_thickness

    def __repr__(self):
        return str(self.to_dict())
    
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
    
    def toggle_visibility(self) -> bool:
        """Toggle the visibility of the layer and return the new state"""
        self.visible = not self.visible
        return self.visible

    def to_dict(self) -> dict:
        """Convert layer to dictionary for serialization"""
        return {
            'name': self.name,
            'thickness': self.thickness,
            'rock_type': self.rock_type.value,
            'formation_top': self.formation_top,
            'young_age': self.young_age,
            'old_age': self.old_age,
            'dep_env': self.dep_env.to_dict() if self.dep_env else None,
            'visible': self.visible,
            'min_thickness': self.min_thickness,
            'max_thickness': self.max_thickness
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Layer':
        """Create layer from dictionary"""
        rock_type = RockType(data['rock_type'])
        dep_env = DepositionalEnvironment.from_dict(data.get("dep_env"))

        return cls(
            name=data['name'],
            thickness=data['thickness'],
            rock_type=rock_type,
            formation_top=data.get('formation_top'),
            young_age=data.get('young_age'),
            old_age=data.get('old_age'),
            dep_env=dep_env,
            visible=data.get('visible'),
            min_thickness=data['min_thickness'],
            max_thickness=data['max_thickness']
        )
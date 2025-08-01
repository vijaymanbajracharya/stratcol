from Lithology import RockType, RockCategory, RockProperties

class Layer:
    def __init__(self, name: str, thickness: float, rock_type: RockType):
        self.name = name
        self.thickness = thickness
        self.rock_type = rock_type
    
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
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Layer':
        """Create layer from dictionary"""
        rock_type = RockType(data['rock_type'])
        
        return cls(
            name=data['name'],
            thickness=data['thickness'],
            rock_type=rock_type,
        )
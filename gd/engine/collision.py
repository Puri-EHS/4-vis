from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from level import LevelObject

class Collision:
    """
    Wrapper for objects that the player is currently touching, 
    
    Contains the object that the player is touching, and the side of the hitbox that the player  into.
    """
    
    def __init__(self, obj: 'LevelObject', vert_side: str = None, vert_coord: float = None): 
        """
        `obj` must be a dict directly from the `engine.objects.OBJECTS.MASTERLIST` dict.
        
        `vert_side` - optional: which vertical edge of the hitbox the player is touching.
        This should be among the values `["top", "bottom"]`, we dont care about left or right.
        Definition of "touching": within 0-EngineConstants.SOLID_SURFACE_LENIENCY of an edge.
        
        `vert_coord` - req'd if vert_side: the y coordinate of the vertical edge of the hitbox the player is touching.
        This is used to adjust position of the player when they are touching a solid surface.
        
        The existence of this class is mainly to handle solid objects,
        since the player dies on some sides and walks on others (and the safe side depends on gravity)
        """
        
        self.obj: "LevelObject" = obj
        """ the object that the player is colliding with. Position is stored in this obj."""
        
        self.vert_side: Literal["top", "bottom"] | None = vert_side
        """ optional: which vertical edge of the hitbox the player is touching.
        This should be among the values `["top", "bottom"]`, we dont care about left or right.
        Definition of "touching": within 0-EngineConstants.SOLID_SURFACE_LENIENCY of an edge. """
        
        self.vert_coord: float | None = vert_coord
        """ (None if vert_side is None) the y coordinate of the vertical edge of the hitbox the player is touching.
        This is used to adjust position of the player when they are touching a solid surface."""
        
        self.has_been_activated = False
        
    def __str__(self) -> str:
        return f"Collision(with {self.obj.type}@x,y={self.obj.x},{self.obj.y}"
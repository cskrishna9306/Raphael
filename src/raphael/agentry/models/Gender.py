# Import standard packages
from enum import Enum

class Gender(Enum):
    """
    Describes a character's gender as portrayed in the screenplay.
    """
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    UNSPECIFIED = "unspecified"

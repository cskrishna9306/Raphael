# Import standard packages
from enum import Enum

class RolePresence(Enum):
    """
    Describes how central a character is to the screenplay.
    """
    LEAD = "lead"
    SUPPORTING = "supporting"
    MINOR = "minor"
    BACKGROUND = "background"
    EXTRA = "extra"


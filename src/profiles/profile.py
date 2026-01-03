from enum import Enum, auto
from typing import TYPE_CHECKING

# TODO: This is not implemented.
from src.lib.translationhandler import tr

# if TYPE_CHECKING:
# 	from ..lib.installer import Installer

class ProfileType(Enum):
    Server     = "Server"
    Desktop    = "Desktop"
    Minimal    = "Minimal"
	CustomType = "CustomType"
	# WindowMgr  = "Window Manager"

class GreeterType(Enum):
	Lightdm = 'lightdm-gtk-greeter'
	LightdmSlick = 'lightdm-slick-greeter'
	Sddm = 'sddm'
	Gdm = 'gdm'
	Ly = 'ly'
	CosmicSession = 'cosmic-greeter'

class SelectResult(Enum):
	NewSelection = auto()
	SameSelection = auto()
	ResetCurrent = auto()

class Profile:
    def __init__(
        # TODO
    )
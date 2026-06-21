"""ProteinPlate content core.

Single source of truth shared by the website build, the CLI, and any future
API/app. Import render functions or data accessors from here.
"""
from . import data, grocery, render

__all__ = ["data", "grocery", "render"]
__version__ = "0.1.0"

"""Library specific exception definitions."""
from typing import Pattern, Union


class PytubeError(Exception):
    """Base pytube exception that all others inherit.
    
    This is done to not pollute the built-in exceptions, which *colud* result
    in unintended errors being unexpectedly and incorrectly handled within
    implementers code.
    """










class ExtractError(PytubeError):
    """Data extraction based exception."""
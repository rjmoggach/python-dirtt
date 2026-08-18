"""Exception hierarchy for python-dirtt.

Library code raises these instead of printing or exiting; the CLI is
the only layer that converts them into exit codes.
"""

from __future__ import annotations


class DirttError(Exception):
    """Base class for all dirtt errors."""


class TemplateError(DirttError):
    """A template could not be read, substituted, or parsed."""

    def __init__(self, message: str, *, name: str | None = None, position: tuple[int, int] | None = None):
        self.name = name
        self.position = position
        if position:
            message = f"{message} at line {position[0]} column {position[1]}"
        if name:
            message = f"{message} in {name}"
        super().__init__(message)


class BuildError(DirttError):
    """A filesystem operation could not be planned or executed."""

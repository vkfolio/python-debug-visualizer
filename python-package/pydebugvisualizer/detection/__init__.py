"""Data structure detection module.

Provides automatic detection of common data structure patterns
like linked lists, binary trees, and graphs.
"""

from .structure_analyzer import StructureAnalyzer, StructureType, StructureAnalysis

__all__ = [
    "StructureAnalyzer",
    "StructureType",
    "StructureAnalysis",
]

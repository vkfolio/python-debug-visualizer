"""Data extractors for Python Debug Visualizer.

This module provides the extractor infrastructure and built-in extractors
for converting Python data structures into visualization data.
"""

from .base import (
    BaseExtractor,
    ExtractionCandidate,
    ExtractionContext,
    ExtractionResult,
    ExtractorPriority,
)
from .registry import (
    ExtractorRegistry,
    get_registry,
    register_extractor,
)
from .builtin import (
    ListExtractor,
    DictExtractor,
    SetExtractor,
    TupleExtractor,
    StringExtractor,
    FallbackExtractor,
)
from .custom import (
    CustomVisualizationExtractor,
    GetVisualizationDataExtractor,
)

__all__ = [
    # Base classes
    "BaseExtractor",
    "ExtractionCandidate",
    "ExtractionContext",
    "ExtractionResult",
    "ExtractorPriority",
    # Registry
    "ExtractorRegistry",
    "get_registry",
    "register_extractor",
    # Built-in extractors
    "ListExtractor",
    "DictExtractor",
    "SetExtractor",
    "TupleExtractor",
    "StringExtractor",
    "FallbackExtractor",
    # Custom protocol extractors
    "CustomVisualizationExtractor",
    "GetVisualizationDataExtractor",
]

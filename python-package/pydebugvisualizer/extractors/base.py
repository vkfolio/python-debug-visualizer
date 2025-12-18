"""Base classes for data extractors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional


class ExtractorPriority(IntEnum):
    """Priority levels for extractor selection.

    Higher priority extractors are tried first.
    """
    FALLBACK = 0       # Generic fallback (repr/str)
    LOW = 100          # Basic built-in type extractors
    MEDIUM = 200       # Advanced built-in type extractors
    HIGH = 300         # Data science library extractors
    CUSTOM = 400       # User-defined __visualize__() methods
    OVERRIDE = 500     # Direct visualization data (dict with 'kind')


@dataclass
class ExtractionResult:
    """Result from a successful data extraction."""
    extractor_id: str
    extractor_name: str
    priority: int
    data: Dict[str, Any]  # Visualization data (JSON-serializable)


@dataclass
class ExtractionCandidate:
    """A potential extraction that can be applied to a value.

    The extract callable is deferred to allow collecting all candidates
    before actually performing extraction.
    """
    extractor_id: str
    extractor_name: str
    priority: int
    extract: Callable[[], Dict[str, Any]]  # Deferred extraction function


@dataclass
class ExtractionContext:
    """Context passed to extractors during data extraction.

    Contains information about the extraction environment and constraints.
    """
    expression: Optional[str] = None  # The expression being evaluated
    variables_in_scope: Optional[Dict[str, Any]] = None  # Local variables
    preferred_extractor_id: Optional[str] = None  # User preference
    max_depth: int = 10  # Maximum recursion depth for nested structures
    max_items: int = 1000  # Maximum number of items to include

    def __post_init__(self):
        if self.variables_in_scope is None:
            self.variables_in_scope = {}


class BaseExtractor(ABC):
    """Abstract base class for all data extractors.

    Extractors are responsible for converting Python values into
    visualization data (JSON-serializable dictionaries that conform
    to the visualization schema).

    Each extractor should:
    1. Define a unique ID and human-readable name
    2. Implement can_extract() to check if it handles a value type
    3. Implement get_extractions() to return possible visualizations

    Example:
        class MyExtractor(BaseExtractor):
            @property
            def id(self) -> str:
                return "my.extractor"

            @property
            def name(self) -> str:
                return "My Extractor"

            def can_extract(self, value, context):
                return isinstance(value, MyClass)

            def get_extractions(self, value, context):
                return [ExtractionCandidate(
                    extractor_id=self.id,
                    extractor_name=self.name,
                    priority=self.priority,
                    extract=lambda: {"kind": {"text": True}, "text": str(value)}
                )]
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for this extractor.

        Convention: use dotted names like 'builtin.list' or 'datascience.numpy'
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for display in UI."""
        pass

    @property
    def priority(self) -> int:
        """Default priority level for this extractor.

        Can be overridden in subclasses. Higher values = higher priority.
        """
        return ExtractorPriority.MEDIUM

    @abstractmethod
    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        """Check if this extractor can handle the given value.

        Args:
            value: The Python value to potentially extract
            context: Extraction context with constraints

        Returns:
            True if this extractor can produce visualization data for the value
        """
        pass

    @abstractmethod
    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        """Get all possible extractions for the given value.

        An extractor may return multiple candidates representing different
        visualization options (e.g., a list could be visualized as a tree,
        table, or grid).

        Args:
            value: The Python value to extract
            context: Extraction context with constraints

        Returns:
            List of extraction candidates, each with a deferred extract function
        """
        pass

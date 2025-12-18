"""Custom visualization protocol extractor.

Allows Python objects to define their own visualization by implementing
the __visualize__() method.
"""

from typing import Any, Dict, List

from .base import (
    BaseExtractor,
    ExtractionCandidate,
    ExtractionContext,
    ExtractorPriority,
)


class CustomVisualizationExtractor(BaseExtractor):
    """Extractor for objects implementing the __visualize__() protocol.

    Any Python object can define custom visualization by implementing
    the __visualize__() method that returns a visualization data dict.

    Example:
        class BinaryTree:
            def __init__(self, value, left=None, right=None):
                self.value = value
                self.left = left
                self.right = right

            def __visualize__(self):
                def build_node(node):
                    if node is None:
                        return None
                    return {
                        "items": [{"text": str(node.value)}],
                        "children": [
                            build_node(node.left),
                            build_node(node.right)
                        ]
                    }

                return {
                    "kind": {"tree": True},
                    "root": build_node(self)
                }

    The __visualize__() method should return a dict matching one of the
    visualization schemas:
    - {"kind": {"tree": True}, "root": {...}}
    - {"kind": {"graph": True}, "nodes": [...], "edges": [...]}
    - {"kind": {"table": True}, "rows": [...]}
    - {"kind": {"grid": True}, "rows": [...]}
    - {"kind": {"plotly": True}, "data": [...]}
    - {"kind": {"text": True}, "text": "..."}
    - {"kind": {"svg": True}, "text": "..."}
    - {"kind": {"imagePng": True}, "base64Data": "..."}
    - {"kind": {"dotGraph": True}, "text": "..."}
    """

    @property
    def id(self) -> str:
        return "custom.visualize"

    @property
    def name(self) -> str:
        return "Custom __visualize__"

    @property
    def priority(self) -> int:
        return ExtractorPriority.CUSTOM

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        """Check if value has a __visualize__ method."""
        return hasattr(value, '__visualize__') and callable(getattr(value, '__visualize__'))

    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        type_name = type(value).__name__
        return [ExtractionCandidate(
            extractor_id=self.id,
            extractor_name=f"{type_name}.__visualize__()",
            priority=self.priority,
            extract=lambda v=value: self._extract(v)
        )]

    def _extract(self, value: Any) -> Dict:
        """Call the __visualize__ method and return its result."""
        result = value.__visualize__()

        # Validate that result is a dict with 'kind'
        if not isinstance(result, dict):
            raise TypeError(
                f"__visualize__() must return a dict, got {type(result).__name__}"
            )

        if "kind" not in result or not isinstance(result.get("kind"), dict):
            raise ValueError(
                "__visualize__() must return a dict with 'kind' key containing a dict "
                "(e.g., {'kind': {'tree': True}, ...})"
            )

        return result


class GetVisualizationDataExtractor(BaseExtractor):
    """Extractor for objects implementing getVisualizationData() method.

    This provides compatibility with the JavaScript debug visualizer's protocol.
    """

    @property
    def id(self) -> str:
        return "custom.getVisualizationData"

    @property
    def name(self) -> str:
        return "getVisualizationData()"

    @property
    def priority(self) -> int:
        return ExtractorPriority.CUSTOM - 10  # Slightly lower than __visualize__

    def can_extract(self, value: Any, context: ExtractionContext) -> bool:
        """Check if value has a getVisualizationData method."""
        return (
            hasattr(value, 'getVisualizationData') and
            callable(getattr(value, 'getVisualizationData'))
        )

    def get_extractions(
        self,
        value: Any,
        context: ExtractionContext
    ) -> List[ExtractionCandidate]:
        type_name = type(value).__name__
        return [ExtractionCandidate(
            extractor_id=self.id,
            extractor_name=f"{type_name}.getVisualizationData()",
            priority=self.priority,
            extract=lambda v=value: self._extract(v)
        )]

    def _extract(self, value: Any) -> Dict:
        """Call the getVisualizationData method and return its result."""
        result = value.getVisualizationData()

        if not isinstance(result, dict):
            raise TypeError(
                f"getVisualizationData() must return a dict, got {type(result).__name__}"
            )

        if "kind" not in result or not isinstance(result.get("kind"), dict):
            raise ValueError(
                "getVisualizationData() must return a dict with 'kind' key"
            )

        return result

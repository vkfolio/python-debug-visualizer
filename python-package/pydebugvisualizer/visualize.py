"""Main visualization function for Python Debug Visualizer.

This module provides the main entry point for visualizing Python data
during debugging sessions.
"""

import json
from typing import Any, Dict, List, Optional

from .extractors.registry import get_registry
from .extractors.base import ExtractionContext


def visualize(
    value: Any,
    preferred_extractor: Optional[str] = None,
    max_depth: int = 10,
    max_items: int = 1000
) -> str:
    """Visualize a Python value for the debug visualizer.

    This is the main entry point called by the VS Code extension during
    debugging sessions. It extracts visualization data from the value
    and returns it as a JSON string.

    Args:
        value: The Python value to visualize
        preferred_extractor: Optional extractor ID to prefer over auto-selection
        max_depth: Maximum recursion depth for nested structures (default: 10)
        max_items: Maximum number of items to include in collections (default: 1000)

    Returns:
        JSON string containing visualization data and extractor metadata.
        The format is:
        {
            "data": { ... visualization data ... },
            "usedExtractor": {
                "id": "extractor.id",
                "name": "Extractor Name",
                "priority": 200
            },
            "availableExtractors": [
                {"id": "...", "name": "...", "priority": ...},
                ...
            ]
        }

    Example:
        >>> result = visualize([1, 2, 3])
        >>> print(result)  # JSON with tree visualization of the list
    """
    context = ExtractionContext(
        expression=None,
        variables_in_scope={},
        preferred_extractor_id=preferred_extractor,
        max_depth=max_depth,
        max_items=max_items
    )

    registry = get_registry()
    result = registry.extract(value, context)

    if result is None:
        # No extractor found - create a fallback text representation
        return json.dumps({
            "data": {
                "kind": {"text": True},
                "text": repr(value)
            },
            "usedExtractor": {
                "id": "fallback",
                "name": "Fallback (repr)",
                "priority": 0
            },
            "availableExtractors": []
        })

    # Get all available extractors for this value
    available_extractors = _get_available_extractors(value, context)

    # Build the response
    response = {
        "data": result.data,
        "usedExtractor": {
            "id": result.extractor_id,
            "name": result.extractor_name,
            "priority": result.priority
        },
        "availableExtractors": available_extractors
    }

    return json.dumps(response)


def _get_available_extractors(value: Any, context: ExtractionContext) -> List[Dict]:
    """Get list of all available extractors for a value.

    Args:
        value: The value to check
        context: Extraction context

    Returns:
        List of extractor info dicts with id, name, and priority
    """
    registry = get_registry()
    candidates = registry.get_extractions(value, context)
    return [
        {
            "id": c.extractor_id,
            "name": c.extractor_name,
            "priority": c.priority
        }
        for c in candidates
    ]


def get_visualization_data(
    value: Any,
    preferred_extractor: Optional[str] = None,
    max_depth: int = 10,
    max_items: int = 1000
) -> Dict:
    """Get visualization data as a Python dict (not JSON string).

    This is useful when you need the visualization data in Python code
    rather than as a JSON string for the extension.

    Args:
        value: The Python value to visualize
        preferred_extractor: Optional extractor ID to prefer
        max_depth: Maximum recursion depth
        max_items: Maximum number of items

    Returns:
        Dict containing visualization data
    """
    result = visualize(value, preferred_extractor, max_depth, max_items)
    return json.loads(result)

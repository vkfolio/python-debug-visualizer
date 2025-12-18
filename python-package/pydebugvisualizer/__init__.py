"""Python Debug Visualizer - Automatic data structure visualization.

This package provides automatic data structure visualization for Python
during VS Code debugging sessions. It supports:

- Built-in types: list, dict, set, tuple, str
- Data science: NumPy arrays, Pandas DataFrames (with optional dependencies)
- Custom structures: Linked lists, trees, graphs (auto-detected)
- Custom visualization: Objects can define __visualize__() method

Basic Usage:
    During debugging, the VS Code extension calls:
    >>> from pydebugvisualizer import visualize
    >>> result = visualize(my_data)  # Returns JSON string

Custom Visualization:
    Define __visualize__() method on your classes:

    class BinaryTree:
        def __visualize__(self):
            return {
                "kind": {"tree": True},
                "root": self._build_tree_node()
            }

Extending:
    Register custom extractors:

    from pydebugvisualizer import register_extractor, BaseExtractor

    class MyExtractor(BaseExtractor):
        ...

    register_extractor(MyExtractor())
"""

__version__ = "0.1.0"

# Import main function
from .visualize import visualize, get_visualization_data

# Import extractor infrastructure
from .extractors import (
    BaseExtractor,
    ExtractionCandidate,
    ExtractionContext,
    ExtractionResult,
    ExtractorPriority,
    ExtractorRegistry,
    get_registry,
    register_extractor,
)


def _register_default_extractors() -> None:
    """Register all default extractors.

    Called automatically on module import.
    """
    from .extractors.builtin import (
        ListExtractor,
        DictExtractor,
        SetExtractor,
        TupleExtractor,
        StringExtractor,
        FallbackExtractor,
    )
    from .extractors.custom import (
        CustomVisualizationExtractor,
        GetVisualizationDataExtractor,
    )

    registry = get_registry()

    # Register built-in type extractors
    registry.register(ListExtractor())
    registry.register(DictExtractor())
    registry.register(SetExtractor())
    registry.register(TupleExtractor())
    registry.register(StringExtractor())
    registry.register(FallbackExtractor())

    # Register custom protocol extractors
    registry.register(CustomVisualizationExtractor())
    registry.register(GetVisualizationDataExtractor())

    # Register structure detection extractors
    from .extractors.structure_ext import (
        LinkedListExtractor,
        BinaryTreeExtractor,
        NaryTreeExtractor,
        GraphExtractor,
    )
    registry.register(LinkedListExtractor())
    registry.register(BinaryTreeExtractor())
    registry.register(NaryTreeExtractor())
    registry.register(GraphExtractor())

    # Try to register optional data science extractors
    _register_optional_extractors()


def _register_optional_extractors() -> None:
    """Register optional extractors for data science libraries.

    These are registered only if the libraries are available.
    """
    registry = get_registry()

    # NumPy extractor
    try:
        from .extractors.numpy_ext import NumpyExtractor
        registry.register(NumpyExtractor())
    except ImportError:
        pass  # NumPy not installed

    # Pandas extractor
    try:
        from .extractors.pandas_ext import PandasExtractor
        registry.register(PandasExtractor())
    except ImportError:
        pass  # Pandas not installed

    # Matplotlib extractor
    try:
        from .extractors.matplotlib_ext import MatplotlibExtractor
        registry.register(MatplotlibExtractor())
    except ImportError:
        pass  # Matplotlib not installed


# Register default extractors on import
_register_default_extractors()


__all__ = [
    # Version
    "__version__",
    # Main functions
    "visualize",
    "get_visualization_data",
    # Extractor infrastructure
    "BaseExtractor",
    "ExtractionCandidate",
    "ExtractionContext",
    "ExtractionResult",
    "ExtractorPriority",
    "ExtractorRegistry",
    "get_registry",
    "register_extractor",
]

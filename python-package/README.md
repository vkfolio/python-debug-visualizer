# pydebugvisualizer

Python Debug Visualizer - Automatic data structure visualization for VS Code debugging.

## Installation

```bash
pip install pydebugvisualizer
```

For data science support:
```bash
pip install pydebugvisualizer[datascience]
```

## Supported Data Types

### Built-in Types
- `list` - Tree, table (for list of dicts), grid (for 2D lists)
- `dict` - Tree, table (for dict of dicts), key-value table
- `set`, `frozenset` - Grid, tree
- `tuple` - Grid, tree
- `str` - Text with syntax highlighting, JSON parsing

### Data Science (optional)
- **NumPy** `ndarray` - Line plots, heatmaps, grids
- **Pandas** `DataFrame`, `Series` - Tables, line plots
- **Matplotlib** figures - PNG/SVG images

### Custom Data Structures
The analyzer automatically detects:
- Linked lists (singly and doubly linked)
- Binary trees
- N-ary trees
- Graphs

## Custom Visualization Protocol

Define `__visualize__()` on your classes to provide custom visualization:

```python
class BinaryTree:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

    def __visualize__(self):
        def build_node(node):
            if node is None:
                return {"items": [{"text": "∅"}], "children": []}
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
```

## Visualization Schemas

The `__visualize__()` method should return a dict with one of these formats:

### Tree
```python
{
    "kind": {"tree": True},
    "root": {
        "items": [{"text": "Node Label", "emphasis": "style1"}],
        "children": [...]  # Nested tree nodes
    }
}
```

### Graph
```python
{
    "kind": {"graph": True},
    "nodes": [
        {"id": "1", "label": "Node 1", "color": "#ff0000"},
        {"id": "2", "label": "Node 2"}
    ],
    "edges": [
        {"from": "1", "to": "2", "label": "edge"}
    ]
}
```

### Table
```python
{
    "kind": {"table": True},
    "rows": [
        {"col1": "value1", "col2": "value2"},
        {"col1": "value3", "col2": "value4"}
    ]
}
```

### Grid
```python
{
    "kind": {"grid": True},
    "columnLabels": [{"label": "A"}, {"label": "B"}],
    "rows": [
        {"label": "Row 1", "columns": [{"content": "1"}, {"content": "2"}]}
    ]
}
```

### Plotly Chart
```python
{
    "kind": {"plotly": True},
    "data": [{"type": "scatter", "x": [1,2,3], "y": [4,5,6]}],
    "layout": {"title": "My Chart"}
}
```

### Text
```python
{
    "kind": {"text": True},
    "text": "Hello, World!",
    "fileName": "example.py"  # Optional, for syntax highlighting
}
```

### Image (PNG)
```python
{
    "kind": {"imagePng": True},
    "base64Data": "iVBORw0KGgo..."  # Base64 encoded PNG
}
```

### SVG
```python
{
    "kind": {"svg": True},
    "text": "<svg>...</svg>"
}
```

## Extending with Custom Extractors

```python
from pydebugvisualizer import BaseExtractor, register_extractor, ExtractionCandidate, ExtractorPriority

class MyExtractor(BaseExtractor):
    @property
    def id(self):
        return "custom.mytype"

    @property
    def name(self):
        return "My Custom Type"

    @property
    def priority(self):
        return ExtractorPriority.HIGH

    def can_extract(self, value, context):
        return isinstance(value, MyClass)

    def get_extractions(self, value, context):
        return [ExtractionCandidate(
            extractor_id=self.id,
            extractor_name=self.name,
            priority=self.priority,
            extract=lambda: {"kind": {"text": True}, "text": str(value)}
        )]

# Register the extractor
register_extractor(MyExtractor())
```

## License

MIT

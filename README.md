# Python Debug Visualizer

A VS Code extension for visualizing Python data structures during debugging.

## Features

- **Automatic visualization** for Python data types:
  - Built-in: `list`, `dict`, `set`, `tuple`, `str`
  - NumPy: `ndarray` (line plots, heatmaps, grids)
  - Pandas: `DataFrame`, `Series` (tables, plots)
  - Matplotlib: figures (PNG/SVG images)

- **Structure auto-detection**:
  - Linked lists (singly and doubly linked)
  - Binary trees
  - N-ary trees
  - Graphs

- **Custom visualization protocol**:
  - Define `__visualize__()` on your classes

## Installation

### 1. Install the Python package

```bash
pip install pydebugvisualizer

# For data science support:
pip install pydebugvisualizer[datascience]
```

### 2. Install the VS Code extension

Search for "Python Debug Visualizer" in VS Code Extensions.

## Usage

1. Start a Python debug session
2. Set a breakpoint and run your code
3. Press `Shift+F1` with a variable selected, or
4. Run command "Python Debug Visualizer: New View"
5. Enter the expression you want to visualize

## Custom Visualization

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
                "children": [build_node(node.left), build_node(node.right)]
            }
        return {
            "kind": {"tree": True},
            "root": build_node(self)
        }
```

## Project Structure

```
python-debug-visualizer/
├── extension/          # VS Code extension (TypeScript)
├── python-package/     # pip package: pydebugvisualizer
└── webview/           # React UI (optional, for advanced rendering)
```

## Development

### Build the Python package

```bash
cd python-package
pip install -e .
```

### Build the VS Code extension

```bash
cd extension
npm install
npm run compile
```

### Run in development

1. Open the `extension` folder in VS Code
2. Press F5 to launch Extension Development Host
3. Open a Python file and start debugging

## License

MIT

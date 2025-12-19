# Python Debug Visualizer

Visualize Python data structures during debugging - trees, graphs, linked lists, arrays, and more.

## Features

- **Data Structure Visualization**: Lists, dicts, sets, trees, graphs, linked lists
- **Scientific Computing**: NumPy arrays, Pandas DataFrames, Matplotlib plots
- **Pointer Tracking**: Highlight nodes/indices as you step through algorithms
- **Watch Variables**: Display variable values below the visualization
- **Side-by-Side**: Visualize multiple expressions simultaneously (e.g., `tree1, tree2`)
- **Auto-Refresh**: Automatically update visualization on each debug step

## Usage

1. Start debugging your Python code
2. Press `Shift+F1` or run command **"Python Debug Visualizer: New View"**
3. Enter a variable name to visualize (e.g., `root`, `my_list`, `df`)

### Multiple Expressions

Enter comma-separated expressions to view side-by-side:
```
tree1, tree2
```

### Pointer Tracking

Track algorithm pointers like `slow` and `fast` in linked list problems:
1. Expand "Pointer Tracking" section
2. Add pointer variable names
3. Select type: "Object" for trees/linked lists, "Index" for arrays

## Requirements

- Python extension for VS Code
- For full visualization features: `pip install pydebugvisualizer`

## Supported Data Types

| Type | Visualization |
|------|---------------|
| list, tuple, set | Array view with indices |
| dict | Table view |
| Binary trees | Tree graph |
| Linked lists | Node chain |
| NumPy arrays | Grid/heatmap |
| Pandas DataFrame | Table |
| Matplotlib figures | Embedded plot |
| NetworkX graphs | Interactive graph |

## Keyboard Shortcuts

- `Shift+F1`: Visualize selected expression

## Extension Settings

- `pythonDebugVisualizer.maxItems`: Maximum items to display (default: 1000)
- `pythonDebugVisualizer.maxDepth`: Maximum nesting depth (default: 10)
- `pythonDebugVisualizer.autoRefresh`: Auto-refresh on debug step (default: true)

## License

MIT

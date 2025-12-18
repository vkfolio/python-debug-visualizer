"""
Test file for Python Debug Visualizer

How to test:
1. Open this file in VS Code (in the Extension Development Host window)
2. Set a breakpoint on line 50 (the "pass" line at the end)
3. Press F5 to start debugging (select "Python Debugger: Debug Python File")
4. When it stops at the breakpoint, press Shift+F1 with a variable selected
   Or run command: "Python Debug Visualizer: New View"
5. Type a variable name (e.g., "my_list") in the visualizer
"""

# ===================
# Basic Data Types
# ===================

# List
my_list = [1, 2, 3, 4, 5]

# Nested list (2D array)
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]

# List of dictionaries (table-like)
users = [
    {"name": "Alice", "age": 30, "city": "New York"},
    {"name": "Bob", "age": 25, "city": "Boston"},
    {"name": "Charlie", "age": 35, "city": "Chicago"},
]

# Dictionary
my_dict = {
    "name": "Test",
    "values": [1, 2, 3],
    "nested": {
        "a": 1,
        "b": 2
    }
}

# Set
my_set = {1, 2, 3, 4, 5}

# Tuple
my_tuple = (10, 20, 30, 40, 50)

# String
my_string = "Hello, Python Debug Visualizer!"


# ===================
# Custom Class with __visualize__
# ===================

class TreeNode:
    """A simple binary tree node with custom visualization."""

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

    def __visualize__(self):
        """Custom visualization as a tree."""
        def build_node(node):
            if node is None:
                return {
                    "items": [{"text": "null", "emphasis": "style3"}],
                    "children": []
                }
            return {
                "items": [{"text": str(node.value), "emphasis": "style1"}],
                "children": [
                    build_node(node.left),
                    build_node(node.right)
                ]
            }

        return {
            "kind": {"tree": True},
            "root": build_node(self)
        }


class LinkedListNode:
    """A simple linked list node."""

    def __init__(self, value, next=None):
        self.value = value
        self.next = next

    def __visualize__(self):
        """Custom visualization as a graph."""
        nodes = []
        edges = []
        current = self
        idx = 0

        while current is not None:
            node_id = str(idx)
            nodes.append({
                "id": node_id,
                "label": str(current.value)
            })

            if current.next is not None:
                edges.append({
                    "from": node_id,
                    "to": str(idx + 1),
                    "label": "next"
                })

            current = current.next
            idx += 1

        return {
            "kind": {"graph": True},
            "nodes": nodes,
            "edges": edges
        }


# Create a binary tree:
#        5
#       / \
#      3   7
#     / \   \
#    1   4   9

tree = TreeNode(
    5,
    TreeNode(3, TreeNode(1), TreeNode(4)),
    TreeNode(7, None, TreeNode(9))
)

# Create a linked list: 1 -> 2 -> 3 -> 4 -> 5
linked_list = LinkedListNode(1,
    LinkedListNode(2,
        LinkedListNode(3,
            LinkedListNode(4,
                LinkedListNode(5)
            )
        )
    )
)


# ===================
# Auto-Detected Structures (NO __visualize__ needed!)
# ===================

# Simple linked list - auto-detected by 'next' field
class SimpleNode:
    """Simple node - NO __visualize__ method, will be auto-detected!"""
    def __init__(self, val, next=None):
        self.val = val
        self.next = next

auto_linked_list = SimpleNode(10, SimpleNode(20, SimpleNode(30, SimpleNode(40))))

# Simple binary tree - auto-detected by 'left'/'right' fields
class SimpleBinaryTree:
    """Simple tree - NO __visualize__ method, will be auto-detected!"""
    def __init__(self, data, left=None, right=None):
        self.data = data
        self.left = left
        self.right = right

auto_binary_tree = SimpleBinaryTree(
    100,
    SimpleBinaryTree(50, SimpleBinaryTree(25), SimpleBinaryTree(75)),
    SimpleBinaryTree(150, SimpleBinaryTree(125), SimpleBinaryTree(175))
)

# N-ary tree - auto-detected by 'children' field
class FileNode:
    """File system node - NO __visualize__ method, will be auto-detected!"""
    def __init__(self, name, children=None):
        self.name = name
        self.children = children or []

file_tree = FileNode("root", [
    FileNode("src", [
        FileNode("main.py"),
        FileNode("utils.py"),
        FileNode("tests", [
            FileNode("test_main.py"),
            FileNode("test_utils.py")
        ])
    ]),
    FileNode("docs", [
        FileNode("README.md"),
        FileNode("API.md")
    ]),
    FileNode("setup.py")
])


# ===================
# Direct Visualization Data
# ===================

# You can also create visualization data directly as a dict
direct_graph = {
    "kind": {"graph": True},
    "nodes": [
        {"id": "A", "label": "Start", "color": "#4CAF50"},
        {"id": "B", "label": "Process"},
        {"id": "C", "label": "End", "color": "#f44336"},
    ],
    "edges": [
        {"from": "A", "to": "B", "label": "step 1"},
        {"from": "B", "to": "C", "label": "step 2"},
    ]
}

direct_plotly = {
    "kind": {"plotly": True},
    "data": [{
        "type": "bar",
        "x": ["A", "B", "C", "D"],
        "y": [10, 20, 15, 25],
        "name": "Sample Data"
    }],
    "layout": {
        "title": "Sample Bar Chart"
    }
}


# ===================
# SET BREAKPOINT HERE
# ===================
# Put your breakpoint on the next line, then try visualizing:
#
# Built-in types:
#   my_list, matrix, users, my_dict, my_set, my_tuple, my_string
#
# Custom __visualize__ (explicit):
#   tree, linked_list
#
# Auto-detected structures (NO __visualize__ needed!):
#   auto_linked_list  - detected by 'next' field
#   auto_binary_tree  - detected by 'left'/'right' fields
#   file_tree         - detected by 'children' field
#
# Direct visualization data:
#   direct_graph, direct_plotly

print("Ready to visualize! Set a breakpoint above this line.")
pass  # <-- SET BREAKPOINT HERE

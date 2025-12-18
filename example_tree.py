"""
Tree Visualization Example

SETUP:
1. Set breakpoint on line 42 (the return statement)
2. Press F5 to debug
3. Press Shift+F1 to open visualizer
4. Configure:
   - Expression: tree
   - Pointer 1: root  |  Type: Object  |  Color: green
5. Check "Auto-refresh on step"
6. Press F11 (Step Into) to go into recursive calls

IMPORTANT: Select "Object" type (not Index) for tree node tracking!
"""

from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


# Build tree:
#       1
#      / \
#     2   3
#    / \
#   4   5

tree = TreeNode(1,
    TreeNode(2, TreeNode(4), TreeNode(5)),
    TreeNode(3)
)


def maxDepth(root: Optional[TreeNode]) -> int:
    if not root:
        return 0

    left = maxDepth(root.left)   # F11 to step into
    right = maxDepth(root.right)

    return max(left, right) + 1  # <-- BREAKPOINT HERE


print("Starting maxDepth...")
result = maxDepth(tree)
print(f"Max depth: {result}")

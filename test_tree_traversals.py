"""
Test Tree Traversal Visualization - Python Debug Visualizer

This file tests tree visualization and traversal tracking.
Watch the 'current' node highlight as you step through recursive calls!

HOW TO TEST:
1. Open this file in the Extension Development Host window
2. Set a breakpoint on line 75 (inside maxDepth, after recursive calls)
3. Press F5 to start debugging
4. Press Shift+F1 to open visualizer
5. In the visualizer:
   - Type "tree" in the expression input (the original tree root)
   - Expand "Pointer Tracking" section
   - Enter "root" in Pointer 1, select "Object" type (green)
   - Check "Auto-refresh on step"
6. Step through the code (F10/F11) and watch 'root' move through the tree!

IMPORTANT: Use "tree" as the expression (the original root),
           and "root" as the pointer (current node in recursion).
"""

from typing import Optional


class TreeNode:
    """Standard LeetCode-style binary tree node."""
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


# Build a test tree:
#
#         1
#        / \
#       2   3
#      / \   \
#     4   5   6
#    /
#   7
#
# Max depth = 4 (path: 1 -> 2 -> 4 -> 7)

tree = TreeNode(1,
    TreeNode(2,
        TreeNode(4,
            TreeNode(7)
        ),
        TreeNode(5)
    ),
    TreeNode(3,
        None,
        TreeNode(6)
    )
)


class Solution:
    def maxDepth(self, root: Optional[TreeNode]) -> int:
        """
        Find the maximum depth of a binary tree.

        SET BREAKPOINT on the 'return' line below to watch
        which node 'root' points to at each step!
        """
        # Base case: empty tree has depth 0
        if not root:
            return 0

        # Recursive calls - step into these to watch traversal
        left_depth = self.maxDepth(root.left)
        right_depth = self.maxDepth(root.right)

        # SET BREAKPOINT HERE - 'root' shows current node
        return max(left_depth, right_depth) + 1

    def inorderTraversal(self, root: Optional[TreeNode]) -> list:
        """
        Inorder traversal: Left -> Root -> Right

        Watch 'root' move: goes left first, then visits node, then right.
        """
        result = []

        def inorder(node):
            if not node:
                return

            inorder(node.left)   # Go left first
            result.append(node.val)  # Visit node - BREAKPOINT HERE
            inorder(node.right)  # Then go right

        inorder(root)
        return result

    def preorderTraversal(self, root: Optional[TreeNode]) -> list:
        """
        Preorder traversal: Root -> Left -> Right

        Watch 'node' - visits root first, then children.
        """
        result = []

        def preorder(node):
            if not node:
                return

            result.append(node.val)  # Visit root first - BREAKPOINT HERE
            preorder(node.left)
            preorder(node.right)

        preorder(root)
        return result

    def postorderTraversal(self, root: Optional[TreeNode]) -> list:
        """
        Postorder traversal: Left -> Right -> Root

        Watch 'node' - visits children first, then root.
        """
        result = []

        def postorder(node):
            if not node:
                return

            postorder(node.left)
            postorder(node.right)
            result.append(node.val)  # Visit root last - BREAKPOINT HERE

        postorder(root)
        return result

    def levelOrder(self, root: Optional[TreeNode]) -> list:
        """
        Level-order (BFS) traversal.

        Track 'node' to see BFS visit each level.
        """
        if not root:
            return []

        result = []
        queue = [root]

        while queue:
            node = queue.pop(0)  # BREAKPOINT HERE - track 'node'
            result.append(node.val)

            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)

        return result


# Another test tree (BST):
#
#         8
#        / \
#       3   10
#      / \    \
#     1   6    14
#        / \   /
#       4   7 13

bst = TreeNode(8,
    TreeNode(3,
        TreeNode(1),
        TreeNode(6, TreeNode(4), TreeNode(7))
    ),
    TreeNode(10,
        None,
        TreeNode(14, TreeNode(13))
    )
)


print("=" * 60)
print("Tree Traversal Visualization Test")
print("=" * 60)
print()
print("Test Tree Structure:")
print("        1")
print("       / \\")
print("      2   3")
print("     / \\   \\")
print("    4   5   6")
print("   /")
print("  7")
print()
print("Instructions for maxDepth:")
print("1. Set breakpoint on line 75 (the return statement in maxDepth)")
print("2. Open visualizer (Shift+F1)")
print("3. Enter 'tree' as expression (original root)")
print("4. Add pointer: 'root' with Object type (green)")
print("5. Step through (F11 to step into recursion)")
print("6. Watch 'root' highlight move through the tree!")
print()

solution = Solution()

# Run maxDepth - set breakpoint inside to watch recursion
depth = solution.maxDepth(tree)
print(f"Max Depth: {depth}")  # Should be 4
print()

# Try other traversals
print("Traversal Results:")
print(f"  Inorder:   {solution.inorderTraversal(tree)}")    # [7,4,2,5,1,3,6]
print(f"  Preorder:  {solution.preorderTraversal(tree)}")   # [1,2,4,7,5,3,6]
print(f"  Postorder: {solution.postorderTraversal(tree)}")  # [7,4,5,2,6,3,1]
print(f"  Level:     {solution.levelOrder(tree)}")          # [1,2,3,4,5,6,7]
print()
print("Try setting breakpoints in other traversal methods!")
print("Track 'node' (Object type) to see the traversal order.")

# Final breakpoint
pass  # <-- SET BREAKPOINT HERE to explore results

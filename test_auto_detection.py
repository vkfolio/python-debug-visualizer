"""
Test Auto Structure Detection - Python Debug Visualizer

This file tests the AUTO-DETECTION feature. None of these classes
have __visualize__ methods - the visualizer detects the structure
automatically based on field names!

HOW TO TEST:
1. Open this file in the Extension Development Host window
2. Set a breakpoint on line 120 (the "pass" line at the end)
3. Press F5 to start debugging
4. Press Shift+F1 to open visualizer
5. Try typing these variable names:

   LINKED LISTS (detected by 'next' field):
   - simple_list      → 1 → 2 → 3 → 4 → 5
   - long_list        → 1 → 2 → ... → 20

   BINARY TREES (detected by 'left'/'right' fields):
   - bst              → Binary search tree
   - expression_tree  → Math expression: (3 + 5) * 2

   N-ARY TREES (detected by 'children' field):
   - file_system      → Folder structure
   - org_chart        → Company hierarchy
   - html_dom         → HTML-like DOM tree
"""

# ===================
# LINKED LIST EXAMPLES
# ===================

class ListNode:
    """Simple linked list node - auto-detected by 'next' field"""
    def __init__(self, val, next=None):
        self.val = val
        self.next = next

# Simple linked list: 1 → 2 → 3 → 4 → 5
simple_list = ListNode(1, ListNode(2, ListNode(3, ListNode(4, ListNode(5)))))

# Longer linked list
def make_list(n):
    head = ListNode(1)
    current = head
    for i in range(2, n + 1):
        current.next = ListNode(i)
        current = current.next
    return head

long_list = make_list(20)


# ===================
# BINARY TREE EXAMPLES
# ===================

class TreeNode:
    """Binary tree node - auto-detected by 'left'/'right' fields"""
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

# Binary Search Tree:
#         8
#       /   \
#      3     10
#     / \      \
#    1   6      14
#       / \    /
#      4   7  13

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

# Expression tree for: (3 + 5) * 2
#         *
#       /   \
#      +     2
#     / \
#    3   5

expression_tree = TreeNode("*",
    TreeNode("+", TreeNode(3), TreeNode(5)),
    TreeNode(2)
)


# ===================
# N-ARY TREE EXAMPLES
# ===================

class FolderNode:
    """File system node - auto-detected by 'children' field"""
    def __init__(self, name, children=None):
        self.name = name
        self.children = children or []

# File system structure
file_system = FolderNode("project", [
    FolderNode("src", [
        FolderNode("main.py"),
        FolderNode("utils.py"),
        FolderNode("models", [
            FolderNode("user.py"),
            FolderNode("product.py"),
        ])
    ]),
    FolderNode("tests", [
        FolderNode("test_main.py"),
        FolderNode("test_utils.py"),
    ]),
    FolderNode("docs", [
        FolderNode("README.md"),
        FolderNode("API.md"),
    ]),
    FolderNode("requirements.txt"),
    FolderNode("setup.py"),
])


class Person:
    """Org chart node - auto-detected by 'children' field"""
    def __init__(self, name, children=None):
        self.name = name
        self.children = children or []

# Organization chart
org_chart = Person("CEO", [
    Person("CTO", [
        Person("Dev Lead", [
            Person("Developer 1"),
            Person("Developer 2"),
            Person("Developer 3"),
        ]),
        Person("QA Lead", [
            Person("Tester 1"),
            Person("Tester 2"),
        ])
    ]),
    Person("CFO", [
        Person("Accountant"),
        Person("Financial Analyst"),
    ]),
    Person("CMO", [
        Person("Marketing Manager"),
        Person("Sales Lead", [
            Person("Sales Rep 1"),
            Person("Sales Rep 2"),
        ])
    ])
])


class Element:
    """HTML DOM node - auto-detected by 'children' field"""
    def __init__(self, tag, children=None):
        self.tag = tag
        self.children = children or []

# HTML-like DOM tree
html_dom = Element("html", [
    Element("head", [
        Element("title"),
        Element("meta"),
        Element("link"),
    ]),
    Element("body", [
        Element("header", [
            Element("nav", [
                Element("a"),
                Element("a"),
                Element("a"),
            ])
        ]),
        Element("main", [
            Element("section", [
                Element("h1"),
                Element("p"),
                Element("p"),
            ]),
            Element("section", [
                Element("h2"),
                Element("ul", [
                    Element("li"),
                    Element("li"),
                    Element("li"),
                ])
            ])
        ]),
        Element("footer")
    ])
])


# ===================
# SET BREAKPOINT HERE
# ===================
print("Ready! Set breakpoint on next line, then try visualizing:")
print("  simple_list, long_list")
print("  bst, expression_tree")
print("  file_system, org_chart, html_dom")
pass  # <-- SET BREAKPOINT HERE

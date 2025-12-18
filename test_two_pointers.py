"""
Test Two-Pointer Algorithm Visualization - Python Debug Visualizer

This file tests the DYNAMIC VISUALIZATION feature with pointer tracking.
Watch the 'slow' and 'fast' pointers move through the linked list as you step!

HOW TO TEST:
1. Open this file in the Extension Development Host window
2. Set a breakpoint on line 42 (inside the while loop)
3. Press F5 to start debugging
4. Press Shift+F1 to open visualizer
5. In the visualizer:
   - Type "head" in the expression input
   - Expand "Pointer Tracking" section
   - Enter "slow" in Pointer 1 (green)
   - Enter "fast" in Pointer 2 (red)
   - Check "Auto-refresh on step"
6. Step through the code (F10) and watch the pointers move!

The visualization will show:
- Green highlight on the node that 'slow' points to
- Red highlight on the node that 'fast' points to
- Both colors if they point to the same node
"""


# Simple linked list node - will be auto-detected
class Node:
    def __init__(self, val, next=None):
        self.val = val
        self.next = next


def find_middle(head):
    """Find the middle node using slow/fast pointer technique."""
    slow = head
    fast = head

    # SET BREAKPOINT HERE - then step through and watch!
    while fast is not None and fast.next is not None:
        slow = slow.next        # slow moves 1 step
        fast = fast.next.next   # fast moves 2 steps
        # When you step here, the visualizer will update to show
        # where slow and fast are pointing!
        pass  # <-- Good place for breakpoint

    return slow  # slow is now at middle


def has_cycle(head):
    """Detect cycle using Floyd's algorithm (tortoise and hare)."""
    slow = head
    fast = head

    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next

        if slow == fast:
            return True  # Cycle detected!
        pass  # <-- Breakpoint here to watch cycle detection

    return False


def reverse_list(head):
    """Reverse a linked list - watch prev and current pointers."""
    prev = None
    current = head

    while current is not None:
        next_node = current.next  # Save next
        current.next = prev       # Reverse link
        prev = current            # Move prev forward
        current = next_node       # Move current forward
        pass  # <-- Breakpoint here, track 'prev' and 'current'

    return prev


# Create test linked lists
# List: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7
head = Node(1, Node(2, Node(3, Node(4, Node(5, Node(6, Node(7)))))))

# For cycle detection test (uncomment to test)
# cycle_head = Node(1, Node(2, Node(3, Node(4))))
# cycle_head.next.next.next.next = cycle_head.next  # Creates cycle: 4 -> 2

print("=" * 50)
print("Two-Pointer Algorithm Visualization Test")
print("=" * 50)
print()
print("Instructions:")
print("1. Set breakpoint on line 42 (inside find_middle)")
print("2. Open visualizer (Shift+F1)")
print("3. Enter 'head' as the expression")
print("4. Add pointers: 'slow' (green) and 'fast' (red)")
print("5. Enable 'Auto-refresh on step'")
print("6. Step through (F10) and watch the pointers!")
print()
print("Testing find_middle()...")

# Run the algorithm - set breakpoint inside function
middle = find_middle(head)
print(f"Middle node value: {middle.val}")  # Should be 4

print()
print("Done! Try other algorithms too:")
print("- has_cycle() - Floyd's algorithm")
print("- reverse_list() - List reversal")

# Final breakpoint
pass  # <-- SET BREAKPOINT HERE to explore results

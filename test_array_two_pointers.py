"""
Test Array Two-Pointer Algorithm Visualization - Python Debug Visualizer

This file tests the INDEX-BASED pointer tracking for array algorithms.
Watch 'left' and 'right' pointers move through the array as you step!

HOW TO TEST:
1. Open this file in the Extension Development Host window
2. Set a breakpoint on line 40 (inside the while loop)
3. Press F5 to start debugging
4. Press Shift+F1 to open visualizer
5. In the visualizer:
   - Type "nums" in the expression input
   - Expand "Pointer Tracking" section
   - Enter "left" in Pointer 1, select "Index" type (green)
   - Enter "right" in Pointer 2, select "Index" type (red)
   - Check "Auto-refresh on step"
6. Step through the code (F10) and watch the pointers move!

The visualization will show:
- Green highlight on the element at index 'left'
- Red highlight on the element at index 'right'
- Both move inward as the algorithm runs
"""


def two_sum_sorted(nums, target):
    """
    Find if two numbers in a sorted array sum to target.
    Uses two-pointer technique: left starts at beginning, right at end.
    """
    left = 0
    right = len(nums) - 1

    # SET BREAKPOINT HERE - then step through and watch!
    while left < right:
        current_sum = nums[left] + nums[right]

        if current_sum == target:
            print(f"Found! nums[{left}]={nums[left]} + nums[{right}]={nums[right]} = {target}")
            return True
        elif current_sum > target:
            right -= 1  # Sum too large, decrease it
        else:
            left += 1  # Sum too small, increase it

        # Breakpoint here to see pointers move
        pass  # <-- GOOD BREAKPOINT LOCATION

    return False


def binary_search(nums, target):
    """
    Binary search - watch left, right, and mid pointers.
    """
    left = 0
    right = len(nums) - 1

    while left <= right:
        mid = (left + right) // 2
        # Track 'left', 'mid', and 'right' for full visualization
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
        pass  # <-- BREAKPOINT for binary search

    return -1


def partition(nums, low, high):
    """
    Partition function for quicksort - watch i and j pointers.
    """
    pivot = nums[high]
    i = low - 1

    for j in range(low, high):
        if nums[j] <= pivot:
            i += 1
            nums[i], nums[j] = nums[j], nums[i]
        pass  # <-- BREAKPOINT to see i and j move

    nums[i + 1], nums[high] = nums[high], nums[i + 1]
    return i + 1


def reverse_array(nums):
    """
    Reverse array in place using two pointers.
    """
    left = 0
    right = len(nums) - 1

    while left < right:
        nums[left], nums[right] = nums[right], nums[left]
        left += 1
        right -= 1
        pass  # <-- BREAKPOINT to watch swap

    return nums


# Test data
nums = [1, 2, 4, 6, 8, 9, 14, 15]
target = 13  # Looking for 4 + 9 = 13

print("=" * 50)
print("Array Two-Pointer Visualization Test")
print("=" * 50)
print()
print(f"Array: {nums}")
print(f"Target sum: {target}")
print()
print("Instructions:")
print("1. Set breakpoint on line 40 (inside two_sum_sorted)")
print("2. Open visualizer (Shift+F1)")
print("3. Enter 'nums' as the expression")
print("4. Add pointers:")
print("   - 'left' with Index type (green)")
print("   - 'right' with Index type (red)")
print("5. Enable 'Auto-refresh on step'")
print("6. Step through (F10) and watch!")
print()

# Run the algorithm
result = two_sum_sorted(nums, target)
print(f"Result: {result}")

print()
print("Try other algorithms:")
print("- binary_search(nums, 9) - track left, mid, right")
print("- reverse_array([1,2,3,4,5]) - watch elements swap")

# Final breakpoint
pass  # <-- SET BREAKPOINT HERE

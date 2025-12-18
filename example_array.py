"""
Array Two-Pointer Example - Ready to Test!

STEPS:
1. Set breakpoint on line 26 (marked with # <-- BREAKPOINT)
2. Press F5 to debug
3. Press Shift+F1 to open visualizer
4. Enter: nums
5. Add pointer: left (select "Index" type, green)
6. Add pointer: right (select "Index" type, red)
7. Check "Auto-refresh on step"
8. Press F10 (Step Over) to watch pointers move!
"""


nums = [1, 2, 4, 6, 8, 9, 14, 15]
target = 13  # Looking for 4 + 9


def two_sum(nums, target):
    left = 0
    right = len(nums) - 1

    while left < right:
        total = nums[left] + nums[right]

        if total == target:
            return [left, right]  # <-- BREAKPOINT
        elif total > target:
            right -= 1
        else:
            left += 1

    return []


result = two_sum(nums, target)
print(f"Found at indices: {result}")  # [2, 5] -> 4 + 9 = 13

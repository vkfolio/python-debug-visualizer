"""
Maze Solver with Visualization
Run this with debugger, set breakpoint inside backtrack(), and visualize 'vis'
"""
from typing import List, Tuple, Set

def solve_maze():
    # Sample maze: 0 = path, 1 = wall
    maze = [
        [0, 0, 1, 0, 0],
        [1, 0, 1, 0, 1],
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0]
    ]

    start = (0, 0)
    end = (4, 4)

    rows, cols = len(maze), len(maze[0])
    visited: Set[Tuple[int, int]] = set()
    path: List[Tuple[int, int]] = []

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right

    def is_valid(row: int, col: int) -> bool:
        return (0 <= row < rows and
                0 <= col < cols and
                maze[row][col] == 0 and
                (row, col) not in visited)

    def backtrack(row: int, col: int) -> bool:
        # === VISUALIZATION STATE ===
        # Set breakpoint here and visualize 'vis' in the debug visualizer
        vis = {
            "maze": maze,
            "start": start,
            "end": end,
            "path": list(path),
            "visited": visited.copy(),
            "current": (row, col)
        }

        # Base case: reached the goal
        if (row, col) == end:
            path.append((row, col))
            return True

        # Mark as visited and add to path
        visited.add((row, col))
        path.append((row, col))

        # Try all four directions
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if is_valid(new_row, new_col):
                if backtrack(new_row, new_col):
                    return True

        # Backtrack: remove from path
        path.pop()
        return False

    # Start solving
    if maze[start[0]][start[1]] == 1:
        print("Start is a wall!")
        return []

    found = backtrack(start[0], start[1])

    if found:
        print(f"Path found: {path}")
    else:
        print("No path found")

    return path


def solve_maze_bfs():
    """BFS version - finds shortest path"""
    from collections import deque

    maze = [
        [0, 0, 0, 0, 0, 0],
        [1, 1, 0, 1, 1, 0],
        [0, 0, 0, 0, 1, 0],
        [0, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 0],
        [1, 1, 0, 0, 0, 0]
    ]

    start = (0, 0)
    end = (5, 5)

    rows, cols = len(maze), len(maze[0])
    visited: Set[Tuple[int, int]] = set()
    parent = {start: None}
    queue = deque([start])
    visited.add(start)

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def get_path_to(pos):
        """Reconstruct path from start to pos"""
        path = []
        current = pos
        while current is not None:
            path.append(current)
            current = parent.get(current)
        return path[::-1]

    while queue:
        row, col = queue.popleft()

        # === VISUALIZATION STATE ===
        # Set breakpoint here and visualize 'vis'
        vis = {
            "maze": maze,
            "start": start,
            "end": end,
            "path": get_path_to((row, col)),
            "visited": visited.copy(),
            "current": (row, col)
        }

        if (row, col) == end:
            final_path = get_path_to(end)
            print(f"Shortest path found: {final_path}")
            return final_path

        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            new_pos = (new_row, new_col)

            if (0 <= new_row < rows and
                0 <= new_col < cols and
                maze[new_row][new_col] == 0 and
                new_pos not in visited):

                visited.add(new_pos)
                parent[new_pos] = (row, col)
                queue.append(new_pos)

    print("No path found")
    return []


if __name__ == "__main__":
    print("=== DFS Backtracking ===")
    solve_maze()

    print("\n=== BFS Shortest Path ===")
    solve_maze_bfs()

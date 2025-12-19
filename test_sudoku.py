"""
4x4 Mini Sudoku Solver with Visualization
Run with debugger, set breakpoint after 'vis = {...}', and visualize 'vis'
"""
import copy

# Initial board: 0 = empty cell
board = [
    [0, 2, 0, 0],
    [0, 0, 1, 0],
    [2, 0, 0, 0],
    [0, 0, 0, 1]
]

# Store original for visualization (to show which numbers were given)
original_board = copy.deepcopy(board)


def isValid(num, i, j, board):
    """Check if placing 'num' at (i, j) is valid."""
    # Check row
    if num in board[i]:
        return False

    # Check column
    for k in range(4):
        if board[k][j] == num:
            return False

    # Check 2x2 subgrid
    subGridRow = (i // 2) * 2
    subGridCol = (j // 2) * 2

    for m in range(subGridRow, subGridRow + 2):
        for n in range(subGridCol, subGridCol + 2):
            if board[m][n] == num:
                return False

    return True


def solve(board):
    """Solve sudoku using backtracking."""
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                for num in range(1, 5):
                    # === VISUALIZATION STATE ===
                    # Set breakpoint here and visualize 'vis'
                    vis = {
                        "board": [row[:] for row in board],  # Copy current state
                        "original": original_board,
                        "current": (i, j),
                        "trying": num
                    }

                    if isValid(num, i, j, board):
                        board[i][j] = num

                        if solve(board):
                            return True

                        # Backtrack
                        board[i][j] = 0

                return False  # No valid number found

    return True  # All cells filled


def print_board(board):
    """Pretty print the board."""
    print("┌───┬───┬───┬───┐")
    for i, row in enumerate(board):
        print("│", end="")
        for j, cell in enumerate(row):
            val = str(cell) if cell != 0 else " "
            print(f" {val} │", end="")
        print()
        if i < 3:
            if i == 1:
                print("├───┼───┼───┼───┤")
            else:
                print("├───┼───┼───┼───┤")
    print("└───┴───┴───┴───┘")


if __name__ == "__main__":
    print("Initial board:")
    print_board(board)

    print("\nSolving...")
    if solve(board):
        print("\nSolved!")
        print_board(board)
    else:
        print("\nNo solution exists!")

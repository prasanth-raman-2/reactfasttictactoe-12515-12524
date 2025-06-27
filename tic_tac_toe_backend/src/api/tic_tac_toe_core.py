"""
Core game logic and Pydantic models for Tic-Tac-Toe.

Handles board and game state, move validation, win/draw detection, and provides models for FastAPI request/response.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# --- GAME MODELS ---


# PUBLIC_INTERFACE
class Player(str):
    """Type alias for a player symbol ('X' or 'O')."""
    pass


# PUBLIC_INTERFACE
class Move(BaseModel):
    """Request model to make a move on the board."""
    player: Literal["X", "O"] = Field(..., description="The player making the move ('X' or 'O').")
    row: int = Field(..., ge=0, le=2, description="Row index for the move (0, 1, or 2).")
    col: int = Field(..., ge=0, le=2, description="Column index for the move (0, 1, or 2).")


# PUBLIC_INTERFACE
class BoardState(BaseModel):
    """Represents the current state of the Tic-Tac-Toe board."""
    board: List[List[Optional[Literal["X", "O"]]]] = Field(
        ..., description='3x3 game board; cells are "X", "O", or None'
    )


# PUBLIC_INTERFACE
class GameStatus(BaseModel):
    """Response model for game status and state."""
    board: List[List[Optional[Literal["X", "O"]]]] = Field(
        ..., description='3x3 game board; cells are "X", "O", or None'
    )
    current_player: Literal["X", "O"] = Field(
        ..., description='The player whose turn it is ("X" or "O")'
    )
    winner: Optional[Literal["X", "O"]] = Field(
        default=None, description='The winner if the game has ended; otherwise None'
    )
    is_draw: bool = Field(
        ..., description='True if the game is a draw, otherwise False'
    )
    message: Optional[str] = Field(
        default=None, description="Game status or error message"
    )


# --- CORE GAME LOGIC ---


# PUBLIC_INTERFACE
class TicTacToeGame:
    """
    Encapsulates Tic-Tac-Toe board state and implements move logic, win detection, and draw detection.
    """

    def __init__(self, board: Optional[List[List[Optional[str]]]] = None, current_player: Optional[str] = "X"):
        """
        Initialize the game with optional starting board and player.
        """
        if board is None:
            self.board: List[List[Optional[str]]] = [[None for _ in range(3)] for _ in range(3)]
        else:
            self.board = board
        self.current_player = current_player or "X"

    # PUBLIC_INTERFACE
    def make_move(self, row: int, col: int) -> Optional[str]:
        """
        Attempt to place the current player's marker at (row, col).
        Returns error message if move is invalid, or None on success.
        """
        if not (0 <= row < 3 and 0 <= col < 3):
            return "Invalid board position"
        if self.board[row][col] is not None:
            return "Cell is already occupied"
        if self.check_winner() or self.is_draw():
            return "Game is already over"
        self.board[row][col] = self.current_player
        return None

    # PUBLIC_INTERFACE
    def switch_player(self):
        """Switch to the other player."""
        self.current_player = "O" if self.current_player == "X" else "X"

    # PUBLIC_INTERFACE
    def check_winner(self) -> Optional[str]:
        """Check if there is a winner. Returns 'X', 'O', or None."""
        b = self.board
        for mark in ["X", "O"]:
            # Check rows and columns
            for i in range(3):
                if all(cell == mark for cell in b[i]):
                    return mark
                if all(b[j][i] == mark for j in range(3)):
                    return mark
            # Check diagonals
            if all(b[i][i] == mark for i in range(3)):
                return mark
            if all(b[i][2 - i] == mark for i in range(3)):
                return mark
        return None

    # PUBLIC_INTERFACE
    def is_draw(self) -> bool:
        """Check if the game is a draw."""
        if self.check_winner():
            return False
        return all(cell is not None for row in self.board for cell in row)

    # PUBLIC_INTERFACE
    def to_status(self, message: Optional[str] = None) -> GameStatus:
        """
        Create a GameStatus response reflecting the current game state.
        """
        winner = self.check_winner()
        return GameStatus(
            board=self.board,
            current_player=self.current_player,
            winner=winner,
            is_draw=self.is_draw(),
            message=message,
        )

    # PUBLIC_INTERFACE
    @staticmethod
    def from_board_state(board: List[List[Optional[str]]], current_player: Optional[str]) -> "TicTacToeGame":
        """
        Restore game from raw board and current player.
        """
        return TicTacToeGame(board=board, current_player=current_player)


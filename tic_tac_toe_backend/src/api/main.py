from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from uuid import uuid4

from .tic_tac_toe_core import (
    TicTacToeGame,
    Move,
    GameStatus,
    BoardState,
)

app = FastAPI(
    title="Tic Tac Toe Backend API",
    description="Backend API for Tic Tac Toe with endpoints to manage games, moves, state, and history.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Game", "description": "Endpoints to manage game lifecycle and moves"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Status"])
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}

# --- In-Memory Game Store ---
class InMemoryGame:
    """Internal structure to hold each game's logic and move history."""

    def __init__(self, game: TicTacToeGame):
        self.game = game
        self.move_history: List[Move] = []

# Maps game_id (str) to InMemoryGame
game_store: Dict[str, InMemoryGame] = {}

# --- API ENDPOINTS ---

# PUBLIC_INTERFACE
@app.post("/game", response_model=GameStatus, tags=["Game"], summary="Start new game", description="Starts a new Tic Tac Toe game and returns the initial state (game_id is included in the response message field).")
def start_new_game():
    """
    Starts a new Tic Tac Toe game.

    Returns:
        GameStatus: current state, with game_id in 'message'.
    """
    game_id = str(uuid4())
    game = TicTacToeGame()
    game_store[game_id] = InMemoryGame(game=game)
    status = game.to_status(message=game_id)
    return status

# PUBLIC_INTERFACE
@app.post(
    "/game/{game_id}/move",
    response_model=GameStatus,
    tags=["Game"],
    summary="Submit move",
    description="Submit a move for the specified game. Returns state or error."
)
def submit_move(
    game_id: str = Path(..., description="Game ID"),
    move: Move = ...,
):
    """
    Submit a move for the existing game.

    Args:
        game_id (str): The game ID.
        move (Move): The move to apply (player, row, col).

    Returns:
        GameStatus: Updated game state.

    Raises:
        HTTPException: if invalid move, player mismatch, or game not found.
    """
    inmem = game_store.get(game_id)
    if not inmem:
        raise HTTPException(status_code=404, detail="Game not found")
    game = inmem.game

    # Check current player matches move
    if move.player != game.current_player:
        return game.to_status(message=f"It is {game.current_player}'s turn.")

    error = game.make_move(move.row, move.col)
    if error:
        return game.to_status(message=error)

    inmem.move_history.append(move)
    winner = game.check_winner()
    if not winner and not game.is_draw():
        game.switch_player()

    return game.to_status(message="Move accepted")

# PUBLIC_INTERFACE
@app.get(
    "/game/{game_id}",
    response_model=GameStatus,
    tags=["Game"],
    summary="Get game state",
    description="Returns the current state for the specified game.",
)
def get_game_state(
    game_id: str = Path(..., description="Game ID"),
):
    """
    Gets the current state of the specified game.
    Args:
        game_id (str): The game ID.
    Returns:
        GameStatus: The current state.
    Raises:
        HTTPException: If not found.
    """
    inmem = game_store.get(game_id)
    if not inmem:
        raise HTTPException(status_code=404, detail="Game not found")
    return inmem.game.to_status()

# PUBLIC_INTERFACE
@app.get(
    "/game/{game_id}/history",
    response_model=List[Move],
    tags=["Game"],
    summary="Get move history",
    description="Get the chronological list of moves for the game."
)
def get_move_history(
    game_id: str = Path(..., description="Game ID"),
):
    """
    Gets move history for the specified game.

    Args:
        game_id (str): The game ID.

    Returns:
        List[Move]: List of moves in order.
    Raises:
        HTTPException: If not found.
    """
    inmem = game_store.get(game_id)
    if not inmem:
        raise HTTPException(status_code=404, detail="Game not found")
    return inmem.move_history


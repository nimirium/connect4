import copy
from abc import ABC, abstractmethod
import random
import time
from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
import math

import signal
from contextlib import contextmanager

class TimeoutException(Exception):
    pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

@dataclass
class GameState:
    """Represents the current state of the game"""
    board: List[List[str]]
    current_player: str
    last_move: Optional[Tuple[int, int]] = None  # (row, col)

class Player(ABC):
    """Abstract base class that competitors must implement"""
    def __init__(self, symbol: str):
        self.symbol = symbol  # 'X' or 'O'
    
    @abstractmethod
    def get_move(self, state: GameState) -> int:
        """
        Given the current game state, return the column (0-6) to play in
        Must return a valid move (column that isn't full)
        """
        pass

class ConnectFour:
    def __init__(self, player1: Player, player2: Player,
                 columns: int = 14, rows: int = 12, 
                 delay: float = 1.0, animate: bool = True):
        self.columns = columns
        self.rows = rows
        self.board = [[' ' for _ in range(columns)] for _ in range(rows)]
        self.player1 = player1  # X
        self.player2 = player2  # O
        self.current_player = player1
        self.delay = delay  # Delay between moves for visualization
        self.animate = animate
    
    def is_valid_move(self, col: int) -> bool:
        """Check if a move is valid"""
        return 0 <= col < self.columns and self.board[0][col] == ' '
    
    def get_next_row(self, col: int) -> Optional[int]:
        """Get the next available row in the given column"""
        for row in range(self.rows-1, -1, -1):
            if self.board[row][col] == ' ':
                return row
        return None
    
    def make_move(self, col: int) -> Tuple[int, int]:
        """Make a move in the given column"""
        row = self.get_next_row(col)
        if row is None:
            raise ValueError("Invalid move")
        
        if self.animate:
            # Animate the piece falling
            for r in range(row + 1):
                if r > 0:
                    self.board[r-1][col] = ' '
                self.board[r][col] = self.current_player.symbol
                self.display_board()
                time.sleep(0.1)
                if r < row:
                    print("\033[F" * 8)  # Move cursor up 8 lines
        else:
            self.board[row][col] = self.current_player.symbol
            self.display_board()
            
        return row, col
    
    def check_winner(self, row: int, col: int) -> bool:
        """Check if the last move created a winning condition"""
        directions = [
            (0, 1),   # horizontal
            (1, 0),   # vertical
            (1, 1),   # diagonal right
            (1, -1),  # diagonal left
        ]
        
        symbol = self.board[row][col]
        
        for dr, dc in directions:
            count = 1
            
            # Check in positive direction
            r, c = row + dr, col + dc
            while (0 <= r < self.rows and 0 <= c < self.columns and 
                   self.board[r][c] == symbol):
                count += 1
                r, c = r + dr, c + dc
            
            # Check in negative direction
            r, c = row - dr, col - dc
            while (0 <= r < self.rows and 0 <= c < self.columns and 
                   self.board[r][c] == symbol):
                count += 1
                r, c = r - dr, c - dc
            
            if count >= 4:
                return True
        
        return False
    
    def is_board_full(self) -> bool:
        """Check if the board is full (tie game)"""
        return all(cell != ' ' for cell in self.board[0])
    
    def display_board(self):
        """Display the current board state with colors"""
        # ANSI color codes
        RED = '\033[91m'
        YELLOW = '\033[93m'
        RESET = '\033[0m'
        BLUE = '\033[94m'

        # Print column numbers
        print("\n " + BLUE + " ".join((str(i) for i in range(self.columns))) + RESET)
        print(BLUE + "--"*self.columns + RESET)
        
        # Print board with colored pieces
        for row in self.board:
            print(BLUE + "|" + RESET, end="")
            for cell in row:
                if cell == 'X':
                    print(RED + "X" + RESET, end="")
                elif cell == 'O':
                    print(YELLOW + "O" + RESET, end="")
                else:
                    print(" ", end="")
                print(BLUE + "|" + RESET, end="")
            print()
        print(BLUE + "--"*self.columns + RESET)
    
    def play_game(self) -> Optional[Player]:
        """Play a full game, returns the winner or None if tie"""
        while True:
            # Display current state
            if not self.animate:
                print(f"\nPlayer {self.current_player.symbol}'s ({type(self.current_player).__name__}) turn")
                self.display_board()
            
            # Get player's move
            try:
                state = GameState(
                    board=[row[:] for row in self.board],
                    current_player=self.current_player.symbol
                )

                # TODO: Add timeout for player moves
                with time_limit(1):
                    col = self.current_player.get_move(state)

                if not self.is_valid_move(col):
                    print(f"Invalid move by player {self.current_player.symbol}")
                    return self.player1 if self.current_player == self.player2 else self.player2
                    
                row, col = self.make_move(col)
                
            except Exception as e:
                print(f"Error from player {self.current_player.symbol}: {e}")
                return self.player1 if self.current_player == self.player2 else self.player2
            
            # Check for winner
            if self.check_winner(row, col):
                if not self.animate:
                    self.display_board()
                print(f"\nPlayer {self.current_player.symbol} ({type(self.current_player).__name__}) wins!")
                return self.current_player
            
            # Check for tie
            if self.is_board_full():
                if not self.animate:
                    self.display_board()
                print("\nTie game!")
                return None
            
            # Switch players
            self.current_player = self.player2 if self.current_player == self.player1 else self.player1
            
            # Add delay for visualization
            if self.delay:
                time.sleep(self.delay)

# Example player implementations
class RandomPlayer(Player):
    """Makes random valid moves"""
    def get_move(self, state: GameState) -> int:
        columns = len(state.board[0])
        valid_moves = [
            col for col in range(columns)
            if state.board[0][col] == ' '
        ]
        return random.choice(valid_moves)

class SimplePlayer(Player):
    """Looks for winning moves and blocking moves"""
    def get_move(self, state: GameState) -> int:
        columns = len(state.board[0])
        rows = len(state.board)
        
        # First check for winning moves
        for col in range(columns):
            if state.board[0][col] != ' ':
                continue
                
            # Find row where piece would land
            row = rows-1
            while row >= 0 and state.board[row][col] != ' ':
                row -= 1
            
            # Try move
            test_board = [row[:] for row in state.board]
            test_board[row][col] = self.symbol
            
            # Check if this move wins
            if self.check_winner(test_board, row, col):
                return col
        
        # Then check for blocking moves
        opponent = 'O' if self.symbol == 'X' else 'X'
        for col in range(columns):
            if state.board[0][col] != ' ':
                continue
            
            row = rows-1
            while row >= 0 and state.board[row][col] != ' ':
                row -= 1
            
            test_board = [row[:] for row in state.board]
            test_board[row][col] = opponent
            
            if self.check_winner(test_board, row, col):
                return col
        
        # Otherwise, pick random valid move
        valid_moves = [
            col for col in range(columns)
            if state.board[0][col] == ' '
        ]
        return random.choice(valid_moves)
    
    def check_winner(self, board: List[List[str]], row: int, col: int) -> bool:
        """Check if there's a winner on the test board"""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        symbol = board[row][col]
        columns = len(board[0])
        rows = len(board)

        for dr, dc in directions:
            count = 1
            
            # Check positive direction
            r, c = row + dr, col + dc
            while (0 <= r < rows and 0 <= c < columns and 
                   board[r][c] == symbol):
                count += 1
                r, c = r + dr, c + dc
            
            # Check negative direction
            r, c = row - dr, col - dc
            while (0 <= r < rows and 0 <= c < columns and 
                   board[r][c] == symbol):
                count += 1
                r, c = r - dr, c - dc
            
            if count >= 4:
                return True
        return False

class LousyPlayer(Player):
    """A terrible Connect Four player that makes many strategic mistakes"""
    
    def __init__(self, symbol: str):
        super().__init__(symbol)
        self.last_col = None  # Remember last move to make repeated mistakes
        
    def get_move(self, state: GameState) -> int:
        # List of bad strategic decisions
        columns = len(state.board[0])
        rows = len(state.board)

        # 1. If we played before, try to play in the same column
        # (This is terrible because it makes our moves predictable and
        # often leads to playing in full columns)
        if self.last_col is not None and state.board[0][self.last_col] == ' ':
            self.last_col = self.last_col
            return self.last_col
            
        # 2. Avoid center columns at all costs
        # (This is terrible because center control is crucial in Connect Four)
        edge_columns = [0, 1, columns-2,  columns-1]
        for col in edge_columns:
            if state.board[0][col] == ' ':
                self.last_col = col
                return col
                
        # 3. Prefer playing in higher positions
        # (This is terrible because it leaves gaps that opponents can use)
        for row in range(rows):
            for col in range(columns):
                if row > 0 and state.board[row][col] == ' ' and state.board[row-1][col] == ' ':
                    if state.board[0][col] == ' ':  # Make sure column isn't full
                        self.last_col = col
                        return col
                        
        # 4. Ignore obvious winning moves
        # (This is terrible because we'll miss easy wins)
        for col in range(columns):
            if state.board[0][col] != ' ':
                continue
                
            # Find where piece would land
            row = rows-1
            while row >= 0 and state.board[row][col] != ' ':
                row -= 1
                
            # If this would be a winning move, avoid it!
            test_board = [r[:] for r in state.board]
            test_board[row][col] = self.symbol
            if self._would_win(test_board, row, col):
                continue
                
            self.last_col = col
            return col
                
        # 5. If all else fails, pick the first available column
        # (This is terrible because it's predictable and ignores strategy)
        for col in range(columns):
            if state.board[0][col] == ' ':
                self.last_col = col
                return col
                
        return 0  # Should never reach here if game isn't over
        
    def _would_win(self, board: List[List[str]], row: int, col: int) -> bool:
        """Check if a move would win (so we can avoid it!)"""
        symbol = board[row][col]
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        columns = len(board[0])
        rows = len(board)

        for dr, dc in directions:
            count = 1
            
            # Check positive direction
            r, c = row + dr, col + dc
            while (0 <= r < rows and 0 <= c < columns and 
                   board[r][c] == symbol):
                count += 1
                r, c = r + dr, c + dc
            
            # Check negative direction
            r, c = row - dr, col - dc
            while (0 <= r < rows and 0 <= c < columns and 
                   board[r][c] == symbol):
                count += 1
                r, c = r - dr, c - dc
            
            if count >= 4:
                return True
        return False

class SophiesPlayer(Player):
    """Looks for winning moves and blocking moves"""

    def __init__(self, symbol: str):
        super().__init__(symbol)
        self.opponent = "X" if symbol == "O" else "O"

    def get_move(self, state: GameState) -> int:
        columns = len(state.board[0])
        rows = len(state.board)

        # First check for winning moves
        for col in range(columns):
            if state.board[0][col] != ' ':
                continue

            # Find row where piece would land
            row = rows - 1
            while row >= 0 and state.board[row][col] != ' ':
                row -= 1

            # Try move
            test_board = [row[:] for row in state.board]
            test_board[row][col] = self.symbol

            # Check if this move wins
            if self.check_winner(test_board, row, col):
                return col

        valid_moves = [
            col for col in range(columns)
            if state.board[0][col] == ' '
        ]

        # Alpha-Beta Pruning
        best_move = -1
        best_score = -math.inf
        alpha = -math.inf
        beta = math.inf

        for move in valid_moves:
            new_state = self.make_move(state, move, self.symbol)
            score = self.alpha_beta(new_state, depth=3, alpha=alpha, beta=beta, maximizing=False)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

        return best_move

    def alpha_beta(self, state: GameState, depth, alpha, beta, maximizing):
        if depth == 0 or self.is_terminal(state):
            return self.heuristic_evaluation(state.board, self.symbol)

        valid_moves = [col for col in range(len(state.board[0])) if state.board[0][col] == ' ']

        if maximizing:
            max_eval = -math.inf
            for move in valid_moves:
                new_state = self.make_move(state, move, self.symbol)
                eval_score = self.alpha_beta(new_state, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = math.inf
            for move in valid_moves:
                new_state = self.make_move(state, move, self.opponent)
                eval_score = self.alpha_beta(new_state, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval

    def make_move(self, state: GameState, col, symbol):
        """Creates a new board state with a move applied."""
        new_state = copy.deepcopy(state)
        for row in range(len(state.board) - 1, -1, -1):
            if new_state.board[row][col] == ' ':
                new_state.board[row][col] = symbol
                break
        return new_state

    def is_terminal(self, state: GameState):
        """Checks if the game is over (win or draw)."""
        return not any(' ' in row for row in state.board)

    @staticmethod
    def heuristic_evaluation(board, player):
        opponent = "X" if player == "O" else "O"
        rows, cols = len(board), len(board[0])

        def check_sequence(sequence, player):
            """Assign scores based on the number of player pieces in a sequence."""
            score = 0
            if sequence.count(player) == 4:
                score += 1000  # Winning move
            elif sequence.count(player) == 3 and sequence.count(" ") == 1:
                score += 100  # Potential win
            elif sequence.count(player) == 2 and sequence.count(" ") == 2:
                score += 10  # Good setup
            if sequence.count(opponent) == 3 and sequence.count(" ") == 1:
                score -= 100  # Block opponent
            return score

        total_score = 0

        # Check all possible lines (rows, columns, diagonals)
        for r in range(rows):
            for c in range(cols):
                if c + 3 < cols:
                    total_score += check_sequence([board[r][c + i] for i in range(4)], player)  # Horizontal
                if r + 3 < rows:
                    total_score += check_sequence([board[r + i][c] for i in range(4)], player)  # Vertical
                if r + 3 < rows and c + 3 < cols:
                    total_score += check_sequence([board[r + i][c + i] for i in range(4)], player)  # Diagonal /
                if r - 3 >= 0 and c + 3 < cols:
                    total_score += check_sequence([board[r - i][c + i] for i in range(4)], player)  # Diagonal \

        return total_score

    def check_winner(self, board: List[List[str]], row: int, col: int) -> bool:
        """Check if there's a winner on the test board"""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        symbol = board[row][col]
        columns = len(board[0])
        rows = len(board)

        for dr, dc in directions:
            count = 1

            # Check positive direction
            r, c = row + dr, col + dc
            while (0 <= r < rows and 0 <= c < columns and
                   board[r][c] == symbol):
                count += 1
                r, c = r + dr, c + dc

            # Check negative direction
            r, c = row - dr, col - dc
            while (0 <= r < rows and 0 <= c < columns and
                   board[r][c] == symbol):
                count += 1
                r, c = r - dr, c - dc

            if count >= 4:
                return True
        return False

class Tournament:
    """Runs a tournament between multiple Connect Four strategies"""
    def __init__(self, strategy_classes: List[type], games_per_match: int = 10):
        self.strategy_classes = strategy_classes
        self.games_per_match = games_per_match
        self.results = {
            name: {
                'wins': 0,
                'losses': 0,
                'ties': 0,
                'points': 0,  # 3 for win, 1 for tie
                'avg_moves': 0,
                'total_games': 0
            }
            for name in [cls.__name__ for cls in strategy_classes]
        }
        
    def run_tournament(self, display_games: bool = False):
        """Run a full tournament where each strategy plays against all others"""
        total_matches = len(self.strategy_classes) * (len(self.strategy_classes) - 1) * self.games_per_match // 2
        matches_played = 0
        
        print(f"\nStarting tournament with {len(self.strategy_classes)} strategies")
        print(f"Each matchup will play {self.games_per_match} games")
        print(f"Total matches to be played: {total_matches}\n")
        
        # Each strategy plays against every other strategy
        for i, strat1 in enumerate(self.strategy_classes):
            for j, strat2 in enumerate(self.strategy_classes[i+1:], i+1):
                print(f"\nMatch: {strat1.__name__} vs {strat2.__name__}")
                
                # Play multiple games per matchup, alternating who goes first
                for game_num in range(self.games_per_match):
                    matches_played += 1
                    print(f"\rProgress: {matches_played}/{total_matches} matches", end="")
                    
                    # Alternate who goes first
                    if game_num % 2 == 0:
                        player1, player2 = strat1('X'), strat2('O')
                        name1, name2 = strat1.__name__, strat2.__name__
                    else:
                        player1, player2 = strat2('X'), strat1('O')
                        name1, name2 = strat2.__name__, strat1.__name__
                    
                    # Play game
                    game = ConnectFour(player1, player2, delay=0.5 if display_games else 0, animate=display_games)
                    winner = game.play_game()

                    # Update statistics
                    if winner is None:  # Tie
                        self.results[name1]['ties'] += 1
                        self.results[name2]['ties'] += 1
                        self.results[name1]['points'] += 1
                        self.results[name2]['points'] += 1
                    else:
                        winner_name = type(winner).__name__
                        loser_name = name1 if winner_name == name2 else name2
                        self.results[winner_name]['wins'] += 1
                        self.results[winner_name]['points'] += 3
                        self.results[loser_name]['losses'] += 1
                    
                    self.results[name1]['total_games'] += 1
                    self.results[name2]['total_games'] += 1
    
    def display_results(self):
        """Display tournament results in a formatted table"""
        print("\n\nTournament Results:")
        print("-" * 80)
        print(f"{'Strategy':<20} {'Games':<8} {'Wins':<8} {'Losses':<8} {'Ties':<8} {'Points':<8} {'Win %':<8}")
        print("-" * 80)
        
        # Sort by points
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: (x[1]['points'], x[1]['wins']),
            reverse=True
        )
        
        for name, stats in sorted_results:
            total_games = stats['total_games']
            win_percentage = (stats['wins'] / total_games * 100) if total_games > 0 else 0
            print(f"{name:<20} {total_games:<8} {stats['wins']:<8} {stats['losses']:<8} "
                  f"{stats['ties']:<8} {stats['points']:<8} {win_percentage:>6.1f}%")
        print("-" * 80)

if __name__ == "__main__":
    # Create tournament with list of strategies
    strategies = [SophiesPlayer, RandomPlayer, SimplePlayer, LousyPlayer]
    tournament = Tournament(strategies, games_per_match=10)

    # Run tournament
    tournament.run_tournament(display_games=False)  # Set True to watch games

    # Show results
    tournament.display_results()
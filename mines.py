import numpy as np
import time
import random
from collections import defaultdict, deque

class MinesweeperBoard:
    def __init__(self, width, height, num_mines):
        self.width = width
        self.height = height
        self.num_mines = num_mines
        self.board = np.zeros((height, width), dtype=int)  # Hidden board with mine locations
        self.visible = np.zeros((height, width), dtype=bool)  # Whether a cell is visible
        self.marked = np.zeros((height, width), dtype=bool)  # Whether a cell is marked as mine
        self.first_move = True
        self.game_over = False
        self.won = False
        self.place_mines_randomly()
        
    def place_mines_randomly(self):
        # Randomly place mines
        positions = [(i, j) for i in range(self.height) for j in range(self.width)]
        mine_positions = random.sample(positions, self.num_mines)
        
        for i, j in mine_positions:
            self.board[i, j] = -1  # -1 represents a mine
        
        # Calculate numbers for non-mine cells
        for i in range(self.height):
            for j in range(self.width):
                if self.board[i, j] != -1:
                    self.board[i, j] = self.count_adjacent_mines(i, j)
    
    def count_adjacent_mines(self, i, j):
        count = 0
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if 0 <= ni < self.height and 0 <= nj < self.width and self.board[ni, nj] == -1:
                    count += 1
        return count
    
    def get_neighbors(self, i, j):
        neighbors = []
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if 0 <= ni < self.height and 0 <= nj < self.width:
                    neighbors.append((ni, nj))
        return neighbors
    
    def probe(self, i, j):
        # Handle first move - ensure it's not a mine (as mentioned in the paper)
        if self.first_move:
            self.first_move = False
            if self.board[i, j] == -1:
                # Find a non-mine position to swap with
                for ni in range(self.height):
                    for nj in range(self.width):
                        if self.board[ni, nj] != -1:
                            # Swap the mine
                            self.board[i, j] = 0
                            self.board[ni, nj] = -1
                            # Recalculate numbers for affected cells
                            for r, c in self.get_neighbors(i, j) + self.get_neighbors(ni, nj) + [(i, j), (ni, nj)]:
                                if self.board[r, c] != -1:
                                    self.board[r, c] = self.count_adjacent_mines(r, c)
                            break
                    if self.board[i, j] != -1:
                        break
        
        # If it's a mine, game over
        if self.board[i, j] == -1:
            self.game_over = True
            return False
        
        # Mark cell as visible
        self.visible[i, j] = True
        
        # If it's a 0, reveal all adjacent cells
        if self.board[i, j] == 0:
            queue = deque([(i, j)])
            while queue:
                r, c = queue.popleft()
                for nr, nc in self.get_neighbors(r, c):
                    if not self.visible[nr, nc] and not self.marked[nr, nc]:
                        self.visible[nr, nc] = True
                        if self.board[nr, nc] == 0:
                            queue.append((nr, nc))
        
        # Check if game is won
        if np.sum(self.visible) == self.width * self.height - self.num_mines:
            self.won = True
            
        return True
    
    def mark_mine(self, i, j):
        self.marked[i, j] = True
    
    def get_visible_board(self):
        # Return a board as seen by the player
        visible_board = np.full((self.height, self.width), '?', dtype=object)
        for i in range(self.height):
            for j in range(self.width):
                if self.visible[i, j]:
                    visible_board[i, j] = str(self.board[i, j])
                elif self.marked[i, j]:
                    visible_board[i, j] = 'F'
        return visible_board
    
    def print_board(self):
        visible_board = self.get_visible_board()
        
        # Print column indices
        print("  ", end="")
        for j in range(self.width):
            print(f"{j} ", end="")
        print()
        
        # Print rows with indices
        for i in range(self.height):
            print(f"{i} ", end="")
            for j in range(self.width):
                print(f"{visible_board[i, j]} ", end="")
            print()
        print()

class Constraint:
    def __init__(self, variables, value):
        self.variables = set(variables)  # List of (i, j) positions
        self.value = value  # The sum constraint (e.g., sum(variables) = value)
        
    def __repr__(self):
        return f"Sum({self.variables}) = {self.value}"

class CSPStrategy:
    def __init__(self, board):
        self.board = board
        self.constraints = []
        self.moves_made = []
        
    def next_move(self):
        """Determine the next move using the CSP strategy from the research paper"""
        # Step 1: Simplify individual constraints
        self.simplify_constraints()
        
        # Step 2: Simplify constraints by using subset relations
        self.simplify_constraints_by_subset()
        
        # Check if we found any trivial constraints that lead to a certain move
        certain_move = self.find_certain_move()
        if certain_move:
            return certain_move
        
        # Step 3 & 4: Find solutions to constraint subsets and identify certain moves
        coupled_constraints = self.find_coupled_constraints()
        for constraints_subset in coupled_constraints:
            # Step 5: Check for "craps shoot" situations
            craps_shoot = self.check_craps_shoot(constraints_subset)
            if craps_shoot:
                return craps_shoot
            
            # Find all solutions and identify certain moves
            certain_move = self.solve_constraints(constraints_subset)
            if certain_move:
                return certain_move
        
        # Step 6: Make a probabilistic guess among constrained squares
        best_guess = self.make_best_guess()
        if best_guess:
            return best_guess
        
        # Step 7: Choose an unconstrained square
        return self.choose_unconstrained_square()
    
    def simplify_constraints(self):
        """Simplify individual constraints based on known values"""
        new_constraints = []
        
        for constraint in self.constraints:
            # Create new constraint with only unknown variables
            new_vars = []
            new_value = constraint.value
            
            for i, j in constraint.variables:
                if self.board.visible[i, j]:
                    # Known to be clear (not a mine)
                    pass
                elif self.board.marked[i, j]:
                    # Known to be a mine
                    new_value -= 1
                else:
                    # Unknown
                    new_vars.append((i, j))
            
            # Check if the constraint is trivial
            if len(new_vars) == 0:
                continue  # No more unknown variables, discard constraint
            
            # Degenerate cases
            if new_value == 0:
                # All remaining variables must be 0 (not mines)
                for i, j in new_vars:
                    self.board.visible[i, j] = True
                continue  # No constraint needed anymore
            
            if new_value == len(new_vars):
                # All remaining variables must be 1 (mines)
                for i, j in new_vars:
                    self.board.mark_mine(i, j)
                continue  # No constraint needed anymore
            
            # Add the simplified constraint
            new_constraints.append(Constraint(new_vars, new_value))
        
        self.constraints = new_constraints
    
    def simplify_constraints_by_subset(self):
        """Simplify constraints by using subset relations"""
        changed = True
        while changed:
            changed = False
            for i, c1 in enumerate(self.constraints):
                for j, c2 in enumerate(self.constraints):
                    if i != j and c1.variables.issubset(c2.variables):
                        # c1's variables are a subset of c2's variables
                        new_vars = c2.variables - c1.variables
                        new_value = c2.value - c1.value
                        
                        # Replace c2 with the simplified constraint
                        if new_vars:  # If there are remaining variables
                            self.constraints[j] = Constraint(new_vars, new_value)
                            changed = True
                        else:
                            # No variables left, remove constraint
                            self.constraints.pop(j)
                            changed = True
                            break
                
                if changed:
                    break
                    
    def find_certain_move(self):
        """Find moves that can be made with certainty based on trivial constraints"""
        for constraint in self.constraints:
            # If all neighboring variables must be mines
            if constraint.value == len(constraint.variables):
                for i, j in constraint.variables:
                    if not self.board.marked[i, j]:
                        return "mark", (i, j), "This square must contain a mine because all variables in the constraint must be mines."
            
            # If all neighboring variables must be clear
            if constraint.value == 0:
                for i, j in constraint.variables:
                    if not self.board.visible[i, j] and not self.board.marked[i, j]:
                        return "probe", (i, j), "This square must be clear because all variables in the constraint must be empty."
        
        return None
    
    def find_coupled_constraints(self):
        """Find coupled subsets of constraints"""
        # Build a graph of connected constraints (constraints that share variables)
        constraint_graph = defaultdict(set)
        for i, c1 in enumerate(self.constraints):
            for j, c2 in enumerate(self.constraints):
                if i != j and any(v in c2.variables for v in c1.variables):
                    constraint_graph[i].add(j)
        
        # Find connected components
        visited = set()
        coupled_sets = []
        
        for i in range(len(self.constraints)):
            if i not in visited:
                component = []
                queue = deque([i])
                visited.add(i)
                
                while queue:
                    node = queue.popleft()
                    component.append(node)
                    
                    for neighbor in constraint_graph[node]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                
                # Create the coupled constraint set
                coupled_constraints = [self.constraints[idx] for idx in component]
                coupled_sets.append(coupled_constraints)
        
        return coupled_sets
    
    def check_craps_shoot(self, constraints_subset):
        """Check for 'craps shoot' situations where a guess must be made"""
        # Get all variables in this constraint subset
        all_vars = set()
        for constraint in constraints_subset:
            all_vars.update(constraint.variables)
        
        # Check if any of the variables have neighbors that are not in this constraint set
        for i, j in all_vars:
            for ni, nj in self.board.get_neighbors(i, j):
                if not self.board.visible[ni, nj] and not self.board.marked[ni, nj] and (ni, nj) not in all_vars:
                    # Has an unknown neighbor outside the constraint set
                    return None
        
        # If we get here, this is a craps shoot - choose randomly
        i, j = random.choice(list(all_vars))
        return "probe", (i, j), "This is a 'craps shoot' situation where a guess must be made. The chosen square is one of several equally likely possibilities."
    
    def solve_constraints(self, constraints_subset):
        """Find all solutions to a coupled subset of constraints and identify certain moves"""
        # Extract all variables in these constraints
        all_vars = set()
        for constraint in constraints_subset:
            all_vars.update(constraint.variables)
        
        all_vars = list(all_vars)  # Convert to list for consistent ordering
        
        # Initialize counters for each variable
        var_is_mine_count = {var: 0 for var in all_vars}
        total_solutions = 0
        
        # Use backtracking to find all solutions
        def backtrack(var_idx, assigned_vars, remaining_constraints):
            nonlocal total_solutions
            
            if var_idx == len(all_vars):
                # Check if this assignment satisfies all constraints
                for constraint in constraints_subset:
                    mine_count = sum(assigned_vars.get(var, 0) for var in constraint.variables)
                    if mine_count != constraint.value:
                        return
                
                # Valid solution found
                total_solutions += 1
                for var, is_mine in assigned_vars.items():
                    if is_mine:
                        var_is_mine_count[var] += 1
                return
            
            var = all_vars[var_idx]
            
            # Try assigning 0 (not a mine)
            assigned_vars[var] = 0
            backtrack(var_idx + 1, assigned_vars, remaining_constraints)
            
            # Try assigning 1 (mine)
            assigned_vars[var] = 1
            backtrack(var_idx + 1, assigned_vars, remaining_constraints)
            
            # Clean up
            del assigned_vars[var]
        
        # Find all solutions
        backtrack(0, {}, constraints_subset)
        
        # If no solutions found, this is a contradiction (should not happen)
        if total_solutions == 0:
            return None
        
        # Find variables that are definitely mines or definitely clear
        for var in all_vars:
            if var_is_mine_count[var] == 0:  # Definitely clear
                i, j = var
                return "probe", (i, j), "This square must be clear because it's not a mine in any valid solution."
            
            if var_is_mine_count[var] == total_solutions:  # Definitely a mine
                i, j = var
                return "mark", (i, j), "This square must be a mine because it's a mine in all valid solutions."
        
        return None
    
    def make_best_guess(self):
        """Make the best probabilistic guess among constrained squares"""
        # First, calculate probabilities for each constrained variable
        var_probs = {}
        
        for constraints_subset in self.find_coupled_constraints():
            # Extract all variables
            all_vars = set()
            for constraint in constraints_subset:
                all_vars.update(constraint.variables)
            
            all_vars = list(all_vars)
            
            # Count solutions
            var_is_mine_count = {var: 0 for var in all_vars}
            total_solutions = 0
            
            # Use backtracking to find all solutions
            def backtrack(var_idx, assigned_vars):
                nonlocal total_solutions
                
                if var_idx == len(all_vars):
                    # Check if this assignment satisfies all constraints
                    for constraint in constraints_subset:
                        mine_count = sum(assigned_vars.get(var, 0) for var in constraint.variables)
                        if mine_count != constraint.value:
                            return
                    
                    # Valid solution found
                    total_solutions += 1
                    for var, is_mine in assigned_vars.items():
                        if is_mine:
                            var_is_mine_count[var] += 1
                    return
                
                var = all_vars[var_idx]
                
                # Try assigning 0 (not a mine)
                assigned_vars[var] = 0
                backtrack(var_idx + 1, assigned_vars)
                
                # Try assigning 1 (mine)
                assigned_vars[var] = 1
                backtrack(var_idx + 1, assigned_vars)
                
                # Clean up
                del assigned_vars[var]
            
            # Find all solutions
            backtrack(0, {})
            
            if total_solutions > 0:
                # Calculate probabilities
                for var in all_vars:
                    p_mine = var_is_mine_count[var] / total_solutions
                    var_probs[var] = 1 - p_mine  # Probability of being clear
        
        # Calculate probability for unconstrained squares
        total_mines = self.board.num_mines
        marked_mines = np.sum(self.board.marked)
        remaining_mines = total_mines - marked_mines
        
        total_unknown = np.sum(~self.board.visible & ~self.board.marked)
        unconstrained_count = total_unknown - sum(1 for var in var_probs if not self.board.visible[var] and not self.board.marked[var])
        
        if unconstrained_count > 0:
            # Calculate expected mines in constrained squares
            expected_mines_constrained = sum(1 - prob for var, prob in var_probs.items())
            expected_mines_unconstrained = remaining_mines - expected_mines_constrained
            
            # Probability for unconstrained squares
            p_unconstrained_clear = 1 - (expected_mines_unconstrained / unconstrained_count)
            
            # Find the best constrained square
            best_var = None
            best_prob = 0
            
            for var, prob in var_probs.items():
                i, j = var
                if not self.board.visible[i, j] and not self.board.marked[i, j] and prob > best_prob:
                    best_var = var
                    best_prob = prob
            
            # Compare with unconstrained probability
            if best_prob > p_unconstrained_clear and best_var:
                i, j = best_var
                reason = f"This is the best probabilistic guess among constrained squares with a {best_prob:.2f} probability of being clear."
                return "probe", (i, j), reason
        
        return None
    
    def choose_unconstrained_square(self):
        """Choose an unconstrained square to probe"""
        # First, look for corners as suggested in the paper
        corners = [(0, 0), (0, self.board.width-1), (self.board.height-1, 0), (self.board.height-1, self.board.width-1)]
        for i, j in corners:
            if not self.board.visible[i, j] and not self.board.marked[i, j]:
                return "probe", (i, j), "Choosing a corner square because corners have the highest probability of containing a zero."
        
        # Next, look for edges
        edges = []
        for i in range(self.board.height):
            for j in range(self.board.width):
                if (i == 0 or i == self.board.height-1 or j == 0 or j == self.board.width-1) and (i, j) not in corners:
                    edges.append((i, j))
        
        random.shuffle(edges)
        for i, j in edges:
            if not self.board.visible[i, j] and not self.board.marked[i, j]:
                return "probe", (i, j), "Choosing an edge square because edges have a higher probability of containing a zero."
        
        # Finally, look for interior square with max overlap to existing constraints
        interior_squares = []
        max_overlap = -1
        best_square = None
        
        for i in range(1, self.board.height-1):
            for j in range(1, self.board.width-1):
                if not self.board.visible[i, j] and not self.board.marked[i, j]:
                    # Calculate overlap with existing constraints
                    overlap = 0
                    for constraint in self.constraints:
                        neighbors = self.board.get_neighbors(i, j)
                        overlap += len([n for n in neighbors if n in constraint.variables])
                    
                    if overlap > max_overlap:
                        max_overlap = overlap
                        best_square = (i, j)
        
        if best_square:
            return "probe", best_square, "Choosing an interior square with maximum overlap to existing constraints."
        
        # If all else fails, choose a random unconstrained square
        unconstrained = []
        for i in range(self.board.height):
            for j in range(self.board.width):
                if not self.board.visible[i, j] and not self.board.marked[i, j]:
                    unconstrained.append((i, j))
        
        if unconstrained:
            i, j = random.choice(unconstrained)
            return "probe", (i, j), "Choosing a random unconstrained square as a last resort."
        
        return None
    
    def add_constraint_from_move(self, i, j):
        """Add a new constraint after a successful probe"""
        if not self.board.visible[i, j]:
            return
        
        # Get the value at this cell
        value = int(self.board.get_visible_board()[i, j])
        
        # Find unknown neighbors
        unknown_neighbors = []
        for ni, nj in self.board.get_neighbors(i, j):
            if not self.board.visible[ni, nj]:
                unknown_neighbors.append((ni, nj))
        
        # If there are unknown neighbors, add a constraint
        if unknown_neighbors and value > 0:
            self.constraints.append(Constraint(unknown_neighbors, value))
    
    def update_constraints(self):
        """Update constraints after board changes"""
        # Add constraints for all visible cells
        for i in range(self.board.height):
            for j in range(self.board.width):
                if self.board.visible[i, j]:
                    self.add_constraint_from_move(i, j)

def play_minesweeper_ai(width=10, height=10, num_mines=10, delay=1):
    """Play a game of Minesweeper using the CSP AI"""
    board = MinesweeperBoard(width, height, num_mines)
    solver = CSPStrategy(board)
    
    move_count = 0
    
    # Main game loop
    while not board.game_over and not board.won:
        print(f"Current Board (Move {move_count}):")
        board.print_board()
        
        # Get next move from AI
        move = solver.next_move()
        
        if not move:
            print("No valid moves found. Game ended.")
            break
        
        action, (i, j), reason = move
        
        # Execute the move
        if action == "probe":
            print(f"AI decides to probe ({i}, {j})")
            print(f"Reason: {reason}")
            result = board.probe(i, j)
            if not result:
                print("Game over! Hit a mine.")
                board.game_over = True
            solver.update_constraints()
        elif action == "mark":
            print(f"AI decides to mark a mine at ({i}, {j})")
            print(f"Reason: {reason}")
            board.mark_mine(i, j)
        
        move_count += 1
        
        # Add delay between moves
        time.sleep(delay)
    
    # Display final board
    print("\nFinal Board:")
    board.print_board()
    
    if board.won:
        print(f"Game won in {move_count} moves!")
    else:
        print("Game lost!")
    
    return board.won, move_count

# Example usage
if __name__ == "__main__":
    # Easy game: 8x8 with 10 mines
    print("Starting Minesweeper game (8x8 with 10 mines)...")
    won, moves = play_minesweeper_ai(width=8, height=8, num_mines=10, delay=1)
    
    # You can also try:
    # Medium: 16x16 with 40 mines
    # won, moves = play_minesweeper_ai(16, 16, 40, 1)
    
    # Hard/Expert: 30x16 with 99 mines
    # won, moves = play_minesweeper_ai(30, 16, 99, 1)

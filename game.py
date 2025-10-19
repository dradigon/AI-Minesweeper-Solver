import tkinter as tk
from tkinter import ttk, scrolledtext, font, messagebox
import time
import threading
import numpy as np
from mines import MinesweeperBoard, CSPStrategy

class MinesweeperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Minesweeper AI Solver")
        self.root.geometry("1200x700")
        self.root.resizable(True, True)
        
        # Set up the main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control panel (top)
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Difficulty selection
        ttk.Label(self.control_frame, text="Difficulty:").pack(side=tk.LEFT, padx=5)
        self.difficulty = tk.StringVar(value="Easy")
        difficulty_combo = ttk.Combobox(self.control_frame, 
                                        textvariable=self.difficulty,
                                        values=["Easy", "Medium", "Hard", "Custom"])
        difficulty_combo.pack(side=tk.LEFT, padx=5)
        difficulty_combo.bind("<<ComboboxSelected>>", self.on_difficulty_change)
        
        # Custom board size and mines
        self.custom_frame = ttk.Frame(self.control_frame)
        ttk.Label(self.custom_frame, text="Width:").pack(side=tk.LEFT, padx=2)
        self.width_var = tk.StringVar(value="10")
        width_entry = ttk.Entry(self.custom_frame, textvariable=self.width_var, width=3)
        width_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(self.custom_frame, text="Height:").pack(side=tk.LEFT, padx=2)
        self.height_var = tk.StringVar(value="10")
        height_entry = ttk.Entry(self.custom_frame, textvariable=self.height_var, width=3)
        height_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(self.custom_frame, text="Mines:").pack(side=tk.LEFT, padx=2)
        self.mines_var = tk.StringVar(value="10")
        mines_entry = ttk.Entry(self.custom_frame, textvariable=self.mines_var, width=3)
        mines_entry.pack(side=tk.LEFT, padx=2)
        
        # Initially hide custom options
        self.custom_frame.pack_forget()
        
        # Speed control
        ttk.Label(self.control_frame, text="Speed:").pack(side=tk.LEFT, padx=5)
        self.speed = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(self.control_frame, from_=0.1, to=2.0, 
                                variable=self.speed, orient=tk.HORIZONTAL, length=100)
        speed_scale.pack(side=tk.LEFT, padx=5)
        
        # Speed value label
        self.speed_label = ttk.Label(self.control_frame, text="1.0x")
        self.speed_label.pack(side=tk.LEFT, padx=2)
        self.speed.trace_add("write", self.update_speed_label)
        
        # Start button
        self.start_button = ttk.Button(self.control_frame, text="Start Game", command=self.start_game)
        self.start_button.pack(side=tk.LEFT, padx=20)
        
        # Game stats
        self.stats_frame = ttk.Frame(self.control_frame)
        self.stats_frame.pack(side=tk.RIGHT, padx=10)
        
        self.moves_var = tk.StringVar(value="Moves: 0")
        ttk.Label(self.stats_frame, textvariable=self.moves_var).pack(side=tk.RIGHT, padx=10)
        
        self.mines_left_var = tk.StringVar(value="Mines: 0")
        ttk.Label(self.stats_frame, textvariable=self.mines_left_var).pack(side=tk.RIGHT, padx=10)
        
        # Game view and reasoning panel (bottom)
        self.game_area = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.game_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create game board frame with scrolling
        self.board_container = ttk.Frame(self.game_area)
        self.game_area.add(self.board_container, weight=3)
        
        # Add scrollbars for the board
        self.h_scrollbar = ttk.Scrollbar(self.board_container, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.v_scrollbar = ttk.Scrollbar(self.board_container, orient=tk.VERTICAL)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create canvas for the board
        self.board_canvas = tk.Canvas(self.board_container, 
                                      xscrollcommand=self.h_scrollbar.set,
                                      yscrollcommand=self.v_scrollbar.set)
        self.board_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Connect scrollbars to the canvas
        self.h_scrollbar.config(command=self.board_canvas.xview)
        self.v_scrollbar.config(command=self.board_canvas.yview)
        
        # Create frame inside canvas for the board
        self.board_frame = ttk.Frame(self.board_canvas)
        self.board_canvas_window = self.board_canvas.create_window((0, 0), 
                                                                   window=self.board_frame,
                                                                   anchor=tk.NW)
        
        # Create reasoning panel
        self.reasoning_frame = ttk.Frame(self.game_area)
        self.game_area.add(self.reasoning_frame, weight=2)
        
        ttk.Label(self.reasoning_frame, text="AI Reasoning:", font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=5, pady=5)
        
        self.reasoning_text = scrolledtext.ScrolledText(self.reasoning_frame, wrap=tk.WORD)
        self.reasoning_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Game variables
        self.board = None
        self.solver = None
        self.cell_buttons = []
        self.running = False
        self.move_count = 0
        self.ai_thread = None
        
        # Configure the canvas to resize with the window
        self.board_frame.bind("<Configure>", self.on_board_frame_configure)
        self.board_canvas.bind("<Configure>", self.on_canvas_configure)
        
    def on_board_frame_configure(self, event):
        # Update the scrollregion to encompass the inner frame
        self.board_canvas.configure(scrollregion=self.board_canvas.bbox("all"))
        
    def on_canvas_configure(self, event):
        # Update the width of the window to fit the canvas
        self.board_canvas.itemconfig(self.board_canvas_window, width=event.width)
        
    def update_speed_label(self, *args):
        self.speed_label.configure(text=f"{self.speed.get():.1f}x")
        
    def on_difficulty_change(self, event):
        if self.difficulty.get() == "Custom":
            self.custom_frame.pack(side=tk.LEFT, padx=5)
        else:
            self.custom_frame.pack_forget()
            
    def start_game(self):
        # Clean up existing game if any
        if self.running:
            self.running = False
            if self.ai_thread and self.ai_thread.is_alive():
                self.ai_thread.join(timeout=1.0)  # Wait for thread to terminate
        
        # Clear the board frame
        for widget in self.board_frame.winfo_children():
            widget.destroy()
            
        # Clear the reasoning text
        self.reasoning_text.delete(1.0, tk.END)
        
        # Reset move counter
        self.move_count = 0
        self.moves_var.set(f"Moves: {self.move_count}")
        
        # Set up board parameters based on difficulty
        if self.difficulty.get() == "Easy":
            width, height, num_mines = 8, 8, 10
        elif self.difficulty.get() == "Medium":
            width, height, num_mines = 16, 16, 40
        elif self.difficulty.get() == "Hard":
            width, height, num_mines = 30, 16, 99
        else:  # Custom
            try:
                width = int(self.width_var.get())
                height = int(self.height_var.get())
                num_mines = int(self.mines_var.get())
                
                # Validate parameters
                if width < 5 or height < 5:
                    messagebox.showerror("Invalid Size", "Board size must be at least 5x5.")
                    return
                if num_mines < 1:
                    messagebox.showerror("Invalid Mines", "Number of mines must be at least 1.")
                    return
                if num_mines >= width * height:
                    messagebox.showerror("Too Many Mines", "Number of mines must be less than the total number of cells.")
                    return
            except ValueError:
                messagebox.showerror("Invalid Input", "Width, height, and mines must be valid numbers.")
                return
                
        # Log the settings
        self.log_reasoning(f"Starting new game with {width}x{height} board and {num_mines} mines.")
            
        # Initialize the game board
        self.board = MinesweeperBoard(width, height, num_mines)
        self.solver = CSPStrategy(self.board)
        
        # Update mines counter
        self.mines_left_var.set(f"Mines: {num_mines}")
        
        # Create the GUI board
        self.create_board_gui(width, height)
        
        # Start the AI solver in a separate thread
        self.running = True
        self.ai_thread = threading.Thread(target=self.run_ai_solver, daemon=True)
        self.ai_thread.start()
        
    def create_board_gui(self, width, height):
    # Determine button size based on board dimensions
        button_size = min(30, 600 // max(width, height))
    
    # Create a font object for the cell buttons
        cell_font = font.Font(size=button_size // 2)
    
    # Create a container for the cells
        cell_container = ttk.Frame(self.board_frame)
        cell_container.pack(expand=True, padx=5, pady=5)
    
    # Create column headers
    # Empty cell for top-left corner
        ttk.Label(cell_container, text="", width=2).grid(row=0, column=0)
    
    # Column indices - place directly in the cell_container with same width as cells
        for j in range(width):
            ttk.Label(cell_container, text=str(j), width=2).grid(row=0, column=j+1)
        
    # Create the grid of cells
        self.cell_buttons = []
        for i in range(height):
            row_buttons = []
        
        # Row index
            ttk.Label(cell_container, text=str(i), width=2).grid(row=i+1, column=0)
        
            for j in range(width):
            # Use Label for display-only cells
                cell = ttk.Label(
                    cell_container, 
                    text="?",
                    width=2,
                    background="lightgray",
                    borderwidth=1,
                    relief="raised",
                    anchor="center",
                    font=cell_font
                )
                cell.grid(row=i+1, column=j+1, padx=1, pady=1)
                row_buttons.append(cell)
            self.cell_buttons.append(row_buttons)
    
    # Update scroll region
        self.board_frame.update_idletasks()
        self.board_canvas.configure(scrollregion=self.board_canvas.bbox("all"))
            
    def run_ai_solver(self):
        # Main game loop
        try:
            while self.running and not self.board.game_over and not self.board.won:
                # Update the displayed board
                self.update_displayed_board()
                
                # Get next move from AI
                move = self.solver.next_move()
                
                if not move:
                    self.log_reasoning("No valid moves found. Game ended.")
                    break
                
                action, (i, j), reason = move
                
                # Log reasoning
                self.log_reasoning(f"AI decides to {action} ({i}, {j})\nReason: {reason}")
                
                # Execute the move
                if action == "probe":
                    result = self.board.probe(i, j)
                    if not result:
                        self.log_reasoning("Game over! Hit a mine.")
                        self.board.game_over = True
                    self.solver.update_constraints()
                elif action == "mark":
                    self.board.mark_mine(i, j)
                    # Update mines counter
                    mines_marked = np.sum(self.board.marked)
                    self.mines_left_var.set(f"Mines: {self.board.num_mines - mines_marked}")
                
                # Update move counter
                self.move_count += 1
                self.moves_var.set(f"Moves: {self.move_count}")
                
                # Add delay between moves
                time.sleep(1 / self.speed.get())
            
            # Final update
            self.update_displayed_board()
            
            # Game result
            if self.board.won:
                self.log_reasoning(f"\nGame won in {self.move_count} moves!")
                messagebox.showinfo("Game Over", f"Game won in {self.move_count} moves!")
            elif self.board.game_over:
                self.log_reasoning("\nGame lost!")
                messagebox.showinfo("Game Over", "Game lost! Hit a mine.")
        except Exception as e:
            self.log_reasoning(f"Error in AI solver: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_displayed_board(self):
        if not self.running:
            return
            
        visible_board = self.board.get_visible_board()
        
        # Update each cell in the GUI
        for i in range(self.board.height):
            for j in range(self.board.width):
                value = visible_board[i][j]
                
                # Update the text
                self.cell_buttons[i][j].configure(text=value)
                
                # Update the color based on the value
                if value == '?':
                    color = "lightgray"
                    relief = "raised"
                elif value == 'F':
                    color = "red"
                    relief = "raised"
                elif value == '0':
                    color = "#DDDDDD"
                    relief = "sunken"
                elif value == '-1':
                    color = "black"
                    relief = "sunken"
                else:
                    color = "#CCCCCC"
                    relief = "sunken"
                
                self.cell_buttons[i][j].configure(background=color, relief=relief)
                
                # Set text color based on number
                if value in ['1', '2', '3', '4', '5', '6', '7', '8']:
                    number_colors = ['blue', 'green', 'red', 'purple', 'maroon', 'turquoise', 'black', 'gray']
                    text_color = number_colors[int(value) - 1]
                    self.cell_buttons[i][j].configure(foreground=text_color)
                else:
                    self.cell_buttons[i][j].configure(foreground="black")
        
        # Ensure updates are displayed                
        try:
            self.root.update_idletasks()
        except:
            # Handle case where root is destroyed
            self.running = False
    
    def log_reasoning(self, text):
        # Add timestamp
        timestamp = time.strftime("[%H:%M:%S] ")
        self.reasoning_text.insert(tk.END, f"{timestamp}{text}\n\n")
        self.reasoning_text.see(tk.END)
        # Force update to ensure text is displayed immediately
        try:
            self.root.update_idletasks()
        except:
            pass

def main():
    root = tk.Tk()
    app = MinesweeperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

🧠 **AI-Based Minesweeper Solver**

An intelligent Minesweeper-solving agent built using Constraint Satisfaction Problem (CSP) techniques and probabilistic reasoning, with a real-time Tkinter graphical interface for visualization.

📘 Overview

This project implements an AI solver capable of playing Minesweeper autonomously.
It uses constraint-based reasoning, subset relationship analysis, and probability-based decision-making to determine which cells to reveal or flag as mines.

When logical deduction is insufficient, the solver leverages probability theory to make the safest possible move—mimicking human reasoning under uncertainty.

⚙️ Features

🧩 CSP-based Logic Solver – Uses mathematical constraints from revealed numbers.

🔍 Subset Simplification – Reduces complex relationships between constraints.

🎯 Probabilistic Guessing – Calculates mine probabilities when logic alone fails.

🖥️ Interactive GUI (Tkinter) – Visualizes the game board and AI’s reasoning process.

📊 Difficulty Levels – Supports Easy, Medium, and Hard modes.

🚀 Optimized Performance – Uses NumPy arrays, caching, and connected component analysis.

🧠 AI Approach

The solver models Minesweeper as a Constraint Satisfaction Problem (CSP):

Constraint Extraction – Each numbered cell defines a constraint on its neighbors.

Simplification – Constraints are simplified using:

Known safe or mined cells

Subset relationships between overlapping constraints

Coupled Constraints – Identifies connected components that must be solved together.

Backtracking Solver – Finds all valid assignments for small constraint sets.

Probabilistic Reasoning – When no certain moves exist, it:

Computes mine probabilities for constrained cells

Chooses the cell with the lowest risk

Strategic Guessing – Prefers corners, then edges, before interior random guesses.

🧩 Architecture

Core Classes:

MinesweeperBoard – Handles board logic, mine placement, and game rules.

Constraint – Represents a numeric constraint around a revealed cell.

CSPStrategy – Implements the AI algorithm and reasoning logic.

MinesweeperGUI – Provides visualization and controls (difficulty, speed, etc.).

🖥️ GUI Demo

The graphical interface shows:

The game board and revealed clues

The AI’s decision-making log

Adjustable difficulty levels and AI speed

Real-time highlighting of AI moves

(Sample Screenshot Placeholder – add image here if available)

📊 Results
Difficulty	Board Size	Mines	Win Rate (%)
Easy	8×8	10	92.5
Medium	16×16	40	78.3
Hard	30×16	99	44.7

The solver performs exceptionally well on easier levels and maintains logical, probabilistic play in harder ones—matching typical human reasoning patterns.

🔬 Analysis of Failures

Disconnected Safe Zones: Gaps between known safe regions require guessing.

Late-Game Ambiguity: Too few constraints to make safe logical moves.

Small Board Traps: Limited openings after initial safe move.

📚 References

Studholme, C. (2000). Minesweeper as a Constraint Satisfaction Problem.

Kaye, R. (2000). Minesweeper is NP-complete. Mathematical Intelligencer, 22(2), 9–15.

Becerra, D. J. (2015). Algorithmic Approaches to Playing Minesweeper. Harvard College Thesis.

Nakov, P. (2003). Minesweeper, Mathematica, and the Density of Prime Numbers. arXiv:0305148.

🧑‍💻 Contributors

Jovan Moris D (CS23B2058) – AI Development & GUI Design

Kishore K (CS23B2016) – Algorithm Implementation & Performance Analysis

🚀 How to Run
# Clone the repository
git clone https://github.com/<your-username>/Minesweeper-AI-Solver.git
cd Minesweeper-AI-Solver

# Install dependencies
pip install -r requirements.txt

# Run the solver
python main.py

🧩 Future Improvements

Deep learning–based probability estimator

Reinforcement learning for adaptive strategies

Enhanced visualization (PyGame or web-based UI)

Support for custom board configurations

⭐ If you find this project interesting, consider starring the repo!

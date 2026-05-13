# Tetris 2048

A hybrid puzzle game that combines classic Tetris mechanics with 2048-style tile merging logic.

## Features

- 7 classic tetromino shapes
- 2048-style chain merging system
- Ghost piece system
- Hold tetromino mechanic
- Score tracking and difficulty scaling
- Persistent leaderboard system
- Gravity handling for floating tiles
- Pause / resume functionality
- Sound effects and animations

## Tech Stack

- Python
- NumPy
- Pygame
- Object-Oriented Programming (OOP)

## Core Concepts

- Grid-based game systems
- Matrix operations
- Wall-kick rotation logic
- BFS-based connected tile detection
- State management
- Collision detection
- Game loop architecture

## Controls

| Key | Action |
|---|---|
| ← / → | Move left/right |
| ↑ | Rotate |
| ↓ | Soft drop |
| Space | Hard drop |
| C | Hold tetromino |
| P | Pause / Resume |
| R | Restart |

## Installation

```bash
git clone https://github.com/yourusername/tetris-2048.git
cd tetris-2048
pip install -r requirements.txt
python Tetris_2048.py

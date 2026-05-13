from tile import Tile
from point import Point
import copy as cp
import random
import numpy as np


class Tetromino:
   # (col, row) positions of tiles within the tile_matrix
   # row 0 = top of matrix, increases downward
   SHAPES = {
      'I': [(0, 1), (1, 1), (2, 1), (3, 1)],  # 4-wide, 2-tall
      'O': [(0, 0), (0, 1), (1, 0), (1, 1)],  # 2x2
      'Z': [(0, 0), (1, 0), (1, 1), (2, 1)],  # 3-wide, 2-tall
      'S': [(1, 0), (2, 0), (0, 1), (1, 1)],  # 3-wide, 2-tall
      'T': [(0, 1), (1, 0), (1, 1), (2, 1)],  # 3-wide, 2-tall
      # FIX: L and J shapes were wrong in original code.
      # L: vertical bar on left, foot sticks right at bottom
      'L': [(0, 0), (0, 1), (0, 2), (1, 2)],  # 2-wide, 3-tall
      # J: vertical bar on right, foot sticks left at bottom
      'J': [(1, 0), (1, 1), (0, 2), (1, 2)],  # 2-wide, 3-tall
   }
   SIZES = {
      'I': (2, 4), 'O': (2, 2), 'Z': (2, 3),
      'S': (2, 3), 'T': (2, 3), 'L': (3, 2), 'J': (3, 2),
   }

   grid_height, grid_width = None, None

   def __init__(self, type):
      self.type = type
      rows, cols = self.SIZES[type]
      self.tile_matrix = np.full((rows, cols), None)
      for col_index, row_index in self.SHAPES[type]:
         self.tile_matrix[row_index][col_index] = Tile()
      self.bottom_left_cell = Point()
      self.reset_position()

   def reset_position(self):
      cols = len(self.tile_matrix[0])
      self.bottom_left_cell.y = Tetromino.grid_height - 1
      self.bottom_left_cell.x = random.randint(0, max(0, Tetromino.grid_width - cols))

   def copy(self):
      """Return a deep copy of this tetromino (used for ghost piece)."""
      clone = Tetromino(self.type)
      clone.tile_matrix = np.full((len(self.tile_matrix), len(self.tile_matrix[0])), None)
      for row in range(len(self.tile_matrix)):
         for col in range(len(self.tile_matrix[0])):
            if self.tile_matrix[row][col] is not None:
               clone.tile_matrix[row][col] = cp.deepcopy(self.tile_matrix[row][col])
      clone.bottom_left_cell = cp.copy(self.bottom_left_cell)
      return clone

   def get_cell_position(self, row, col):
      """Return the grid (x, y) coordinate for tile_matrix[row][col]."""
      n_rows = len(self.tile_matrix)
      position = Point()
      position.x = self.bottom_left_cell.x + col
      position.y = self.bottom_left_cell.y + (n_rows - 1) - row
      return position

   def get_min_bounded_tile_matrix(self, return_position=False):
      """Return a tightly-cropped copy of the tile matrix."""
      n_rows = len(self.tile_matrix)
      n_cols = len(self.tile_matrix[0])
      min_row, max_row = n_rows - 1, 0
      min_col, max_col = n_cols - 1, 0
      for row in range(n_rows):
         for col in range(n_cols):
            if self.tile_matrix[row][col] is not None:
               min_row = min(min_row, row)
               max_row = max(max_row, row)
               min_col = min(min_col, col)
               max_col = max(max_col, col)
      copy = np.full((max_row - min_row + 1, max_col - min_col + 1), None)
      for row in range(min_row, max_row + 1):
         for col in range(min_col, max_col + 1):
            if self.tile_matrix[row][col] is not None:
               copy[row - min_row][col - min_col] = cp.deepcopy(self.tile_matrix[row][col])
      if not return_position:
         return copy
      blc_position = cp.copy(self.bottom_left_cell)
      blc_position.translate(min_col, (n_rows - 1) - max_row)
      return copy, blc_position

   def draw(self, ghost=False, landing_scale=1.0):
      n_rows = len(self.tile_matrix)
      n_cols = len(self.tile_matrix[0])
      for row in range(n_rows):
         for col in range(n_cols):
            if self.tile_matrix[row][col] is not None:
               position = self.get_cell_position(row, col)
               if position.y < Tetromino.grid_height:
                  if ghost:
                     self.tile_matrix[row][col].draw_ghost(position)
                  else:
                     self.tile_matrix[row][col].draw(position, length=landing_scale)

   def rotate(self, game_grid):
      """Rotate 90° clockwise with wall-kick. Returns True if successful."""
      n_rows = len(self.tile_matrix)
      n_cols = len(self.tile_matrix[0])
      rotated = np.full((n_cols, n_rows), None)
      for row in range(n_rows):
         for col in range(n_cols):
            if self.tile_matrix[row][col] is not None:
               rotated[col][n_rows - 1 - row] = cp.deepcopy(self.tile_matrix[row][col])

      old_matrix = self.tile_matrix
      old_blc = cp.copy(self.bottom_left_cell)
      self.tile_matrix = rotated
      self._fix_position_after_rotation(game_grid)

      if self._is_valid_position(game_grid):
         return True

      # Wall-kick: try small horizontal nudges
      for kick in (-1, 1, -2, 2):
         self.bottom_left_cell.x += kick
         if self._is_valid_position(game_grid):
            return True
         self.bottom_left_cell.x -= kick

      # Revert if no valid position found
      self.tile_matrix = old_matrix
      self.bottom_left_cell = old_blc
      return False

   def _fix_position_after_rotation(self, game_grid):
      """Clamp x position so the rotated piece stays inside the grid."""
      n_cols = len(self.tile_matrix[0])
      if self.bottom_left_cell.x < 0:
         self.bottom_left_cell.x = 0
      if self.bottom_left_cell.x + n_cols > Tetromino.grid_width:
         self.bottom_left_cell.x = Tetromino.grid_width - n_cols

   def _is_valid_position(self, game_grid):
      """Return True if all tiles are in-bounds and not colliding."""
      n_rows = len(self.tile_matrix)
      n_cols = len(self.tile_matrix[0])
      for row in range(n_rows):
         for col in range(n_cols):
            if self.tile_matrix[row][col] is not None:
               pos = self.get_cell_position(row, col)
               if pos.x < 0 or pos.x >= Tetromino.grid_width:
                  return False
               if pos.y < 0:
                  return False
               if game_grid.is_occupied(pos.y, pos.x):
                  return False
      return True

   def move(self, direction, game_grid):
      if not self.can_be_moved(direction, game_grid):
         return False
      if direction == 'left':
         self.bottom_left_cell.x -= 1
      elif direction == 'right':
         self.bottom_left_cell.x += 1
      else:
         self.bottom_left_cell.y -= 1
      return True

   def hard_drop(self, game_grid):
      """Drop to lowest valid position. Returns number of rows dropped."""
      distance = 0
      while self.can_be_moved('down', game_grid):
         self.bottom_left_cell.y -= 1
         distance += 1
      return distance

   def can_be_moved(self, direction, game_grid):
      """Return True if moving one step in direction is legal."""
      n_rows = len(self.tile_matrix)
      n_cols = len(self.tile_matrix[0])

      if direction == 'left':
         # FIX: original code had a broken loop structure where the left/right
         # checks shared one loop body using if/else on direction, causing
         # wrong tile to be checked. Now separated into clear, correct logic.
         for row in range(n_rows):
            for col in range(n_cols):          # scan left-to-right, stop at first tile
               if self.tile_matrix[row][col] is not None:
                  pos = self.get_cell_position(row, col)
                  if pos.x <= 0:
                     return False
                  if game_grid.is_occupied(pos.y, pos.x - 1):
                     return False
                  break                        # only leftmost tile in this row matters

      elif direction == 'right':
         for row in range(n_rows):
            for col in range(n_cols - 1, -1, -1):  # scan right-to-left, stop at first tile
               if self.tile_matrix[row][col] is not None:
                  pos = self.get_cell_position(row, col)
                  if pos.x >= Tetromino.grid_width - 1:
                     return False
                  if game_grid.is_occupied(pos.y, pos.x + 1):
                     return False
                  break                        # only rightmost tile in this row matters

      else:  # down
         for col in range(n_cols):
            for row in range(n_rows - 1, -1, -1):  # scan bottom-to-top, stop at first tile
               if self.tile_matrix[row][col] is not None:
                  pos = self.get_cell_position(row, col)
                  if pos.y <= 0:
                     return False
                  if game_grid.is_occupied(pos.y - 1, pos.x):
                     return False
                  break                        # only bottommost tile in this col matters

      return True

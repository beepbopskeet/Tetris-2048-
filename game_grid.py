import lib.stddraw as stddraw
from lib.color import Color
from point import Point
import numpy as np


class GameGrid:
   def __init__(self, grid_h, grid_w):
      self.grid_height = grid_h
      self.grid_width = grid_w
      self.tile_matrix = np.full((grid_h, grid_w), None)
      self.current_tetromino = None
      self.hold_tetromino = None
      self.game_over = False
      self.paused = False
      self.score = 0
      self.best_score = 0
      self.win = False
      self.level = 1
      self.fall_speed = 8
      self.difficulty_name = 'Classic'
      self.combo_count = 0
      self.combo_text = ''
      self.combo_timer = 0
      self.empty_cell_color = Color(239, 246, 255)
      self.line_color = Color(214, 226, 244)
      self.boundary_color = Color(184, 203, 229)
      self.panel_color = Color(229, 238, 255)
      self.text_color = Color(91, 103, 130)
      self.card_color = Color(255, 243, 248)
      self.alt_card_color = Color(238, 247, 255)
      self.combo_color = Color(255, 182, 217)
      self.line_thickness = 0.002
      self.box_thickness = 5 * self.line_thickness

   def display(self, next_tetromino=None, panel_width=5, username=''):
      stddraw.clear(Color(244, 248, 255))
      panel_x = self.grid_width - 0.5
      stddraw.setPenColor(self.panel_color)
      stddraw.filledRectangle(panel_x, -0.5, panel_width, self.grid_height)
      self.draw_grid()
      self.draw_ghost_piece()
      if self.current_tetromino is not None:
         self.current_tetromino.draw()
      self.draw_boundaries()
      self._draw_panel(next_tetromino, panel_width, username)
      self._draw_combo_overlay()
      stddraw.show(90)

   def draw_ghost_piece(self):
      if self.current_tetromino is None:
         return
      ghost = self.current_tetromino.copy()
      while ghost.can_be_moved('down', self):
         ghost.bottom_left_cell.y -= 1
      ghost.draw(ghost=True)

   def animate_landing(self, tetromino, next_tetromino, username, panel_width):
      for scale in (1.02, 0.97, 1.0):
         stddraw.clear(Color(244, 248, 255))
         panel_x = self.grid_width - 0.5
         stddraw.setPenColor(self.panel_color)
         stddraw.filledRectangle(panel_x, -0.5, panel_width, self.grid_height)
         self.draw_grid()
         self.draw_ghost_piece()
         tetromino.draw(landing_scale=scale)
         self.draw_boundaries()
         self._draw_panel(next_tetromino, panel_width, username)
         self._draw_combo_overlay()
         stddraw.show(35)

   def _rounded_card(self, x, y, w, h, fill_color):
      stddraw.setPenColor(fill_color)
      stddraw.filledRectangle(x, y, w, h)
      stddraw.setPenColor(self.boundary_color)
      stddraw.setPenRadius(0.003)
      stddraw.rectangle(x, y, w, h)
      stddraw.setPenRadius()

   def _draw_panel(self, next_tetromino, panel_width, username=''):
      panel_left = self.grid_width + 0.2
      panel_inner_w = panel_width - 0.9
      center_x = panel_left + panel_inner_w / 2

      self._rounded_card(panel_left, 16.9, panel_inner_w, 2.2, self.card_color)
      stddraw.setPenColor(self.text_color)
      stddraw.setFontFamily('Arial')
      stddraw.setFontSize(11)
      stddraw.boldText(center_x, 18.35, username or 'Player')
      stddraw.setFontSize(10)
      stddraw.text(center_x, 17.55, f'Difficulty: {self.difficulty_name}')

      self._rounded_card(panel_left, 13.4, panel_inner_w, 2.7, self.alt_card_color)
      stddraw.setFontSize(12)
      stddraw.boldText(center_x, 15.5, 'SCORE')
      stddraw.setFontSize(18)
      stddraw.boldText(center_x, 14.45, str(self.score))

      self._rounded_card(panel_left, 10.2, panel_inner_w, 2.4, self.card_color)
      stddraw.setFontSize(11)
      stddraw.boldText(center_x, 12.0, f'BEST  {self.best_score}')
      stddraw.text(center_x, 11.1, f'LEVEL {self.level}   SPD {max(1, 14 - self.fall_speed)}')

      self._rounded_card(panel_left, 6.4, panel_inner_w, 2.9, self.alt_card_color)
      stddraw.setFontSize(12)
      stddraw.boldText(center_x, 8.75, 'NEXT')
      if next_tetromino is not None:
         self._draw_next_piece(next_tetromino, center_x, 7.3)

      self._rounded_card(panel_left, 2.8, panel_inner_w, 2.9, self.card_color)
      stddraw.setFontSize(12)
      stddraw.boldText(center_x, 5.15, 'HOLD')
      if self.hold_tetromino is not None:
         self._draw_next_piece(self.hold_tetromino, center_x, 3.7)
      else:
         stddraw.setFontSize(10)
         stddraw.text(center_x, 3.8, 'Press C')

      # ── Pause button ──────────────────────────────────────────────────
      btn_x = panel_left
      btn_y = 0.2
      btn_w = panel_inner_w
      btn_h = 1.35
      btn_color = Color(255, 182, 217) if self.paused else Color(183, 217, 255)
      self._rounded_card(btn_x, btn_y, btn_w, btn_h, btn_color)
      stddraw.setPenColor(self.text_color)
      stddraw.setFontSize(13)
      label = '▶  Resume' if self.paused else '⏸  Pause'
      stddraw.boldText(center_x, btn_y + btn_h / 2, label)
      # Store button bounds so run_game can hit-test mouse clicks
      self._pause_btn = (btn_x, btn_y, btn_w, btn_h)

      self._rounded_card(panel_left, 1.75, panel_inner_w, 0.9, self.alt_card_color)
      stddraw.setFontSize(8)
      stddraw.text(center_x, 2.25, 'R restart   Space drop   C hold')

   def is_pause_button_clicked(self, mx, my):
      """Return True if (mx, my) falls inside the pause button."""
      if not hasattr(self, '_pause_btn'):
         return False
      x, y, w, h = self._pause_btn
      return x <= mx <= x + w and y <= my <= y + h

   def _draw_next_piece(self, tetromino, center_x, center_y):
      mat = tetromino.get_min_bounded_tile_matrix()
      n_rows = len(mat)
      n_cols = len(mat[0])
      # Card inner width ~5.3 units, height ~1.8 units available for piece
      max_tile_w = 5.3 / n_cols
      max_tile_h = 1.8 / n_rows
      tile_size  = min(max_tile_w, max_tile_h, 0.9)  # cap at 0.9
      offset_x = center_x - n_cols * tile_size / 2.0 + tile_size / 2.0
      offset_y = center_y + n_rows * tile_size / 2.0 - tile_size / 2.0
      for row in range(n_rows):
         for col in range(n_cols):
            if mat[row][col] is not None:
               p = Point(offset_x + col * tile_size, offset_y - row * tile_size)
               mat[row][col].draw(p, length=tile_size)

   def _draw_combo_overlay(self):
      if self.combo_timer <= 0 or not self.combo_text:
         return
      cx = self.grid_width / 2 - 0.5
      cy = self.grid_height - 1.5
      stddraw.setPenColor(self.combo_color)
      stddraw.setFontFamily('Arial')
      stddraw.setFontSize(22 if self.combo_timer > 10 else 18)
      stddraw.boldText(cx, cy, self.combo_text)
      self.combo_timer -= 1

   def draw_grid(self):
      for row in range(self.grid_height):
         for col in range(self.grid_width):
            if self.tile_matrix[row][col] is not None:
               self.tile_matrix[row][col].draw(Point(col, row))
            else:
               stddraw.setPenColor(self.empty_cell_color)
               stddraw.filledSquare(col, row, 0.5)
      stddraw.setPenColor(self.line_color)
      stddraw.setPenRadius(self.line_thickness)
      start_x, end_x = -0.5, self.grid_width - 0.5
      start_y, end_y = -0.5, self.grid_height - 0.5
      for x in np.arange(start_x + 1, end_x, 1):
         stddraw.line(x, start_y, x, end_y)
      for y in np.arange(start_y + 1, end_y, 1):
         stddraw.line(start_x, y, end_x, y)
      stddraw.setPenRadius()

   DANGER_ROWS = 3   # game over threshold — tile must land above this many rows from top

   def draw_boundaries(self):
      stddraw.setPenColor(self.boundary_color)
      stddraw.setPenRadius(self.box_thickness)
      stddraw.rectangle(-0.5, -0.5, self.grid_width, self.grid_height)
      stddraw.setPenRadius()
      # Red danger line — located DANGER_ROWS rows below the top
      danger_y = self.grid_height - self.DANGER_ROWS - 0.5
      stddraw.setPenColor(Color(220, 60, 80))
      stddraw.setPenRadius(0.006)
      stddraw.line(-0.5, danger_y, self.grid_width - 0.5, danger_y)
      stddraw.setPenRadius()

   def is_occupied(self, row, col):
      if not self.is_inside(row, col):
         return False
      return self.tile_matrix[row][col] is not None

   def is_inside(self, row, col):
      if row < 0 or row >= self.grid_height:
         return False
      if col < 0 or col >= self.grid_width:
         return False
      return True

   def update_grid(self, tiles_to_lock, blc_position):
      self.current_tetromino = None
      n_rows, n_cols = len(tiles_to_lock), len(tiles_to_lock[0])
      danger_threshold = self.grid_height - self.DANGER_ROWS
      for col in range(n_cols):
         for row in range(n_rows):
            if tiles_to_lock[row][col] is not None:
               pos = Point()
               pos.x = blc_position.x + col
               pos.y = blc_position.y + (n_rows - 1) - row
               if self.is_inside(pos.y, pos.x):
                  self.tile_matrix[pos.y][pos.x] = tiles_to_lock[row][col]
                  # Game over: tile placed above the danger line
                  if pos.y >= danger_threshold:
                     self.game_over = True
               else:
                  self.game_over = True
      return self.game_over

   def find_merge_candidates(self):
      """
      Return a set of (row, col) positions that would merge in the next
      process_after_landing call (vertically adjacent equal tiles).
      """
      candidates = set()
      for col in range(self.grid_width):
         for row in range(self.grid_height - 1):
            lower = self.tile_matrix[row][col]
            upper = self.tile_matrix[row + 1][col]
            if lower is not None and upper is not None and lower.number == upper.number:
               candidates.add((row, col))
               candidates.add((row + 1, col))
      return candidates

   def _draw_frame(self, next_tetromino, panel_width, username,
                   flash_cells=None, bright=True, override_matrix=None,
                   line_flash_cells=None, line_bright=True):
      """
      Draw one complete frame.  flash_cells is a set of (row,col) to highlight.
      override_matrix lets gravity pass a mid-animation tile layout.
      """
      matrix = override_matrix if override_matrix is not None else self.tile_matrix
      stddraw.clear(Color(244, 248, 255))
      panel_x = self.grid_width - 0.5
      stddraw.setPenColor(self.panel_color)
      stddraw.filledRectangle(panel_x, -0.5, panel_width, self.grid_height)

      for row in range(self.grid_height):
         for col in range(self.grid_width):
            tile = matrix[row][col]
            if tile is not None:
               p = Point(col, row)
               if line_flash_cells and (row, col) in line_flash_cells:
                  tile.draw_line_flash(p, bright=line_bright)
               elif flash_cells and (row, col) in flash_cells:
                  tile.draw_flash(p, bright=bright)
               else:
                  tile.draw(p)
            else:
               stddraw.setPenColor(self.empty_cell_color)
               stddraw.filledSquare(col, row, 0.5)

      stddraw.setPenColor(self.line_color)
      stddraw.setPenRadius(self.line_thickness)
      start_x, end_x = -0.5, self.grid_width - 0.5
      start_y, end_y = -0.5, self.grid_height - 0.5
      for x in np.arange(start_x + 1, end_x, 1):
         stddraw.line(x, start_y, x, end_y)
      for y in np.arange(start_y + 1, end_y, 1):
         stddraw.line(start_x, y, end_x, y)
      stddraw.setPenRadius()

      self.draw_boundaries()
      self._draw_panel(next_tetromino, panel_width, username)
      self._draw_combo_overlay()

   def _animate_gravity(self, next_tetromino, panel_width, username):
      """
      Smoothly drop each floating tile to its settled position.
      Works column by column: computes final positions, then animates
      each tile sliding down step by step.
      """
      import copy as _copy

      # Build per-column drop distances
      # For each tile that needs to fall, record (current_row, col, distance)
      drops = []   # list of [row, col, fall_distance]
      for col in range(self.grid_width):
         # Simulate gravity for this column
         tiles_in_col = [(row, self.tile_matrix[row][col])
                         for row in range(self.grid_height)
                         if self.tile_matrix[row][col] is not None]
         # After gravity: tile i (0-indexed from bottom) sits at row i
         for settled_row, (orig_row, tile) in enumerate(tiles_in_col):
            if orig_row != settled_row:
               drops.append([orig_row, col, orig_row - settled_row])

      if not drops:
         return   # nothing to animate

      max_dist = max(d[2] for d in drops)

      # Animate step by step
      for step in range(1, max_dist + 1):
         # Build a temporary display matrix
         temp = np.full((self.grid_height, self.grid_width), None)
         # Copy tiles that don't move
         for row in range(self.grid_height):
            for col in range(self.grid_width):
               if self.tile_matrix[row][col] is not None:
                  temp[row][col] = self.tile_matrix[row][col]

         # Place falling tiles at their interpolated position
         moving_cells = set()
         for entry in drops:
            orig_row, col, dist = entry
            step_dist = min(step, dist)
            new_row = orig_row - step_dist
            # Remove from original, place at new
            temp[orig_row][col] = None
            temp[new_row][col] = self.tile_matrix[orig_row][col]
            moving_cells.add((new_row, col))

         self._draw_frame(next_tetromino, panel_width, username,
                          override_matrix=temp)
         stddraw.show(35)

      # Commit gravity to real matrix
      self.handle_free_tiles()

   def process_after_landing(self, next_tetromino=None, panel_width=0, username=''):
      """
      Animated version:
        1. Flash + merge vertically adjacent equal tiles (chain)
        2. Clear full horizontal lines
        3. Animate gravity (tiles fall to fill gaps)
        4. Repeat until stable
      """
      total_lines   = 0
      total_merged  = 0
      total_moved   = 0
      total_gain    = 0
      animate       = next_tetromino is not None or panel_width > 0

      changed = True
      while changed:
         # ── 1. Flash candidates then merge ──────────────────────────
         if animate:
            candidates = self.find_merge_candidates()
            if candidates:
               for _ in range(3):
                  for bright in (True, False):
                     self._draw_frame(next_tetromino, panel_width, username,
                                      flash_cells=candidates, bright=bright)
                     stddraw.show(75)

         merged_count, gain = self.merge_tiles()
         total_merged += merged_count
         total_gain   += gain

         if animate and merged_count:
            self._draw_frame(next_tetromino, panel_width, username)
            stddraw.show(60)

         # ── 2. Flash full lines then clear ──────────────────────────
         if animate:
            full_rows = [row for row in range(self.grid_height)
                         if all(self.tile_matrix[row][col] is not None
                                for col in range(self.grid_width))]
            if full_rows:
               line_cells = {(row, col)
                             for row in full_rows
                             for col in range(self.grid_width)}
               for _ in range(3):
                  for lb in (True, False):
                     self._draw_frame(next_tetromino, panel_width, username,
                                      line_flash_cells=line_cells, line_bright=lb)
                     stddraw.show(75)

         line_count, gain = self.clear_full_lines()
         total_lines += line_count
         total_gain  += gain

         if animate and line_count:
            self._draw_frame(next_tetromino, panel_width, username)
            stddraw.show(60)

         # ── 3. Gravity with animation ────────────────────────────────
         if animate:
            self._animate_gravity(next_tetromino, panel_width, username)
            moved_count = 1 if self._has_gaps_before_gravity() else 0
         else:
            moved_count, _ = self.handle_free_tiles()
         total_moved += moved_count

         changed = (merged_count > 0 or line_count > 0 or moved_count > 0)

      # ── Combo text ───────────────────────────────────────────────────
      if total_lines > 0 or total_merged > 1:
         self.combo_count += 1
         bonus = self.combo_count * 15
         self.score += bonus
         total_gain += bonus
         self.combo_text  = f'COMBO x{self.combo_count}' if self.combo_count > 1 else 'NICE!'
         self.combo_timer = 16
      else:
         self.combo_count = 0
         if total_moved > 0:
            self.combo_text  = 'CASCADE!'
            self.combo_timer = 14

      self.best_score = max(self.best_score, self.score)
      return {
         'lines_cleared': total_lines,
         'merged':        total_merged,
         'removed':       total_moved,
         'score_gain':    total_gain,
      }

   def _has_gaps_before_gravity(self):
      """Return True if any column has a gap below a tile (gravity needed)."""
      for col in range(self.grid_width):
         found_tile = False
         for row in range(self.grid_height - 1, -1, -1):
            if self.tile_matrix[row][col] is not None:
               found_tile = True
            elif found_tile:
               return True
      return False

   def merge_tiles(self):
      """
      Column-wise bottom-to-top chain merging.
      Two vertically adjacent tiles with equal numbers merge: lower tile
      doubles, upper tile removed. Returns (merge_count, score_gained).
      """
      merged_count = 0
      score_gain = 0
      # Keep repeating until a full pass produces no merges (chain merging)
      changed = True
      while changed:
         changed = False
         for col in range(self.grid_width):
            row = 0
            while row < self.grid_height - 1:
               lower = self.tile_matrix[row][col]
               upper = self.tile_matrix[row + 1][col]
               if lower is not None and upper is not None and lower.number == upper.number:
                  new_val = lower.number * 2
                  lower.number = new_val
                  lower._update_colors()
                  self.tile_matrix[row + 1][col] = None
                  self.score += new_val
                  score_gain += new_val
                  merged_count += 1
                  changed = True
                  if new_val == 2048:
                     self.win = True
                  # Don't advance row — the merged tile may chain with the one above
               else:
                  row += 1
      return merged_count, score_gain

   def clear_full_lines(self):
      """
      Remove fully-occupied rows, shift everything above down.
      Score += sum of numbers in each cleared row.
      Returns (lines_cleared, score_gained).
      """
      cleared_count = 0
      gained = 0
      row = 0
      while row < self.grid_height:
         if all(self.tile_matrix[row][col] is not None for col in range(self.grid_width)):
            line_sum = sum(self.tile_matrix[row][col].number for col in range(self.grid_width))
            self.score += line_sum
            gained += line_sum
            cleared_count += 1
            for r in range(row, self.grid_height - 1):
               for c in range(self.grid_width):
                  self.tile_matrix[r][c] = self.tile_matrix[r + 1][c]
            for c in range(self.grid_width):
               self.tile_matrix[self.grid_height - 1][c] = None
            # Don't increment row — re-check same index (it now holds the row above)
         else:
            row += 1
      return cleared_count, gained

   def handle_free_tiles(self):
      """
      Apply gravity: in each column, compact all tiles to the bottom,
      filling any gaps left by merges or cleared lines.
      Returns (moved_count, 0).
      """
      moved_total = 0
      for col in range(self.grid_width):
         # Collect non-None tiles in this column from bottom to top
         tiles = []
         for row in range(self.grid_height):
            if self.tile_matrix[row][col] is not None:
               tiles.append(self.tile_matrix[row][col])
         # Place them back starting from row 0 (bottom), fill rest with None
         for row in range(self.grid_height):
            new_tile = tiles[row] if row < len(tiles) else None
            if new_tile is not self.tile_matrix[row][col]:
               moved_total += 1
            self.tile_matrix[row][col] = new_tile
      return moved_total, 0

   def _find_connected_tiles(self):
      """BFS from every tile in row 0 (bottom). Returns boolean grid."""
      connected = np.full((self.grid_height, self.grid_width), False)
      queue = []
      for col in range(self.grid_width):
         if self.tile_matrix[0][col] is not None:
            connected[0][col] = True
            queue.append((0, col))
      while queue:
         row, col = queue.pop(0)
         for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = row + dr, col + dc
            if self.is_inside(nr, nc) and not connected[nr][nc] and self.tile_matrix[nr][nc] is not None:
               connected[nr][nc] = True
               queue.append((nr, nc))
      return connected
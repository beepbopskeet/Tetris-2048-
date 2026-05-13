import json
import os
import random
from typing import Optional

import lib.stddraw as stddraw
from lib.color import Color
from lib.picture import Picture

from game_grid import GameGrid
from tetromino import Tetromino

try:
   import pygame
   import numpy as np
except Exception:
   pygame = None
   np = None


LEADERBOARD_FILE = 'leaderboard.json'

BG           = Color(244, 248, 255)
LEFT_DECOR   = Color(228, 240, 255)
RIGHT_DECOR  = Color(255, 230, 242)
CARD_BG      = Color(255, 242, 248)
BUTTON       = Color(183, 217, 255)
BUTTON_HOVER = Color(255, 198, 226)
TEXT         = Color(91, 103, 130)
BORDER       = Color(194, 208, 232)
HIGHLIGHT    = Color(255, 175, 210)
SOFT_WHITE   = Color(255, 252, 254)

DIFFICULTIES = {
   'Sweet':   {'base_speed': 13, 'speedup': 1, 'threshold': 420},
   'Classic': {'base_speed': 10, 'speedup': 1, 'threshold': 320},
   'Spicy':   {'base_speed':  8, 'speedup': 1, 'threshold': 240},
}


# ── Sound ──────────────────────────────────────────────────────────────

class SoundManager:
   def __init__(self):
      self.enabled = False
      self.sounds = {}
      if pygame is None or np is None:
         return
      try:
         if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=1)
         self.sounds = {
            'move':     self._make_tone(420, 0.045, volume=0.18),
            'rotate':   self._make_tone(560, 0.06,  volume=0.20),
            'drop':     self._make_tone(250, 0.08,  volume=0.22),
            'merge':    self._make_tone(660, 0.10,  volume=0.25),
            'clear':    self._make_tone(780, 0.13,  volume=0.30),
            'hold':     self._make_tone(520, 0.08,  volume=0.24),
            'levelup':  self._make_tone(900, 0.16,  volume=0.32),
            'gameover': self._make_tone(180, 0.35,  volume=0.28),
         }
         self.enabled = True
      except Exception:
         self.enabled = False

   def _make_tone(self, frequency, duration, volume=0.2):
      sample_rate = 22050
      t = np.linspace(0, duration, int(sample_rate * duration), False)
      wave = np.sin(2 * np.pi * frequency * t)
      envelope = np.linspace(1.0, 0.15, len(wave))
      audio = (wave * envelope * (32767 * volume)).astype(np.int16)
      return pygame.sndarray.make_sound(audio)

   def play(self, name):
      if self.enabled and name in self.sounds:
         try:
            self.sounds[name].play()
         except Exception:
            pass


SFX = SoundManager()


# ── Leaderboard ────────────────────────────────────────────────────────

def load_leaderboard():
   if os.path.exists(LEADERBOARD_FILE):
      with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
         return json.load(f)
   return []

def save_leaderboard(lb):
   with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
      json.dump(lb, f)

def add_to_leaderboard(username, score):
   lb = load_leaderboard()
   lb.append({'name': username, 'score': score})
   lb.sort(key=lambda x: x['score'], reverse=True)
   lb = lb[:15]
   save_leaderboard(lb)
   return lb

def get_best_score():
   lb = load_leaderboard()
   return lb[0]['score'] if lb else 0


# ── Helpers ────────────────────────────────────────────────────────────

def _rounded_card(x, y, w, h, fill_color, border_color=BORDER):
   stddraw.setPenColor(fill_color)
   stddraw.filledRectangle(x, y, w, h)
   stddraw.setPenColor(border_color)
   stddraw.setPenRadius(0.004)
   stddraw.rectangle(x, y, w, h)
   stddraw.setPenRadius()

def calculate_fall_speed(score, difficulty_name):
   config = DIFFICULTIES[difficulty_name]
   level_gain = score // config['threshold']
   return max(2, config['base_speed'] - level_gain * config['speedup'])

def get_level(score, difficulty_name):
   return 1 + score // DIFFICULTIES[difficulty_name]['threshold']

def create_tetromino(piece_type: Optional[str] = None):
   tetromino_types = ['I', 'O', 'Z', 'S', 'T', 'L', 'J']
   return Tetromino(piece_type or random.choice(tetromino_types))


# ── One game session ───────────────────────────────────────────────────

def run_game(grid_height, grid_width, panel_width, username, difficulty_name):
   """
   Play one full game. Returns True if the player pressed R to restart.

   FIX: Previously main() called main() recursively for restart, which
   caused the app to close when returning. Now restart is handled by
   returning True to the caller's while loop — no recursion.
   """
   Tetromino.grid_height = grid_height
   Tetromino.grid_width = grid_width

   grid = GameGrid(grid_height, grid_width)
   grid.best_score = get_best_score()
   grid.difficulty_name = difficulty_name

   current_tetromino = create_tetromino()
   next_tetromino    = create_tetromino()
   hold_tetromino    = None
   can_hold          = True
   grid.current_tetromino = current_tetromino
   grid.hold_tetromino    = hold_tetromino

   paused         = False
   fall_counter   = 0
   previous_level = 1
   # FIX: flag so hard-drop lands on the very next frame without waiting
   # for fall_counter to tick up to fall_speed.
   hard_dropped   = False

   while True:
      # ── Input ───────────────────────────────────────────────────────
      if stddraw.hasNextKeyTyped():
         key_typed = stddraw.nextKeyTyped()
         stddraw.clearKeysTyped()
         key_lower = key_typed.lower() if key_typed else ''

         if not paused:
            if key_lower == 'left':
               if current_tetromino.move('left', grid):
                  SFX.play('move')
            elif key_lower == 'right':
               if current_tetromino.move('right', grid):
                  SFX.play('move')
            elif key_lower == 'down':
               if current_tetromino.move('down', grid):
                  SFX.play('move')
            elif key_lower == 'up':
               if current_tetromino.rotate(grid):
                  SFX.play('rotate')
            elif key_lower in ('space', ' '):
               dist = current_tetromino.hard_drop(grid)
               if dist > 0:
                  SFX.play('drop')
               hard_dropped = True
            elif key_lower in ('c', 'h'):
               current_tetromino, next_tetromino, hold_tetromino, can_hold = handle_hold(
                  current_tetromino, next_tetromino, hold_tetromino, can_hold, grid
               )

         if key_lower == 'p':
            paused = not paused
            grid.paused = paused
         elif key_lower == 'r':
            return True   # signal restart — no recursion

      # ── Mouse click — pause button ───────────────────────────────────
      if not paused and stddraw.mousePressed():
         mx, my = stddraw.mouseX(), stddraw.mouseY()
         if grid.is_pause_button_clicked(mx, my):
            paused = True
            grid.paused = True
            while stddraw.mousePressed():
               stddraw.show(30)

      # ── Pause ───────────────────────────────────────────────────────
      if paused:
         # Draw and wait — no redrawing in loop, no flickering
         grid.display(next_tetromino, panel_width, username)
         _draw_pause_screen(grid_height, grid_width, panel_width)
         stddraw.show(0)
         # Only waiting for input, no display updates
         while paused:
            stddraw.show(50)
            # Keyboard check
            if stddraw.hasNextKeyTyped():
               k = stddraw.nextKeyTyped()
               stddraw.clearKeysTyped()
               if k == 'p':
                  paused = False
                  grid.paused = False
               elif k == 'r':
                  return True
            # Mouse check
            if stddraw.mousePressed():
               mx, my = stddraw.mouseX(), stddraw.mouseY()
               if grid.is_pause_button_clicked(mx, my):
                  paused = False
                  grid.paused = False
                  while stddraw.mousePressed():
                     stddraw.show(30)
         continue

      # ── Level / speed ────────────────────────────────────────────────
      fall_speed   = calculate_fall_speed(grid.score, difficulty_name)
      grid.level   = get_level(grid.score, difficulty_name)
      grid.fall_speed  = fall_speed
      grid.best_score  = max(grid.best_score, grid.score)
      grid.hold_tetromino = hold_tetromino

      if grid.level > previous_level:
         previous_level = grid.level
         grid.combo_text  = f'LEVEL {grid.level}'
         grid.combo_timer = 18
         SFX.play('levelup')

      # ── Gravity / hard-drop landing ──────────────────────────────────
      if hard_dropped:
         # Piece is already at its lowest position; land it now.
         landed       = True
         hard_dropped = False
      else:
         fall_counter += 1
         if fall_counter >= fall_speed:
            fall_counter = 0
            landed = not current_tetromino.move('down', grid)
         else:
            landed = False

      # ── Landing sequence ─────────────────────────────────────────────
      if landed:
         grid.animate_landing(current_tetromino, next_tetromino, username, panel_width)
         tiles, pos = current_tetromino.get_min_bounded_tile_matrix(True)
         game_over = grid.update_grid(tiles, pos)
         if game_over:
            break

         events = grid.process_after_landing(next_tetromino, panel_width, username)
         if events['merged']:
            SFX.play('merge')
         if events['lines_cleared']:
            SFX.play('clear')
         can_hold = True

         if grid.win:
            _draw_win_screen(grid, next_tetromino, grid_height, grid_width, panel_width, username)
            grid.win = False

         current_tetromino = next_tetromino
         next_tetromino    = create_tetromino()
         grid.current_tetromino = current_tetromino

      # ── Draw ─────────────────────────────────────────────────────────
      grid.display(next_tetromino, panel_width, username)

   # ── Game over ────────────────────────────────────────────────────────
   lb = add_to_leaderboard(username, grid.score)
   SFX.play('gameover')
   return _draw_game_over_screen(grid, next_tetromino, grid_height, grid_width, panel_width, username, lb)


# ── Main ───────────────────────────────────────────────────────────────

def main():
   grid_height, grid_width = 20, 12
   panel_width = 8
   cell_size   = 28
   canvas_side = cell_size * (grid_width + panel_width)

   # FIX: Canvas is set up ONCE here and never again.
   # Previously setCanvasSize was called inside main() which was called
   # recursively on restart — opening a new window each time.
   stddraw.setCanvasSize(canvas_side, canvas_side)
   stddraw.setXscale(-0.5, grid_width + panel_width - 0.5)
   stddraw.setYscale(-0.5, grid_height - 0.5)

   Tetromino.grid_height = grid_height
   Tetromino.grid_width  = grid_width

   # FIX: restart loop — no recursion, no stack overflow, no closed window.
   while True:
      username, difficulty_name = display_game_menu(grid_height, grid_width, panel_width)
      restart = run_game(grid_height, grid_width, panel_width, username, difficulty_name)
      if not restart:
         break


# ── Hold ───────────────────────────────────────────────────────────────

def handle_hold(current_tetromino, next_tetromino, hold_tetromino, can_hold, grid):
   if not can_hold:
      return current_tetromino, next_tetromino, hold_tetromino, can_hold

   SFX.play('hold')
   # reset the new tetromino and keep the old one
   current_tetromino.reset_position()

   if hold_tetromino is None:
      hold_tetromino    = current_tetromino
      current_tetromino = next_tetromino
      next_tetromino    = create_tetromino()
   else:
      previous_hold     = hold_tetromino
      hold_tetromino    = current_tetromino
      current_tetromino = previous_hold
      current_tetromino.reset_position()

   grid.current_tetromino = current_tetromino
   grid.hold_tetromino    = hold_tetromino
   return current_tetromino, next_tetromino, hold_tetromino, False


# ── Screens ────────────────────────────────────────────────────────────

def display_game_menu(grid_height, grid_width, panel_width):
   total_width      = grid_width + panel_width
   cx               = (total_width - 1) / 2
   username         = ''
   difficulty_names = list(DIFFICULTIES.keys())
   difficulty_index = 0
   show_about       = False

   # ── About button geometry (top right corner) ───────────────────────────
   about_w, about_h = 3.2, 1.1
   about_x = total_width - 0.5 - about_w - 0.4
   about_y = grid_height - 1.5

   while True:
      stddraw.clear(BG)

      stddraw.setPenColor(LEFT_DECOR)
      stddraw.filledRectangle(-0.5, -0.5, total_width * 0.30, grid_height)
      stddraw.setPenColor(Color(255, 230, 242))
      stddraw.filledRectangle(total_width * 0.70 - 0.5, -0.5, total_width * 0.30, grid_height)

      card_w, card_h = 12.4, 16.0
      card_x = cx - card_w / 2
      card_y = 0.4
      _rounded_card(card_x, card_y, card_w, card_h, CARD_BG)

      current_dir = os.path.dirname(os.path.realpath(__file__))
      img_file = os.path.join(current_dir, 'images', 'menu_image.png')
      try:
         stddraw.picture(Picture(img_file), cx, grid_height - 3.8)
      except Exception:
         stddraw.setPenColor(TEXT)
         stddraw.setFontFamily('Arial')
         stddraw.setFontSize(30)
         stddraw.boldText(cx, grid_height - 3.8, 'Tetris 2048')

      stddraw.setPenColor(TEXT)
      stddraw.setFontFamily('Arial')
      stddraw.setFontSize(12)
      stddraw.boldText(cx, 13.2, 'Enter your name')

      box_w, box_h = 8.4, 1.25
      box_x, box_y = cx - box_w / 2, 11.75
      _rounded_card(box_x, box_y, box_w, box_h, SOFT_WHITE)
      stddraw.setPenColor(TEXT)
      stddraw.setFontSize(15)
      stddraw.text(cx, box_y + box_h / 2, username if username else 'Type here...')

      stddraw.setFontSize(12)
      stddraw.boldText(cx, 10.5, 'Difficulty')

      diff_y = 9.2
      diff_box_w, diff_box_h = 2.6, 1.0
      diff_gap = 0.35
      total_diff_w  = len(difficulty_names) * diff_box_w + (len(difficulty_names) - 1) * diff_gap
      diff_start_x  = cx - total_diff_w / 2

      for i, name in enumerate(difficulty_names):
         x    = diff_start_x + i * (diff_box_w + diff_gap)
         fill = Color(255, 205, 225) if i == difficulty_index else Color(205, 225, 255)
         _rounded_card(x, diff_y, diff_box_w, diff_box_h, fill)
         stddraw.setPenColor(TEXT)
         stddraw.setFontSize(10)
         stddraw.boldText(x + diff_box_w / 2, diff_y + diff_box_h / 2, name)

      if stddraw.mousePressed():
         mx, my = stddraw.mouseX(), stddraw.mouseY()
      else:
         mx, my = -999, -999

      button_w, button_h = 8.2, 1.45
      button_x, button_y = cx - button_w / 2, 7.15
      hovered = button_x <= mx <= button_x + button_w and button_y <= my <= button_y + button_h
      _rounded_card(button_x, button_y, button_w, button_h, BUTTON_HOVER if hovered else BUTTON)
      stddraw.setPenColor(TEXT)
      stddraw.setFontSize(16)
      stddraw.boldText(cx, button_y + button_h / 2, 'Start Game')

      _draw_leaderboard_preview(cx, 6.5)

      # ── About buton ────────────────────────────────────────────────
      about_hovered = about_x <= mx <= about_x + about_w and about_y <= my <= about_y + about_h
      _rounded_card(about_x, about_y, about_w, about_h,
                    BUTTON_HOVER if about_hovered else Color(220, 235, 255))
      stddraw.setPenColor(TEXT)
      stddraw.setFontFamily('Arial')
      stddraw.setFontSize(10)
      stddraw.boldText(about_x + about_w / 2, about_y + about_h / 2, '?  About')

      # ── About popup ─────────────────────────────────────────────────
      if show_about:
         _draw_about_screen(cx, grid_height)

      stddraw.show(50)

      if stddraw.hasNextKeyTyped():
         key = stddraw.nextKeyTyped()
         stddraw.clearKeysTyped()
         if show_about:
            show_about = False
         elif key in ('Return', 'enter'):
            if username.strip():
               break
         elif key in ('BackSpace', 'backspace'):
            username = username[:-1]
         elif len(key) == 1 and len(username) < 12 and key.isprintable():
            username += key

      if stddraw.mousePressed():
         mouse_x, mouse_y = stddraw.mouseX(), stddraw.mouseY()
         if show_about:
            show_about = False
         else:
            for i, name in enumerate(difficulty_names):
               x = diff_start_x + i * (diff_box_w + diff_gap)
               if x <= mouse_x <= x + diff_box_w and diff_y <= mouse_y <= diff_y + diff_box_h:
                  difficulty_index = i
            if button_x <= mouse_x <= button_x + button_w and button_y <= mouse_y <= button_y + button_h:
               if not username.strip():
                  username = 'Player'
               break
            if about_x <= mouse_x <= about_x + about_w and about_y <= mouse_y <= about_y + about_h:
               show_about = True
         while stddraw.mousePressed():
            stddraw.show(20)

   return (username.strip() or 'Player', difficulty_names[difficulty_index])


def _draw_leaderboard_preview(cx, top_y):
   lb = load_leaderboard()
   card_w, card_h = 9.4, 2.7
   _rounded_card(cx - card_w / 2, top_y - card_h, card_w, card_h, Color(239, 247, 255))
   stddraw.setPenColor(TEXT)
   stddraw.setFontFamily('Arial')
   stddraw.setFontSize(11)
   stddraw.boldText(cx, top_y - 0.45, 'BEST SCORES')
   if not lb:
      stddraw.setFontSize(10)
      stddraw.text(cx, top_y - 1.55, 'No scores yet')
      return
   for i, entry in enumerate(lb[:3]):
      y = top_y - 1.05 - 0.55 * i
      stddraw.setFontSize(10)
      stddraw.text(cx, y, f'{i + 1}. {entry["name"][:10]}  -  {entry["score"]}')


def _draw_about_screen(cx, grid_height):
   """Overlay About / Controls popup displayed on top of the menu."""
   pw, ph = 13.0, 13.5
   px = cx - pw / 2
   py = grid_height / 2 - ph / 2
   _rounded_card(px, py, pw, ph, Color(255, 245, 252))
   stddraw.setPenColor(TEXT)
   stddraw.setFontFamily('Arial')

   stddraw.setFontSize(15)
   stddraw.boldText(cx, py + ph - 0.7, 'How to Play')

   stddraw.setFontSize(11)
   stddraw.boldText(cx, py + ph - 1.55, 'Controls')

   lines = [
      (u'\u2190 / \u2192', 'Move left / right'),
      (u'\u2191',          'Rotate piece'),
      (u'\u2193',          'Soft drop'),
      ('SPACE',            'Hard drop'),
      ('C',                'Hold piece'),
      ('P',                'Pause / Resume'),
      ('R',                'Restart game'),
   ]
   row_h  = 0.78
   start_y = py + ph - 2.35
   for i, (key, desc) in enumerate(lines):
      y = start_y - i * row_h
      if i % 2 == 0:
         stddraw.setPenColor(Color(240, 248, 255))
         stddraw.filledRectangle(px + 0.4, y - 0.28, pw - 0.8, row_h - 0.08)
      stddraw.setPenColor(Color(183, 217, 255))
      stddraw.filledRectangle(px + 0.55, y - 0.18, 2.5, row_h - 0.26)
      stddraw.setPenColor(TEXT)
      stddraw.setFontSize(10)
      stddraw.boldText(px + 0.55 + 1.25, y + 0.13, key)
      stddraw.text(px + 4.8, y + 0.13, desc)

   rule_y = start_y - len(lines) * row_h - 0.15
   stddraw.setFontSize(11)
   stddraw.boldText(cx, rule_y, 'Rules')
   rules = [
      'Merge two tiles with the same number',
      'to double their value (reach 2048!)',
      'Clear full rows to earn bonus points.',
      'Game over when tiles reach the red line.',
   ]
   for i, rule in enumerate(rules):
      stddraw.setFontSize(9)
      stddraw.setPenColor(TEXT)
      stddraw.text(cx, rule_y - 0.52 - i * 0.52, rule)

   stddraw.setFontSize(9)
   stddraw.setPenColor(Color(200, 180, 210))
   stddraw.text(cx, py + 0.35, 'Click anywhere or press any key to close')


def _draw_pause_screen(grid_height, grid_width, panel_width):
   cx = grid_width / 2 - 0.5
   cy = grid_height / 2
   _rounded_card(cx - 4.2, cy - 1.8, 8.4, 3.6, Color(255, 245, 249))
   stddraw.setPenColor(TEXT)
   stddraw.setFontFamily('Arial')
   stddraw.setFontSize(28)
   stddraw.boldText(cx, cy + 0.6, 'PAUSED')
   stddraw.setFontSize(13)
   stddraw.text(cx, cy - 0.2, 'Click ⏸ Pause or press P')
   stddraw.text(cx, cy - 0.9, 'to resume')


def _draw_game_over_screen(grid, next_tetromino, grid_height, grid_width, panel_width, username, leaderboard):
   """Show game-over screen. Returns True if player pressed R to restart."""
   cx = (grid_width + panel_width) / 2 - 0.5
   cy = grid_height / 2

   # ── Draw once ──────────────────────────────────────────────────────
   grid.display(next_tetromino, panel_width, username)
   _rounded_card(cx - 6.7, cy - 6.3, 13.4, 12.6, Color(255, 245, 249))
   stddraw.setPenColor(TEXT)
   stddraw.setFontFamily('Arial')
   stddraw.setFontSize(26)
   stddraw.boldText(cx, cy + 5.0, 'GAME OVER')
   stddraw.setFontSize(14)
   stddraw.boldText(cx, cy + 4.0, f'{username}  -  Score: {grid.score}')
   stddraw.text(cx, cy + 3.2, f'Best: {max(grid.best_score, grid.score)}')
   stddraw.boldText(cx, cy + 2.3, 'LEADERBOARD')
   for i, entry in enumerate(leaderboard[:7]):
      row_y = cy + 1.3 - i * 0.82
      if entry['name'] == username and entry['score'] == grid.score:
         stddraw.setPenColor(Color(255, 214, 232))
         stddraw.filledRectangle(cx - 5.7, row_y - 0.26, 11.4, 0.56)
      stddraw.setPenColor(TEXT)
      stddraw.setFontSize(11)
      stddraw.text(cx - 4.6, row_y, f'#{i + 1}')
      stddraw.text(cx,       row_y, entry['name'][:10])
      stddraw.text(cx + 4.4, row_y, str(entry['score']))
   stddraw.setPenColor(HIGHLIGHT)
   stddraw.setFontSize(13)
   stddraw.boldText(cx, cy - 5.2, 'Press R to restart')
   stddraw.show(0)

   # ── Only wait for input, do not redraw ─────────────────────────────────
   while True:
      stddraw.show(50)
      if stddraw.hasNextKeyTyped():
         key = stddraw.nextKeyTyped()
         stddraw.clearKeysTyped()
         if key == 'r':
            return True


def _draw_win_screen(grid, next_tetromino, grid_height, grid_width, panel_width, username):
   grid.display(next_tetromino, panel_width, username)
   cx = (grid_width + panel_width) / 2 - 0.5
   cy = grid_height / 2
   _rounded_card(cx - 5.0, cy - 2.5, 10.0, 5.0, Color(255, 231, 241))
   stddraw.setPenColor(TEXT)
   stddraw.setFontFamily('Arial')
   stddraw.setFontSize(28)
   stddraw.boldText(cx, cy + 0.8, '2048!')
   stddraw.setFontSize(15)
   stddraw.text(cx, cy - 0.2, 'Keep pushing your score higher!')
   stddraw.show(1200)


main()
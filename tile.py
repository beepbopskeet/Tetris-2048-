import random

import lib.stddraw as stddraw
from lib.color import Color


class Tile:
   boundary_thickness = 0.004
   font_family, font_size = 'Arial', 14

   COLOR_MAP = {
      2:    (Color(234, 245, 255), Color(91, 103, 130)),
      4:    (Color(255, 236, 245), Color(91, 103, 130)),
      8:    (Color(220, 234, 255), Color(91, 103, 130)),
      16:   (Color(255, 221, 238), Color(91, 103, 130)),
      32:   (Color(204, 227, 255), Color(91, 103, 130)),
      64:   (Color(255, 205, 230), Color(91, 103, 130)),
      128:  (Color(190, 219, 255), Color(91, 103, 130)),
      256:  (Color(255, 189, 221), Color(91, 103, 130)),
      512:  (Color(177, 212, 255), Color(91, 103, 130)),
      1024: (Color(255, 173, 212), Color(91, 103, 130)),
      2048: (Color(162, 205, 255), Color(91, 103, 130)),
   }
   DEFAULT_BG = Color(150, 188, 235)
   DEFAULT_FG = Color(255, 248, 252)
   GHOST_BG = Color(225, 233, 245)
   GHOST_BORDER = Color(185, 198, 220)

   def __init__(self, number=None):
      # FIX: was random.choice([2, 2, 2, 4]) giving 75% chance of 2.
      # Spec says each tile is randomly 2 or 4 — equal probability.
      self.number = random.choice([2, 4]) if number is None else number
      self._update_colors()

   def _update_colors(self):
      bg, fg = self.COLOR_MAP.get(self.number, (self.DEFAULT_BG, self.DEFAULT_FG))
      self.background_color = bg
      self.foreground_color = fg
      self.box_color = Color(186, 204, 229)

   def _set_font_size(self):
      stddraw.setFontFamily(Tile.font_family)
      if self.number >= 1000:
         stddraw.setFontSize(10)
      elif self.number >= 100:
         stddraw.setFontSize(12)
      else:
         stddraw.setFontSize(Tile.font_size)

   def draw(self, position, length=1):
      stddraw.setPenColor(self.background_color)
      stddraw.filledSquare(position.x, position.y, length / 2)
      stddraw.setPenColor(self.box_color)
      stddraw.setPenRadius(Tile.boundary_thickness)
      stddraw.square(position.x, position.y, length / 2)
      stddraw.setPenRadius()
      stddraw.setPenColor(self.foreground_color)
      self._set_font_size()
      stddraw.boldText(position.x, position.y, str(self.number))

   def draw_flash(self, position, bright=True, length=1):
      """Draw tile with a bright highlight to signal it is about to merge."""
      if bright:
         flash_color = Color(255, 240, 100)   # warm yellow flash
         border_color = Color(255, 200, 50)
      else:
         flash_color = self.background_color
         border_color = self.box_color
      stddraw.setPenColor(flash_color)
      stddraw.filledSquare(position.x, position.y, length / 2)
      stddraw.setPenColor(border_color)
      stddraw.setPenRadius(Tile.boundary_thickness * 2)
      stddraw.square(position.x, position.y, length / 2)
      stddraw.setPenRadius()
      stddraw.setPenColor(self.foreground_color if not bright else Color(80, 60, 0))
      self._set_font_size()
      stddraw.boldText(position.x, position.y, str(self.number))

   def draw_line_flash(self, position, bright=True, length=1):
      """Draw tile with purple highlight to signal the line is about to clear."""
      if bright:
         flash_color = Color(210, 150, 255)   # bright purple
         border_color = Color(160, 80, 220)
         text_color = Color(60, 0, 100)
      else:
         flash_color = Color(240, 220, 255)   # soft purple
         border_color = Color(190, 130, 240)
         text_color = self.foreground_color
      stddraw.setPenColor(flash_color)
      stddraw.filledSquare(position.x, position.y, length / 2)
      stddraw.setPenColor(border_color)
      stddraw.setPenRadius(Tile.boundary_thickness * 2)
      stddraw.square(position.x, position.y, length / 2)
      stddraw.setPenRadius()
      stddraw.setPenColor(text_color)
      self._set_font_size()
      stddraw.boldText(position.x, position.y, str(self.number))

   def draw_ghost(self, position, length=1):
      stddraw.setPenColor(self.GHOST_BG)
      stddraw.filledSquare(position.x, position.y, length / 2)
      stddraw.setPenColor(self.GHOST_BORDER)
      stddraw.setPenRadius(Tile.boundary_thickness)
      stddraw.square(position.x, position.y, length / 2)
      stddraw.setPenRadius()

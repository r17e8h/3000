import curses
import time
import random
import os
import re

ART_FOLDER = "art"
FPS = 30
GLYPHS = ["0", "1"]

CYCLE_PAUSE = 4.0
ASSEMBLE_DUR = 3.0
HOLD_DUR = 5.0
DISSOLVE_DUR = 2.0

ST_RAIN = 0
ST_ASSEMBLING = 1
ST_HOLD = 2
ST_DISSOLVING = 3

SGR_RE = re.compile(r"\x1b\[([0-9;]*)m")


def parse_local_sprite(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
            text = text.replace("\x1b[?25l", "").replace("\x1b[?25h", "")
    except Exception:
        return None

    metadata = []
    image_lines = []

    for line in text.splitlines():
        if "\x1b[" not in line and line.strip():
            metadata.append(line.strip())
        elif "\x1b[" in line:
            image_lines.append(line)

    if not image_lines:
        return None

    cells = {}
    img_width = 0
    img_height = len(image_lines)

    for r, line in enumerate(image_lines):
        col = 0
        fg = None
        i = 0
        n = len(line)
        while i < n:
            m = SGR_RE.match(line, i)
            if m:
                params = m.group(1).split(";") if m.group(1) else ["0"]
                j = 0
                while j < len(params):
                    p = params[j]
                    if p == "0" or p == "":
                        fg = None
                    elif p == "38" and j + 2 < len(params) and params[j + 1] == "5":
                        fg = int(params[j + 2])
                        j += 2
                    j += 1
                i = m.end()
                continue

            ch = line[i]
            if ch not in ("\n", "\r"):
                if ch != " ":
                    cells[(r, col)] = (ch, fg, False)
                col += 1
            i += 1
        img_width = max(img_width, col)
    text_start_row = img_height + 2
    for row_offset, line_text in enumerate(metadata):
        for col_offset, char in enumerate(line_text):
            cells[(text_start_row + row_offset, col_offset)] = (char, 46, True)
            if char != " ":
                cells[(text_start_row + row_offset, col_offset)] = (char, 46, True)

    total_width = max(img_width, max((len(m) for m in metadata), default=0))
    total_height = text_start_row + len(metadata)

    return {"width": total_width, "height": total_height, "cells": cells}


def load_all_art():
    sprites = []
    if not os.path.exists(ART_FOLDER):
        return sprites
    for f in os.listdir(ART_FOLDER):
        if f.endswith(".txt"):
            sprite = parse_local_sprite(os.path.join(ART_FOLDER, f))
            if sprite:
                sprites.append(sprite)
    return sprites


class MatrixEngine:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        self.stdscr.nodelay(1)
        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(1, curses.COLOR_GREEN, -1)

        self.max_y, self.max_x = self.stdscr.getmaxyx()
        self.sprites = load_all_art()
        self.playlist = list(range(len(self.sprites)))
        random.shuffle(self.playlist)
        self.playlist_index = 0

        self.drops = [
            [random.randint(-self.max_y, 0), random.randint(0, self.max_x - 1)]
            for _ in range(self.max_x // 2)
        ]
        self.state = ST_RAIN
        self.state_timer = time.time()

        self.active_sprite = None
        self.locked_pixels = {}
        self.dissolving_pixels = []

        self.color_cache = {}
        self.pair_id = 2

    def get_color_attr(self, color256):
        if color256 is None:
            return curses.color_pair(1)

        if color256 not in self.color_cache and self.pair_id < curses.COLOR_PAIRS - 1:
            try:
                curses.init_pair(self.pair_id, color256, -1)
                self.color_cache[color256] = curses.color_pair(self.pair_id)
                self.pair_id += 1
            except curses.error:
                self.color_cache[color256] = curses.color_pair(1)

        return self.color_cache.get(color256, curses.color_pair(1))

    def run(self):
        if not self.sprites:
            self.stdscr.addstr(
                self.max_y // 2,
                2,
                "No art found in art/ folder. Exiting.",
                curses.A_REVERSE,
            )
            self.stdscr.refresh()
            time.sleep(2)
            return
        msg = f" SYSTEM ONLINE: {len(self.sprites)} DATABASES LOADED "
        self.stdscr.addstr(
            self.max_y // 2, (self.max_x - len(msg)) // 2, msg, curses.A_REVERSE
        )
        self.stdscr.refresh()
        time.sleep(1.5)

        while True:
            ch = self.stdscr.getch()
            if ch != -1:
                if ch in (27, ord("q"), ord("Q")):
                    return
                elif ch in (ord(" "), ord("n"), ord("N")):
                    self.locked_pixels.clear()
                    self.dissolving_pixels.clear()
                    self.state = ST_RAIN
                    self.state_timer = 0

            self.stdscr.erase()
            self.max_y, self.max_x = self.stdscr.getmaxyx()
            now = time.time()
            elapsed_in_state = now - self.state_timer

            for drop in self.drops:
                drop[0] += 1
                if drop[0] > self.max_y:
                    drop[0] = random.randint(-5, 0)
                    if self.state == ST_ASSEMBLING and self.active_sprite:
                        missing_cols = list(
                            {
                                self.start_x + c
                                for r, c in self.active_sprite["cells"].keys()
                                if (self.start_y + r, self.start_x + c)
                                not in self.locked_pixels
                            }
                        )
                        if missing_cols and random.random() < 0.75:
                            drop[1] = random.choice(missing_cols)
                        else:
                            drop[1] = random.randint(0, self.max_x - 1)
                    else:
                        drop[1] = random.randint(0, self.max_x - 1)

                for i in range(5):
                    char_y = drop[0] - i
                    if 0 <= char_y < self.max_y and 0 <= drop[1] < self.max_x:
                        if (char_y, drop[1]) not in self.locked_pixels:
                            try:
                                attr = (
                                    curses.color_pair(1) | curses.A_BOLD
                                    if i == 0
                                    else curses.color_pair(1)
                                )
                                self.stdscr.addstr(
                                    char_y, drop[1], random.choice(GLYPHS), attr
                                )
                            except curses.error:
                                pass

            if self.state == ST_RAIN:
                if elapsed_in_state > CYCLE_PAUSE and self.sprites:
                    current_idx = self.playlist[self.playlist_index]
                    self.active_sprite = self.sprites[current_idx]
                    self.playlist_index += 1
                    if self.playlist_index >= len(self.playlist):
                        random.shuffle(self.playlist)
                        self.playlist_index = 0

                    self.start_y = max(
                        0, (self.max_y - self.active_sprite["height"]) // 2
                    )
                    self.start_x = max(
                        0, (self.max_x - self.active_sprite["width"]) // 2
                    )
                    self.state = ST_ASSEMBLING
                    self.state_timer = now

            elif self.state == ST_ASSEMBLING:
                if not self.active_sprite:
                    continue
                chance = min(elapsed_in_state / ASSEMBLE_DUR, 1.0)

                for drop in self.drops:
                    head_y, head_x = drop[0], drop[1]
                    local_r = head_y - self.start_y
                    local_c = head_x - self.start_x

                    if (
                        0 <= local_r < self.active_sprite["height"]
                        and 0 <= local_c < self.active_sprite["width"]
                    ):
                        if (local_r, local_c) in self.active_sprite["cells"]:
                            if random.random() < chance:
                                self.locked_pixels[(head_y, head_x)] = (
                                    self.active_sprite["cells"][(local_r, local_c)]
                                )

                if len(self.locked_pixels) >= len(self.active_sprite["cells"]):
                    self.state = ST_HOLD
                    self.state_timer = now

            elif self.state == ST_HOLD:
                if not self.active_sprite:
                    continue
                if elapsed_in_state > HOLD_DUR:
                    for (y, x), (char, color256, is_text) in self.locked_pixels.items():
                        self.dissolving_pixels.append([y, x, char, color256, is_text])
                    self.locked_pixels.clear()
                    self.state = ST_DISSOLVING
                    self.state_timer = now

            elif self.state == ST_DISSOLVING:
                alive = []
                for p in self.dissolving_pixels:
                    p[0] += random.randint(1, 3)
                    if random.random() < 0.2:
                        p[2] = random.choice(GLYPHS)

                    if p[0] < self.max_y:
                        alive.append(p)
                        try:
                            self.stdscr.addstr(
                                p[0], p[1], p[2], self.get_color_attr(p[3])
                            )
                        except curses.error:
                            pass

                self.dissolving_pixels = alive
                if not self.dissolving_pixels:
                    self.state = ST_RAIN
                    self.state_timer = now

            for (y, x), (char, color256, is_text) in self.locked_pixels.items():
                try:
                    self.stdscr.addstr(
                        y, x, char, self.get_color_attr(color256) | curses.A_BOLD
                    )
                except curses.error:
                    pass

            self.stdscr.refresh()
            time.sleep(1.0 / FPS)


if __name__ == "__main__":
    try:
        curses.wrapper(lambda stdscr: MatrixEngine(stdscr).run())
    except KeyboardInterrupt:
        pass


# Project 3000

> "I love you 3000."

**Project 3000** is a custom, terminal-based screensaver and art display engine built in Python. It features a state-machine physics engine that renders "Matrix-style" digital rain that interacts with high-resolution, true-color pixel art. Characters from the Marvel Universe are dynamically assembled by the rain, held on screen to display their database dossier, and then dissolved using sub-cell gravity physics.

##  Core Features

* **Smart Rain Physics:** Digital rain actively hunts down missing pixels to construct images organically.
* **True-Color Terminal Rendering:** Utilizes 256-color SGR escape codes for vibrant, high-fidelity character art.
* **Layered Rendering:** A Z-index system allows matrix rain to flow behind assembled character art, creating a high-speed parallax effect.
* **Dynamic Lore Assembly:** Dossier metadata is parsed and rendered as physical components of the character sprite.
* **Sub-Cell Dissolve:** Characters melt away using float-based gravity calculations for a smooth, dramatic "shatter" effect.
* **Playlist Shuffle:** A smart queue system ensures every character is displayed sequentially before reshuffling the deck.
* **Global Command Access:** Wired into your system shell for instant invocation.

##  Technical Stack

* **Language:** Python 3
* **Library:** `curses` (for terminal UI and high-frequency rendering)
* **Terminal:** Optimized for Kitty (GPU-accelerated, true-color support)
* **Art Processor:** `chafa` (for generating symbol-based terminal assets)

##  Installation

1. **Clone the repository:**
```bash
git clone https://github.com/r17e8h/3000.git
cd 3000

```


2. **Setup virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```


3. **Global Alias (Linux):**
Add this to your `~/.bashrc` to invoke the screensaver from any directory:
```bash
alias marvel="~/Projects/3000/venv/bin/python ~/Projects/3000/marvel.py"

```


*Reload your config:* `source ~/.bashrc`

## Controls

* **`Space` / `N**`: Skip current character and force immediate assembly of the next hero/villain.
* **`Q` / `ESC**`: Exit the screensaver.

## Asset Generation

To add new characters to the `art/` directory, use `chafa` to generate the required symbol-based output:

```bash
chafa --format=symbols --symbols vhalf --colors 256 -s 90x90 input_image.png > art/new_char.txt

```

*Note: Ensure you strip all background transparency before converting to avoid "ghost box" artifacts.*

## Database Integration

Prepend your character lore directly to the top of your generated `.txt` files. The engine automatically parses lines without color escape codes as database entries:

```text
DATABASE: [NAME]
IDENTITY: [TRUE NAME]
STATUS: [ACTIVE/INACTIVE]
THREAT LEVEL: [CLASS]

\x1b[38;5;... (chafa color data follows)

```

##  Licence

**MIT** 
## 
Developed for Linux terminal environments.

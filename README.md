# Terminal Games

![Python](https://img.shields.io/badge/python-3.7%2B-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-555555?logo=gnometerminal&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)

A collection of classic games and a relaxing screen, all in a single Python file. Pick one from the menu and play right in your terminal. No installs, no dependencies.

## Games

| # | Game | Description |
|---|------|-------------|
| 1 | **Snake** | Eat, grow and don't hit yourself. It speeds up as you score. |
| 2 | **Wordle** | Guess the 5-letter Spanish word in 6 tries. Green, yellow and gray hints. |
| 3 | **Tetris** | 10x20 board, rotation with wall kicks, levels and scoring. |
| 4 | **Roguelike** | Procedurally generated rooms, goblins that chase you, potions and stairs. Escape from depth 5. |
| 5 | **Game of Life** | Conway's cellular automaton on a wrapping grid. |
| 6 | **Hangman** | Guess the word before the drawing is complete. |
| 7 | **Minesweeper** | 12x10 board with 15 mines. The first click is always safe. |
| 8 | **Pong** | Play against an AI first to 7 points. |
| 9 | **Chill** | A big ASCII clock with circles and ghosts that fade in and out. |

## Getting started

### Requirements

- Python 3.7 or newer
- A modern terminal with ANSI and Unicode support (Windows Terminal, current PowerShell, or any Linux/macOS terminal)
- Recommended size: at least 80x30

### Run it

```bash
git clone https://github.com/bagpotato/terminal-games.git
cd terminal-games
python juegos.py
```

On Linux and macOS use `python3 juegos.py`. On Windows, `py juegos.py` also works.

## Controls

**Menu:** `↑` `↓` + `Enter`, or press the game number. `q` / `Esc` to quit.

Inside any game, `q` or `Esc` takes you back to the menu. In Wordle and Hangman only `Esc` works, since `q` is a letter.

| Game | Keys |
|------|------|
| Snake | Arrows / `WASD` |
| Wordle | Letters, `Enter` to submit, `Backspace` to delete |
| Tetris | `←` `→` move, `↑` rotate, `↓` soft drop, `Space` hard drop |
| Roguelike | Arrows / `WASD` to move and attack, `Space` to wait |
| Game of Life | `Space` pause, `r` new random board |
| Hangman | Letters |
| Minesweeper | Arrows move the cursor, `Space` / `Enter` reveal, `f` flag |
| Pong | `↑` `↓` / `W` `S` |
| Chill | Just relax |

## How it works

Everything lives in `juegos.py`:

- **Input:** non-blocking keyboard reading with `msvcrt` on Windows and `termios` + `select` on Unix.
- **Rendering:** ANSI escape codes on the alternate screen buffer, so your terminal is left untouched when you exit.
- **Chill mode:** 24-bit color with brightness scaled over each sprite's lifetime to get the fade effect.
- **Games:** each one is a plain function (`snake()`, `tetris()`, ...) registered in the `JUEGOS` list, so adding a new one is a single entry.

## Adding a game

1. Write a function that runs the game loop and returns when it ends.
2. Add it to the `JUEGOS` list:

```python
JUEGOS = [
    ("Snake", snake),
    # ...
    ("My game", my_game),
]
```

Use `poll(dt)` for tick-based games, `key()` for turn-based ones, and `final(msg)` to show the end screen.

## Notes

- Wordle accepts any 5-letter word as a guess. Secret words come from a built-in list of Spanish words without accents.
- The legacy Windows console (`cmd.exe` on old builds) may not render colors or Unicode correctly.
- Chill mode assumes a dark terminal background, since the fade goes to black.

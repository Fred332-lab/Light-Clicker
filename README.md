# 💡 Light Clicker

> A bulb-clicking idle game built with Pygame — manage heat, buy upgrades, unlock achievements, and play minigames to rack up the highest score.

**Version:** 0.2.2 (Under Construction) &nbsp;·&nbsp; **Engine:** Python + Pygame

---

## 🎮 Gameplay

Click the lightbulb to earn points. The longer you keep it on, the more it heats up — let it overheat and you'll lose a chunk of your score as a penalty. Balance clicking with cooling, invest in upgrades, and chase achievements to power up your bulb.

### Core Loop

1. **Click** the bulb (or press `Space`) to earn points based on your click income.
2. Watch the **temperature bar** — if it hits 100°C, the bulb overheats and you lose a % of your score.
3. Toggle the bulb off to let it cool, then click again when it's safe.
4. Spend your score on **upgrades** to boost click income, passive income, and cooling.
5. Unlock **achievements** for bonus stats and special upgrade slots.

### Difficulty Levels

| Level  | Room Temperature | Effect                        |
|--------|-----------------|-------------------------------|
| Easy   | +18°C           | Bulb cools quickly            |
| Medium | +36°C           | Balanced challenge            |
| Hard   | +52°C           | Heat builds fast              |
| Hell   | +80°C           | Extremely punishing heat      |

Difficulty must be chosen at the start of a run and cannot be changed later.

### Beginner's Luck

New players get a temporary boost: click income is multiplied (up to 4×) and upgrade costs are reduced (down to 40%). This bonus fades as you buy your first 5 upgrades.

---

## 🛒 Upgrades

Upgrades are purchased from the in-game menu and fall into four categories:

| Category      | Examples                                    | Effect                          |
|---------------|---------------------------------------------|---------------------------------|
| **Click**     | Multi Click, Mega Click, Hyper Click        | +click income per level         |
| **Passive**   | Solar Power, Nuclear Power, Antimatter Plant | +score per second               |
| **Thermal**   | Overclock, Undervolt, LED Light, Copper Heat Sink | Trade heat vs. income    |
| **Penalty**   | Consumers Discount, Insurance Policy        | Reduces overheat score penalty  |
| **Randomizer**| Randomizer (up to 50×)                     | Random stat changes each buy    |

Certain upgrades are locked behind achievements. Upgrade costs scale with each purchase.

---

## 🏆 Achievements

Achievements track gameplay milestones (clicks, overheats, upgrades bought, score, playtime, and minigame sessions) and reward the player with permanent stat bonuses:

- `+click income`
- `+passive income`
- `+cooling rate`
- `-overheat penalty`

Some achievements also unlock additional upgrade slots unavailable in the base shop.

Press `A` or open the **Achievements** panel from the side menu to track progress.

---

## 🎲 Minigames

Access minigames from the side menu or press `G`. Playing minigames affects your score and counts toward certain achievements.

| Game          | Description                          |
|---------------|--------------------------------------|
| **Blackjack** | Classic card game against the house  |
| **Rock Paper Scissors** | Best-of series RPS       |
| **Plinko**    | Drop a ball, win score multipliers   |

Minigames are auto-discovered at startup — any module added to the `minigames/` folder that exposes a class with `.name`, `.draw`, and `.handle_event` will be loaded automatically.

---

## ⌨️ Controls

| Input             | Action                     |
|-------------------|----------------------------|
| `Click` bulb      | Earn points                |
| `Space`           | Earn points (keyboard)     |
| `A`               | Toggle achievements panel  |
| `G`               | Toggle minigame hub        |
| `Ctrl+S`          | Quick save                 |
| `Esc`             | Close any open menu        |

---

## 💾 Save System

The game auto-saves on exit and auto-loads on startup. Saves are stored as `savegame.json` in the game directory with a SHA-256 checksum to prevent tampering.

A `submit.json` file is also generated (via **Exit → SUBMIT**) for score submission.

---

## 🖥️ Requirements

- Python 3.8+
- [Pygame](https://www.pygame.org/) (`pip install pygame`)

---

## 🚀 Running the Game

```bash
git clone https://github.com/your-username/light-clicker.git
cd light-clicker
pip install pygame
python main.py
```

---

## 📁 Project Structure

```
light-clicker/
├── main.py            # Main game loop, bulb logic, UI
├── achievements.py    # Achievement system, rewards, unlockable upgrades
├── gra.py             # (auxiliary module)
├── savegame.json      # Auto-generated save file
├── submit.json        # Auto-generated score submission file
└── minigames/
    ├── __init__.py    # MiniGameHub facade + auto-loader
    ├── blackjack.py   # Blackjack minigame
    ├── rps.py         # Rock Paper Scissors minigame
    └── plinko.py      # Plinko minigame
```

---

## 🎨 Visual Style

The game uses the [Catppuccin Mocha](https://github.com/catppuccin/catppuccin) color palette and supports four resolutions: 480p, 720p, 1080p, and 1440p. The window is resizable and all rendering scales automatically.

---

## 🔧 Adding a Custom Minigame

1. Create a new file in `minigames/`, e.g. `minigames/mygame.py`.
2. Define a class with:
   - `name` — string attribute with the game's display name
   - `draw(screen)` — renders the game
   - `handle_event(event, bulb)` — handles input
3. The auto-loader will detect and register it on next startup.

---

## 📝 License

This project is currently **under construction**. License TBD.

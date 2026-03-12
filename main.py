# main.py  –  Zarowka Clicker  v0.0.1
# Plik 1/2: Główna pętla gry, logika żarówki, UI
# Plik 2/2: achievements.py  (system osiągnięć, nagrody, odblokowane ulepszenia)
# Folder:   minigames/  (blackjack, rps, plinko)

import pygame
import math
import random
import json
import os
import hashlib
import time
import importlib
import pkgutil

import achievements as ach_mod
from achievements import (
    AchievementSystem, UNLOCKABLE_UPGRADES,
    ACHIEVEMENTS_DEF, ACHIEVEMENT_REWARDS,
    ScrollablePanel,
)
from minigames import MiniGameHub

# ──────────────────────────────────────────────────────────────────────────────
# KONFIGURACJA
# ──────────────────────────────────────────────────────────────────────────────
BASE_W, BASE_H   = 1920, 1080
SAVE_FILE        = "savegame.json"
SUBMIT_FILE      = "submit.json"
SAVE_VERSION     = 2
GAME_VERSION     = "0.0.1"
GAME_NAME        = "Light Clicker"
PLAYER_NAME      = "Fryderyk"

RESOLUTIONS = {
    "480p  (854x480)":   (854,  480),
    "720p  (1280x720)":  (1280, 720),
    "1080p (1920x1080)": (1920, 1080),
    "1440p (2560x1440)": (2560, 1440),
}

play_time  = 0.0
render_w, render_h = BASE_W, BASE_H

# ──────────────────────────────────────────────────────────────────────────────
# KOLORY  (Catppuccin Mocha)
# ──────────────────────────────────────────────────────────────────────────────
class CatppuccinMocha:
    rosewater = (245, 224, 220)
    red       = (243, 139, 168)
    yellow    = (249, 226, 175)
    green     = (166, 227, 161)
    teal      = (148, 226, 213)
    sky       = (137, 220, 235)
    blue      = (137, 180, 250)
    lavender  = (180, 190, 254)
    peach     = (250, 179, 135)
    mauve     = (203, 166, 247)
    text      = (205, 214, 244)
    subtext1  = (186, 194, 222)
    subtext0  = (166, 173, 200)
    overlay2  = (147, 153, 178)
    overlay1  = (127, 132, 156)
    overlay0  = (108, 112, 134)
    surface2  = (88,  91,  112)
    surface1  = (69,  71,  90)
    surface0  = (49,  50,  68)
    base      = (30,  30,  46)
    mantle    = (24,  24,  37)
    crust     = (17,  17,  27)

C = CatppuccinMocha()

_FONT_CACHE: dict = {}
def _font(size: int) -> pygame.font.Font:
    if size not in _FONT_CACHE:
        _FONT_CACHE[size] = pygame.font.Font(None, size)
    return _FONT_CACHE[size]

def _txt(font, text, color):
    try:    return font.render(text, True, color)
    except: return font.render("?",  True, color)


# ──────────────────────────────────────────────────────────────────────────────
# AUTO MINIGAME LOADER
# Scans the minigames/ package and returns a dict {name: module}
# Any module inside minigames/ that exposes a class with a `name` attribute
# and a `draw` / `handle_event` method is considered a valid mini-game.
# ──────────────────────────────────────────────────────────────────────────────
def discover_minigames() -> dict:
    """
    Automatically import every sub-module of the `minigames` package and
    collect classes that look like mini-games (have .name, .draw, .handle_event).

    Returns:
        dict mapping game_name -> game_class
    """
    import minigames as _mg_pkg

    found = {}
    pkg_path = _mg_pkg.__path__
    pkg_name = _mg_pkg.__name__

    for _finder, module_name, _ispkg in pkgutil.iter_modules(pkg_path):
        full_name = f"{pkg_name}.{module_name}"
        try:
            mod = importlib.import_module(full_name)
        except Exception as e:
            print(f"[AutoLoader] Pominięto moduł {full_name}: {e}")
            continue

        # Inspect module for game classes
        for attr_name in dir(mod):
            obj = getattr(mod, attr_name)
            if (
                isinstance(obj, type)
                and hasattr(obj, "name")
                and hasattr(obj, "draw")
                and hasattr(obj, "handle_event")
                and obj.__module__ == full_name  # only classes defined in this module
            ):
                game_name = getattr(obj, "name", attr_name)
                found[game_name] = obj
                print(f"[AutoLoader] Znaleziono grę: '{game_name}' w {full_name}")

    if not found:
        print("[AutoLoader] Brak dodatkowych mini-gier (lub MiniGameHub zarządza nimi wewnętrznie).")
    return found


# ──────────────────────────────────────────────────────────────────────────────
# ŻARÓWKA  (model gry)
# ──────────────────────────────────────────────────────────────────────────────
class Zarowka:
    # ── Beginner's Luck ──────────────────────────────────────────────────────
    BEGINNER_LUCK_UPGRADES_THRESHOLD = 5
    BEGINNER_LUCK_CLICK_MULT         = 4
    BEGINNER_LUCK_COST_MULT          = 0.4

    BASE_UPGRADES = {
        # Klikanie
        "Multi Click":        {"cost":    200, "owned": 0, "income_bonus":   2,   "max": 8},
        "Mega Click":         {"cost":  4_000, "owned": 0, "income_bonus":   8,   "max": 6},
        "Ultra Click":        {"cost": 40_000, "owned": 0, "income_bonus":  30,   "max": 5},
        "Hyper Click":        {"cost":400_000, "owned": 0, "income_bonus": 100,   "max": 4},
        # Pasywne
        "Solar Power":        {"cost":  1_500, "owned": 0, "passive_bonus":  2,   "max": 5},
        "Coal Power":         {"cost": 20_000, "owned": 0, "passive_bonus":  6,   "max": 4},
        "Nuclear Power":      {"cost":180_000, "owned": 0, "passive_bonus": 20,   "max": 3},
        "Antimatter Plant":   {"cost":2_000_000,"owned":0, "passive_bonus": 90,   "max": 2},
        # Temperaturowe
        "Overclock":  {"cost":  8_000, "owned": 0, "income_bonus":  6,  "cooling_bonus": -2.0, "max": 3},
        "Undervolt":  {"cost":  8_000, "owned": 0, "income_bonus": -3,  "cooling_bonus":  2.0, "max": 3},
        "LED light":  {"cost":100_000, "owned": 0, "income_bonus": 30,  "cooling_bonus":  3.0, "max": 1},
        "Copper Heat Sink":{"cost":10_000,"owned":0,"cooling_bonus": 1.5,"max":4},
        # Kara
        "Consumers Discount": {"cost":150_000, "owned": 0, "penalty": -2, "max": 3},
        "Insurance Policy":   {"cost":1_500_000,"owned": 0, "penalty": -3, "max": 2},
        # Losowe
        "Randomizer": {"cost": 25_000, "owned": 0, "max": 50},
    }

    DIFFICULTY = {
        "Easy":   {"room_temp": 18, "label": "Easy   (pokój +18°C)"},
        "Medium": {"room_temp": 36, "label": "Medium (pokój +36°C)"},
        "Hard":   {"room_temp": 52, "label": "Hard   (pokój +52°C)"},
        "Hell":   {"room_temp": 80, "label": "Hell   (pokój +80°C)"},
    }

    def __init__(self):
        self.loaded = False
        self.score    = 0.0
        self.income   = 3
        self.passive_income    = 0
        self.temperature       = 20.0
        self.room_temperature  = 20.0
        self.temperature_increase = 25.0   # szybciej grzeje
        self.temperature_decrease = 8.0    # wolniej chłodzi
        self.overheat_threshold   = 100
        self.penalty              = 15
        self.state  = 0

        # ── Opóźnienie chłodzenia ─────────────────────────────────────────────
        # Po wyłączeniu żarówki odczekaj _cooling_delay sekund zanim zacznie chłodzić.
        self._cooling_delay     = 0.0
        self._cooling_delay_max = 1.5    # 1.5s bezwładności – dostosuj wg uznania

        self.width  = 260
        self.height = 260
        self.location = pygame.Rect(
            render_w//2 - self.width//2,
            render_h//2 - self.height//2,
            self.width, self.height,
        )

        self.beginners_luck_active   = True
        self.beginners_luck_notified = False

        self.total_clicks              = 0
        self.total_overheats           = 0
        self.total_upgrades_bought     = 0
        self.score_since_last_overheat = 0.0

        self.blackajck_played = 0
        self.rps_played = 0
        self.plinko_played = 0

        self.ach_income_bonus      = 0
        self.ach_passive_bonus     = 0
        self.ach_cooling_bonus     = 0.0
        self.ach_penalty_reduction = 0

        import copy
        self.upgrades: dict = copy.deepcopy(self.BASE_UPGRADES)

        self.newly_unlocked_upgrades: set = set()

        self.current_difficulty = "NONE"
        self.difficulty_locked  = False
        self.random_seed        = 123456

    # ── Helpers ───────────────────────────────────────────────────────────────
    def reposition(self):
        self.location = pygame.Rect(
            render_w//2 - self.width//2,
            render_h//2 - self.height//2,
            self.width, self.height,
        )

    def fmt_score(self) -> str:
        s = int(self.score)
        if s >= 1_000_000_000: return f"{s/1_000_000_000:.2f}G"
        if s >= 1_000_000:     return f"{s/1_000_000:.2f}M"
        if s >= 1_000:         return f"{s/1_000:.1f}k"
        return str(s)

    def _bl_click_mult(self) -> float:
        if not self.beginners_luck_active:
            return 1.0
        t = self.BEGINNER_LUCK_UPGRADES_THRESHOLD
        progress = min(self.total_upgrades_bought, t) / t
        return max(1.0, self.BEGINNER_LUCK_CLICK_MULT * (1.0 - progress) + 1.0 * progress)

    def _bl_cost_mult(self) -> float:
        if not self.beginners_luck_active:
            return 1.0
        t = self.BEGINNER_LUCK_UPGRADES_THRESHOLD
        progress = min(self.total_upgrades_bought, t) / t
        return self.BEGINNER_LUCK_COST_MULT + (1.0 - self.BEGINNER_LUCK_COST_MULT) * progress

    def _update_beginners_luck(self):
        if self.beginners_luck_active and \
                self.total_upgrades_bought >= self.BEGINNER_LUCK_UPGRADES_THRESHOLD:
            self.beginners_luck_active = False

    # ── Kliknięcie ────────────────────────────────────────────────────────────
    def click(self):
        gained = max(1, int(self.income * self._bl_click_mult()))
        self.score += gained
        self.score_since_last_overheat += gained
        self.total_clicks += 1
        self.state = 1 - self.state

    # ── Efektywny koszt ulepszenia ────────────────────────────────────────────
    def effective_cost(self, name: str) -> int:
        u = self.upgrades.get(name)
        if u is None:
            return 0
        return max(1, int(u["cost"] * self._bl_cost_mult()))

    # ── Kup ulepszenie ────────────────────────────────────────────────────────
    def buy_upgrade(self, name: str):
        u = self.upgrades.get(name)
        if u is None:
            return

        cost = self.effective_cost(name)

        if name == "Randomizer":
            if self.score < cost or u["owned"] >= u["max"]:
                return
            rng     = random.Random(self.random_seed)
            income  = rng.randint(-30, 50)
            passive = rng.randint(-15, 20)
            cooling = rng.randint(-3,   4)
            self.random_seed += 10
            self.score       -= cost
            u["owned"]       += 1
            u["cost"]         = int(u["cost"] * 1.6)
            self.income              += income
            self.passive_income      += passive
            self.temperature_increase -= cooling
            self.total_upgrades_bought += 1
            self._update_beginners_luck()
            return

        if self.score < cost or u["owned"] >= u["max"]:
            return
        self.score    -= cost
        u["owned"]    += 1
        self.total_upgrades_bought += 1

        if "income_bonus"  in u: self.income              += u["income_bonus"]
        if "passive_bonus" in u: self.passive_income      += u["passive_bonus"]
        if "cooling_bonus" in u:
            self.temperature_increase -= u["cooling_bonus"]
            self.temperature_decrease += u["cooling_bonus"] / 2
        if "penalty"       in u: self.penalty              += u["penalty"]

        u["cost"] = int(u["cost"] * 1.4)

        self._update_beginners_luck()

    # ── Trudność ──────────────────────────────────────────────────────────────
    def set_difficulty(self, name: str):
        if self.difficulty_locked:
            return
        self.current_difficulty = name
        self.room_temperature   = self.DIFFICULTY[name]["room_temp"]
        self.difficulty_locked  = True

    # ── Tick ──────────────────────────────────────────────────────────────────
    def tick(self, fps: int):
        gained = self.passive_income / fps
        self.score                     += gained
        self.score_since_last_overheat += gained

        if self.state:
            self.temperature += self.temperature_increase / fps
            if self.temperature >= self.overheat_threshold:
                self.state         = 0
                self.total_overheats += 1
                self.score_since_last_overheat = 0.0
                effective_penalty = self.penalty
                if self.beginners_luck_active:
                    effective_penalty = max(0, effective_penalty // 2)
                self.score = max(0.0, self.score * (1 - effective_penalty / 100))
        else:
            self.temperature = max(
                self.room_temperature,
                self.temperature - self.temperature_decrease / fps,
            )

    # ── Zapis / odczyt ────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        data = {
            "save_version":  SAVE_VERSION,
            "game_version":  GAME_VERSION,
            "player":        PLAYER_NAME,
            "score":         round(self.score, 3),
            "play_time":     int(play_time),
            "random_seed":   self.random_seed,
            "difficulty":    self.current_difficulty,
            "income":        self.income,
            "passive_income":self.passive_income,
            "temperature":   round(self.temperature, 2),
            "room_temperature": self.room_temperature,
            "temperature_increase": round(self.temperature_increase, 3),
            "temperature_decrease": round(self.temperature_decrease, 3),
            "overheat_threshold": self.overheat_threshold,
            "penalty":       self.penalty,
            "total_clicks":  self.total_clicks,
            "total_overheats": self.total_overheats,
            "total_upgrades_bought": self.total_upgrades_bought,
            "score_since_last_overheat": round(self.score_since_last_overheat, 3),
            "ach_income_bonus":      self.ach_income_bonus,
            "ach_passive_bonus":     self.ach_passive_bonus,
            "ach_cooling_bonus":     self.ach_cooling_bonus,
            "ach_penalty_reduction": self.ach_penalty_reduction,
            "beginners_luck_active": self.beginners_luck_active,
            "upgrades": {
                n: {"owned": u["owned"], "cost": u["cost"]}
                for n, u in self.upgrades.items()
            },
            "timestamp": int(time.time()),
            "blackjack": self.blackajck_played,
            "rps": self.rps_played,
            "plinko": self.plinko_played,
        }
        data["checksum"] = _checksum(data)
        return data

    def load_from_dict(self, data: dict):
        global play_time

        exp  = data.get("checksum", "")
        tmp  = {k: v for k, v in data.items() if k != "checksum"}
        if _checksum(tmp) != exp:
            print("WARNING: checksum mismatch – pomijam wczytanie")
            return

        self.score             = data.get("score", 0.0)
        play_time              = data.get("play_time", 0)
        self.random_seed       = data.get("random_seed", 123456)
        self.temperature       = data.get("temperature", 20.0)
        self.room_temperature  = data.get("room_temperature", 20.0)
        self.overheat_threshold= data.get("overheat_threshold", 100)
        self.penalty           = data.get("penalty", 15)
        self.total_clicks              = data.get("total_clicks", 0)
        self.total_overheats           = data.get("total_overheats", 0)
        self.total_upgrades_bought     = data.get("total_upgrades_bought", 0)
        self.score_since_last_overheat = data.get("score_since_last_overheat", 0.0)
        self.ach_income_bonus      = data.get("ach_income_bonus", 0)
        self.ach_passive_bonus     = data.get("ach_passive_bonus", 0)
        self.ach_cooling_bonus     = data.get("ach_cooling_bonus", 0.0)
        self.ach_penalty_reduction = data.get("ach_penalty_reduction", 0)
        self.current_difficulty = data.get("difficulty", "NONE")
        self.difficulty_locked  = self.current_difficulty != "NONE"
        self.beginners_luck_active = data.get("beginners_luck_active", False)
        self.blackajck_played = data.get("blackjack", 0)
        self.rps_played = data.get("rps", 0)
        self.plinko_played = data.get("plinko", 0)

        saved = data.get("upgrades", {})

        import copy
        self.upgrades = copy.deepcopy(self.BASE_UPGRADES)
        for name, tmpl in UNLOCKABLE_UPGRADES.items():
            if name in saved:
                self.upgrades[name] = dict(tmpl)

        for name, u in self.upgrades.items():
            sv = saved.get(name, {})
            u["owned"] = min(sv.get("owned", 0), u["max"])
            u["cost"]  = sv.get("cost", u["cost"])

        self.income               = 3
        self.passive_income       = 0
        self.temperature_increase = 25.0   # zawsze od bazy – upgrades przeliczane poniżej
        self.temperature_decrease = 8.0    # zawsze od bazy – upgrades przeliczane poniżej
        self.penalty              = 15

        for name, u in self.upgrades.items():
            for _ in range(u["owned"]):
                if "income_bonus"  in u: self.income              += u["income_bonus"]
                if "passive_bonus" in u: self.passive_income      += u["passive_bonus"]
                if "cooling_bonus" in u:
                    self.temperature_increase -= u["cooling_bonus"]
                    self.temperature_decrease += u["cooling_bonus"] / 2
                if "penalty"       in u: self.penalty              += u["penalty"]

        self.income              += self.ach_income_bonus
        self.passive_income      += self.ach_passive_bonus
        self.temperature_decrease+= self.ach_cooling_bonus
        self.penalty              = max(0, self.penalty - self.ach_penalty_reduction)
        self.overheat_threshold   = data.get("overheat_threshold", 100)
        self.loaded = True
        self.reposition()  # synchronizuj hitbox z aktualnym rozmiarem ekranu


# ──────────────────────────────────────────────────────────────────────────────
# SIDE MENU
# ──────────────────────────────────────────────────────────────────────────────
class SideMenu:
    W          = 340
    BTN_H      = 36
    BTN_GAP    = 8
    BOTTOM_PAD = 16

    def __init__(self, screen, bulb: Zarowka):
        self.screen  = screen
        self.bulb    = bulb
        self.visible = True
        self.fh      = 36
        self.font    = _font(self.fh - 2)
        self.fsm     = _font(22)
        self.diff_rect    = pygame.Rect(0, 0, self.W, self.BTN_H)
        self.upgrade_rect = pygame.Rect(0, 0, self.W, self.BTN_H)
        self.exit_rect    = pygame.Rect(0, 0, self.W, self.BTN_H)
        self.achiev_rect  = pygame.Rect(0, 0, self.W, self.BTN_H)
        self.games_rect   = pygame.Rect(0, 0, self.W, self.BTN_H)
        self._build_btn_rects()

    def _build_btn_rects(self):
        step = self.BTN_H + self.BTN_GAP
        base = render_h - self.BOTTOM_PAD - 5 * step
        self.diff_rect    = pygame.Rect(4, base,          self.W - 8, self.BTN_H)
        self.upgrade_rect = pygame.Rect(4, base + step,   self.W - 8, self.BTN_H)
        self.exit_rect    = pygame.Rect(4, base + 2*step, self.W - 8, self.BTN_H)
        self.achiev_rect  = pygame.Rect(4, base + 3*step, self.W - 8, self.BTN_H)
        self.games_rect   = pygame.Rect(4, base + 4*step, self.W - 8, self.BTN_H)
        self.sep_y        = base - 12
        self.content_clip = self.sep_y - 2

    def draw(self, ach_sys: AchievementSystem):
        if not self.visible:
            return
        b = self.bulb
        self._build_btn_rects()

        pygame.draw.rect(self.screen, C.mantle, (0, 0, self.W, render_h))
        pygame.draw.line(self.screen, C.yellow, (self.W, 0), (self.W, render_h), 2)

        old_clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(0, 0, self.W, self.content_clip))

        y = self.fh // 2
        hot = b.temperature > b.overheat_threshold - 12

        effective_click     = max(1, int(b.income * b._bl_click_mult())) if b.beginners_luck_active else b.income
        effective_cost_hint = f" [BL {b._bl_click_mult():.1f}x]" if b.beginners_luck_active else ""

        stats = [
            (f"Score: {b.fmt_score()}",                       C.text),
            (f"Klik: {effective_click}{effective_cost_hint}", C.peach if b.beginners_luck_active else C.text),
            (f"Passive/s: {b.passive_income}",                C.text),
            (f"Temp: {b.temperature:.1f}/{b.overheat_threshold}C",
             C.red if hot else C.text),
            (f"Chlodz: {b.temperature_decrease:.1f}/s",       C.sky),
            (f"Kara:  {b.penalty}%",                          C.peach),
            (f"Diff:  {b.current_difficulty}",                C.text),
        ]
        for txt, col in stats:
            self.screen.blit(_txt(self.font, txt, col), (12, y))
            y += self.fh

        if b.beginners_luck_active:
            pygame.draw.line(self.screen, C.peach, (8, y), (self.W-8, y), 1)
            y += 4
            self.screen.blit(_txt(self.fsm, "** BEGINNER'S LUCK **", C.peach), (12, y))
            y += 22
            remaining = max(0, b.BEGINNER_LUCK_UPGRADES_THRESHOLD - b.total_upgrades_bought)
            self.screen.blit(_txt(self.fsm, f"  Zostalo ulepszen: {remaining}", C.peach), (12, y))
            y += 20
            self.screen.blit(_txt(self.fsm, "  (ceny obnizzone!)", C.overlay1), (12, y))
            y += 24

        pygame.draw.line(self.screen, C.green, (8, y), (self.W-8, y), 1)
        y += 4
        self.screen.blit(_txt(self.fsm, "== Buffy z Osiagniec ==", C.green), (12, y))
        y += 22
        buffs = []
        if b.ach_income_bonus:      buffs.append((f"  +{b.ach_income_bonus} klik/ach",    C.green))
        if b.ach_passive_bonus:     buffs.append((f"  +{b.ach_passive_bonus} pass/ach",   C.green))
        if b.ach_cooling_bonus:     buffs.append((f"  +{b.ach_cooling_bonus:.0f} chlodz", C.green))
        if b.ach_penalty_reduction: buffs.append((f"  -{b.ach_penalty_reduction}% kara",  C.green))
        if not buffs:               buffs = [("  (brak)", C.overlay1)]
        for bl, col in buffs:
            self.screen.blit(_txt(self.fsm, bl, col), (12, y))
            y += 20
        y += 26
        mg_stats = [
            (f"  Blackjack: {b.blackajck_played}x", C.subtext1),
            (f"  RPS:       {b.rps_played}x",       C.subtext1),
            (f"  Plinko:    {b.plinko_played}x",    C.subtext1),
        ]
        for ml, col in mg_stats:
            y += 20

        self.screen.set_clip(old_clip)

        pygame.draw.line(self.screen, C.yellow, (8, self.sep_y), (self.W-8, self.sep_y), 1)

        def btn(rect, label, bg, border, fg):
            pygame.draw.rect(self.screen, bg,     rect)
            pygame.draw.rect(self.screen, border, rect, 2)
            s = _txt(self.font, label, fg)
            self.screen.blit(s, s.get_rect(center=rect.center))

        if not b.difficulty_locked:
            btn(self.diff_rect, "Difficulty",     C.surface1, C.yellow,    C.text)
        btn(self.upgrade_rect,  "Upgrades",       C.surface1, C.yellow,    C.text)
        btn(self.exit_rect,     "Exit / Save",    C.red,      C.rosewater, C.base)

        done  = len(ach_sys.unlocked)
        total = len(ACHIEVEMENTS_DEF)
        btn(self.achiev_rect, f"Achiev. {done}/{total}", C.surface0, C.yellow, C.text)
        btn(self.games_rect,  "🎲 Mini Gry",            C.surface0, C.mauve,  C.mauve)

        if b.newly_unlocked_upgrades:
            n   = len(b.newly_unlocked_upgrades)
            tag = _txt(_font(24), f" +{n} NOWE! ", C.base)
            tr  = tag.get_rect(topright=(self.W - 8, self.upgrade_rect.y + 2))
            pygame.draw.rect(self.screen, C.mauve, tr.inflate(4, 2))
            self.screen.blit(tag, tr)

    def handle_event(self, event, upgrade_menu, difficulty_menu):
        if not self.visible:
            return False, False, False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            p = event.pos
            if self.upgrade_rect.collidepoint(p):
                upgrade_menu.open(); return True, False, False
            if self.exit_rect.collidepoint(p):
                exit_menu.open();    return True, False, False
            if not self.bulb.difficulty_locked and self.diff_rect.collidepoint(p):
                difficulty_menu.open(); return True, False, False
            if self.achiev_rect.collidepoint(p):
                return True, True, False
            if self.games_rect.collidepoint(p):
                return True, False, True
            if pygame.Rect(0, 0, self.W, render_h).collidepoint(p):
                return True, False, False
        return False, False, False


# ──────────────────────────────────────────────────────────────────────────────
# POPUP MENU
# ──────────────────────────────────────────────────────────────────────────────
class PopupMenu:
    TITLES = {
        "upgrade":    "ULEPSZENIA",
        "difficulty": "TRUDNOSC",
        "resolution": "ROZDZIELCZOSC",
        "exit":       "MENU",
        "generic":    "MENU",
    }

    def __init__(self, screen, options_fn, actions_fn, kind="generic"):
        self.screen     = screen
        self.options_fn = options_fn
        self.actions_fn = actions_fn
        self.kind       = kind
        self.visible    = False
        self.font       = _font(34)
        self.font_sm    = _font(24)
        self.panel      = ScrollablePanel(screen, width=680, height=600, row_h=64)

    def open(self):  self.visible = True;  self.panel.scroll = 0
    def close(self): self.visible = False

    def draw(self):
        if not self.visible:
            return
        self.panel.screen = self.screen
        rows = [
            {"text": t, "action": a}
            for t, a in zip(self.options_fn(), self.actions_fn())
        ]

        def row_renderer(dst, row, rr):
            text = row["text"]
            is_ach = "[ach]" in text
            is_new = any(n in text for n in bulb.newly_unlocked_upgrades)
            bg     = C.surface0 if is_ach else C.surface1
            border = C.mauve if is_new else (C.green if is_ach else C.yellow)
            pygame.draw.rect(dst, bg,     rr)
            pygame.draw.rect(dst, border, rr, 2)
            col = C.mauve if is_new else (C.green if is_ach else C.text)
            s   = _txt(self.font, text, col)
            dst.blit(s, s.get_rect(center=rr.center))
            if is_new:
                tag = _txt(self.font_sm, " NOWE! ", C.base)
                tr  = tag.get_rect(topright=(rr.right-6, rr.y+4))
                pygame.draw.rect(dst, C.mauve, tr.inflate(4, 2))
                dst.blit(tag, tr)
            if bulb.beginners_luck_active and self.kind == "upgrade":
                for uname, u in bulb.upgrades.items():
                    if uname in text:
                        eff = bulb.effective_cost(uname)
                        if eff != u["cost"]:
                            hint = _txt(self.font_sm, f" [{eff}] ", C.peach)
                            hr   = hint.get_rect(bottomright=(rr.right-6, rr.bottom-4))
                            dst.blit(hint, hr)
                        break
            return row["action"]

        self.panel.draw(
            title=self.TITLES.get(self.kind, "MENU"),
            rows=rows, row_renderer=row_renderer,
            close_label="Zamknij  [Esc]",
        )

    def handle_event(self, event) -> bool:
        if not self.visible:
            return False
        kind, payload = self.panel.handle_event(
            event, rows_len=len(self.options_fn()),
            close_keys=(pygame.K_ESCAPE,),
        )
        if kind is None:  return False
        if kind == "close":
            if self.kind != "difficulty" or bulb.current_difficulty != "NONE":
                self.close()
            return True
        if kind == "select":
            payload()
            if self.kind == "upgrade":
                for n in list(bulb.newly_unlocked_upgrades):
                    if bulb.upgrades.get(n, {}).get("owned", 0) > 0:
                        bulb.newly_unlocked_upgrades.discard(n)
            else:
                self.close()
            return True
        return True


# ──────────────────────────────────────────────────────────────────────────────
# SUBMITION
# ──────────────────────────────────────────────────────────────────────────────
class Submition:
    def read_save(self, data: dict):
        exp = data.get("checksum", "")
        tmp = {k: v for k, v in data.items() if k != "checksum"}
        if _checksum(tmp) != exp:
            print("WARNING: checksum mismatch w submit"); return
        self.player    = data.get("player", "")
        self.score     = data.get("score",  0.0)
        self.play_time = data.get("play_time", 0)

    def make_submit(self):
        sub = {"player": PLAYER_NAME, "score": self.score,
               "play_time": self.play_time, "random_seed": 123456}
        sub["checksum"] = _checksum(sub)
        with open(SUBMIT_FILE, "w", encoding="utf-8") as f:
            json.dump(sub, f, indent=4)


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def _checksum(data: dict) -> str:
    raw = f"{data['player']}|{data['score']}|{data['play_time']}|{data['random_seed']}"
    return hashlib.sha256(raw.encode()).hexdigest()

def scale_pos(pos):
    ww, wh = screen.get_size()
    return int(pos[0]*render_w/ww), int(pos[1]*render_h/wh)

def save_game():
    d = bulb.to_dict()
    d["achievements"] = ach_sys.to_dict()
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=4)

def load_game():
    if not os.path.exists(SAVE_FILE): return
    try:
        with open(SAVE_FILE, encoding="utf-8") as f:
            d = json.load(f)
        bulb.load_from_dict(d)
        if "achievements" in d:
            ach_sys.load_from_dict(d["achievements"])
    except Exception as e:
        print(f"Zapis uszkodzony – startujemy od nowa ({e})")

def do_submit():
    try:
        with open(SAVE_FILE, encoding="utf-8") as f:
            d = json.load(f)
        sub = Submition(); sub.read_save(d); sub.make_submit()
    except Exception as e:
        print(f"Submit error: {e}")

def set_resolution(w, h):
    global game_surface, render_w, render_h
    render_w, render_h = w, h
    game_surface = pygame.Surface((render_w, render_h))
    for m in (side_menu, upgrade_menu, difficulty_menu, resolution_menu, exit_menu):
        m.screen = game_surface
    ach_mod.set_render_size(render_w, render_h)
    minigame_hub.set_render_size(render_w, render_h)
    minigame_hub.screen = game_surface
    bulb.reposition()

def get_upgrade_texts():
    out = []
    for name, u in bulb.upgrades.items():
        prefix = "[ach] " if name in UNLOCKABLE_UPGRADES else ""
        eff_cost = bulb.effective_cost(name)
        affordable = "  ✓" if bulb.score >= eff_cost and u["owned"] < u["max"] else ""
        out.append(f"{prefix}{name}  ({u['owned']}/{u['max']})  koszt:{eff_cost}{affordable}")
    return out

def get_upgrade_actions():
    return [lambda n=n: bulb.buy_upgrade(n) for n in bulb.upgrades]

def get_diff_texts():
    return [v["label"] for v in Zarowka.DIFFICULTY.values()]

def get_diff_actions():
    return [lambda d=d: bulb.set_difficulty(d) for d in Zarowka.DIFFICULTY]


# ──────────────────────────────────────────────────────────────────────────────
# INIT
# ──────────────────────────────────────────────────────────────────────────────
pygame.init()
screen       = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption(f"{GAME_NAME}  {GAME_VERSION}")
game_surface = pygame.Surface((render_w, render_h))
clock        = pygame.time.Clock()
FPS          = 60

bulb    = Zarowka()
ach_sys = AchievementSystem()

# Wstrzyknij kontekst do modułu achievements
ach_mod.init(C, render_w, render_h)

# ── Auto-discover mini-games ──────────────────────────────────────────────────
discovered_minigames = discover_minigames()

show_ach_panel = False

upgrade_menu = PopupMenu(
    game_surface, get_upgrade_texts, get_upgrade_actions, "upgrade")

difficulty_menu = PopupMenu(
    game_surface, get_diff_texts, get_diff_actions, "difficulty")

resolution_menu = PopupMenu(
    game_surface,
    lambda: list(RESOLUTIONS.keys()),
    lambda: [lambda w=w, h=h: set_resolution(w,h) for w,h in RESOLUTIONS.values()],
    "resolution",
)

exit_menu = PopupMenu(
    game_surface,
    lambda: ["Exit to Desktop", "Save Game", "Load Game", "SUBMIT", "Resolution"],
    lambda: [
        lambda: (pygame.quit(), exit()),
        save_game,
        load_game,
        do_submit,
        resolution_menu.open,
    ],
    "exit",
)

side_menu = SideMenu(game_surface, bulb)

# ── Automatyczne wczytanie zapisu ─────────────────────────────────────────────
load_game()
if not bulb.loaded:
    difficulty_menu.open()

# ── Mini Games Hub (z auto-załadowanymi grami) ────────────────────────────────
minigame_hub = MiniGameHub(game_surface)
minigame_hub.init(C, render_w, render_h)

# Zarejestruj dynamicznie odkryte gry (jeśli MiniGameHub to wspiera)
if discovered_minigames and hasattr(minigame_hub, "register_game"):
    for gname, gcls in discovered_minigames.items():
        try:
            minigame_hub.register_game(gname, gcls)
            print(f"[AutoLoader] Zarejestrowano: '{gname}'")
        except Exception as e:
            print(f"[AutoLoader] Błąd rejestracji '{gname}': {e}")


# ──────────────────────────────────────────────────────────────────────────────
# GAME LOOP
# ──────────────────────────────────────────────────────────────────────────────
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        epos = scale_pos(event.pos) if hasattr(event, "pos") else None
        if epos:
            scaled = pygame.event.Event(
                event.type,
                {"pos": epos, "button": getattr(event, "button", None)},
            )
        else:
            scaled = event

        if show_ach_panel:
            if ach_sys.handle_panel_event(scaled):
                show_ach_panel = False
            continue

        if minigame_hub.is_open:
            minigame_hub.handle_event(scaled, bulb)
            continue

        ui = False
        ui |= upgrade_menu.handle_event(scaled)
        ui |= difficulty_menu.handle_event(scaled)
        ui |= resolution_menu.handle_event(scaled)
        ui |= exit_menu.handle_event(scaled)
        consumed, open_ach, open_games = side_menu.handle_event(scaled, upgrade_menu, difficulty_menu)
        ui |= consumed
        if open_ach:
            show_ach_panel = True
        if open_games:
            minigame_hub.open()

        if ui:
            continue

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if epos and bulb.location.collidepoint(epos):
                bulb.click()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                bulb.click()
            if event.key == pygame.K_a:
                show_ach_panel = not show_ach_panel
            if event.key == pygame.K_g:
                if minigame_hub.is_open: minigame_hub.close()
                else:                   minigame_hub.open()
            if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                save_game()

    dt = clock.tick(FPS) / 1000.0
    play_time += dt

    bulb.tick(FPS)
    ach_sys.check(bulb, play_time)
    ach_sys.tick(dt)

    if minigame_hub.is_open and minigame_hub.active_game is not None:
        if hasattr(minigame_hub.active_game, '_update'):
            minigame_hub.active_game._update(dt)

    # ── RYSOWANIE ─────────────────────────────────────────────────────────────
    game_surface.fill(C.crust)

    side_menu.visible = not difficulty_menu.visible
    side_menu.draw(ach_sys)

    hot    = bulb.temperature >= bulb.overheat_threshold
    on     = bulb.state == 1
    color  = C.red    if hot else (C.yellow  if on else C.blue)
    border = C.rosewater if hot else (C.sky  if on else C.lavender)

    if on and not hot:
        pulse = int(math.sin(pygame.time.get_ticks() * 0.006) * 6)
        r = bulb.location.inflate(pulse, pulse)
    else:
        r = bulb.location

    pygame.draw.rect(game_surface, color,  r)
    pygame.draw.rect(game_surface, border, r, 3)

    if bulb.beginners_luck_active:
        glow_alpha = int(abs(math.sin(pygame.time.get_ticks() * 0.003)) * 120) + 60
        glow = pygame.Surface((r.width+24, r.height+24), pygame.SRCALPHA)
        glow.fill((0, 0, 0, 0))
        pygame.draw.rect(glow, (*C.peach, glow_alpha), glow.get_rect(), border_radius=8)
        game_surface.blit(glow, (r.x-12, r.y-12))

    bw = 200
    bx = render_w//2 - bw//2
    by = render_h//2 + bulb.height//2 + 18
    bh = 14
    ratio = min(1.0, bulb.temperature / bulb.overheat_threshold)
    bar_col = C.green if ratio < 0.5 else (C.yellow if ratio < 0.8 else C.red)
    pygame.draw.rect(game_surface, C.surface0, (bx, by, bw, bh))
    pygame.draw.rect(game_surface, bar_col,   (bx, by, int(bw*ratio), bh))
    pygame.draw.rect(game_surface, C.overlay1, (bx, by, bw, bh), 1)
    temp_s = _txt(_font(22), f"{bulb.temperature:.0f}/{bulb.overheat_threshold}°C", C.subtext1)
    game_surface.blit(temp_s, temp_s.get_rect(centerx=render_w//2, y=by+bh+4))

    upgrade_menu.draw()
    difficulty_menu.draw()
    resolution_menu.draw()
    exit_menu.draw()

    if show_ach_panel:
        ach_sys.draw_panel(game_surface)

    if minigame_hub.is_open:
        minigame_hub.draw(game_surface, bulb)

    ach_sys.draw_notifications(game_surface)

    if bulb.difficulty_locked and not minigame_hub.is_open and not show_ach_panel:
        hint_s = _txt(_font(20), "[G] Mini Gry", C.overlay0)
        game_surface.blit(hint_s, (render_w - hint_s.get_width() - 8, render_h - 24))

    ww, wh = screen.get_size()
    screen.blit(pygame.transform.smoothscale(game_surface, (ww, wh)), (0, 0))
    for _ in range(30000):
        math.sqrt(12345.6789)

    ww, wh = screen.get_size()
    screen.blit(pygame.transform.smoothscale(game_surface, (ww, wh)), (0, 0))
    pygame.display.flip()

save_game()

pygame.quit()

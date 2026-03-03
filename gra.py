import pygame
import math
import random
import json
import os
import hashlib
import time

# ================== KONFIGURACJA LOGICZNA ==================
BASE_W, BASE_H = 1280, 720

SAVE_FILE = "savegame.json"
SAVE_VERSION = 1
GAME_VERSION = '0.1.0'
PLAYER_NAME = 'Fryderyk'

play_time = 0.0

# ================== KLASA ŻARÓWKI ==================
class Zarowka:
    def __init__(self):
        self.score = 0.0
        self.income = 1
        self.passive_income = 0
        self.state = 0
        self.location = pygame.Rect(600, 10, 80, 80)

        self.temperature = 20.0
        self.room_temperature = 20.0
        self.temperature_increase = 15.0
        self.overheat_threshold = 100
        self.penalty = 10

        self.upgrades = {
            "Better filament": {"cost": 10, "owned": 0, "income_bonus": 1, "max": 7},
            "PWM brighness reducer": {"cost": 50, "owned": 0, "income_bonus": 5, "max": 4},
            "Solar power": {"cost": 500, "owned": 0, "passive_bonus": 12, "max": 3},
            "Heatsink": {"cost": 200, "owned": 0, "cooling_bonus": 1, "max": 3},
            "Overclock": {"cost": 1000, "owned": 0, "income_bonus": 20, "cooling_bonus": -0.5, "max": 2},
            "Undervolt": {"cost": 1000, "owned": 0, "income_bonus": -5, "cooling_bonus": 2, "max": 2},
            "Coal powerplant": {"cost": 20000, "owned": 0, "passive_bonus": 100, "cooling_bonus": -2, "max": 2},
            "LED light": {"cost": 5000, "owned": 0, "income_bonus": 100, "cooling_bonus": 5, "max": 1},
            "Consumers Discount": {"cost": 10000, "owned": 0, "penalty": -3, "max": 1},
            "Randomizer": {"cost": 5000, "owned": 0, "max": 10},
        }

        self.difficulty = {
            "Easy": 18,
            "Medium": 36,
            "Hard": 52,
            "Hell": 80
        }

        self.current_difficulty = "NONE"
        self.difficulty_locked = False
        self.random_seed = 123456  # dowolny startowy

    def click(self):
        self.score += self.income
        self.state = 1 - self.state

    def buy_upgrade(self, name):
        u = self.upgrades[name]

        # ===== RANDOMIZER (specjalny przypadek) =====
        if name == "Randomizer":
            if self.score < u["cost"] or u["owned"] >= u["max"]:
                return

            rng = random.Random(self.random_seed)

            income = rng.randint(-25, 30)
            passive = rng.randint(-10, 10)
            cooling = rng.randint(-2, 2)

            self.random_seed += 10

            self.score -= u["cost"]
            u["owned"] += 1
            u["cost"] = int(u["cost"] * 1.5)

            self.income += income
            self.passive_income += passive
            self.temperature_increase -= cooling
            return

        # ===== NORMALNE UPGRADE =====
        if self.score < u["cost"] or u["owned"] >= u["max"]:
            return

        self.score -= u["cost"]
        u["owned"] += 1

        if "income_bonus" in u:
            self.income += u["income_bonus"]
        if "passive_bonus" in u:
            self.passive_income += u["passive_bonus"]
        if "cooling_bonus" in u:
            self.temperature_increase -= u["cooling_bonus"]
        if "penalty" in u:
            self.penalty += u["penalty"]

        u["cost"] = int(u["cost"] * 1.5)

    def set_difficulty(self, name):
        if self.difficulty_locked:
            return
        self.current_difficulty = name
        self.room_temperature = self.difficulty[name]
        self.difficulty_locked = True

    def tick(self, fps):
        self.score += self.passive_income / fps
        if self.state:
            self.temperature += self.temperature_increase / fps
            if self.temperature > self.overheat_threshold:
                self.state = 0
                self.score = max(0, self.score * (1 - self.penalty / 100))
        else:
            self.temperature = max(
                self.room_temperature,
                self.temperature - self.temperature_increase / (fps * 2)
            )
    def to_dict(self):
        data = {
            "save_version": SAVE_VERSION,
            "game_version": GAME_VERSION,
            "player": PLAYER_NAME,

            "score": round(self.score, 3),
            "play_time": int(play_time),
            "random_seed": self.random_seed,
            "difficulty": self.current_difficulty,

            "income": self.income,
            "passive_income": self.passive_income,
            "temperature": self.temperature,
            "room_temperature": self.room_temperature,
            "penalty": self.penalty,

            "upgrades": {
                name: {
                    "owned": u["owned"],
                    "cost": u["cost"]
                } for name, u in self.upgrades.items()
            },

            "timestamp": int(time.time())
        }

        data["checksum"] = compute_checksum(data)
        return data

    def load_from_dict(self, data):
        global play_time

        # --- weryfikacja checksum ---
        expected = data.get("checksum", "")
        temp = dict(data)
        temp.pop("checksum", None)

        if compute_checksum(temp) != expected:
            print("⚠ Save checksum mismatch – possible tampering")
            return
        # podstawowe liczby – brak? -> zero
        self.score = data.get("score", 0.0)
        play_time = data.get("play_time", 0)
        self.random_seed = data.get("random_seed", 123456)

        self.income = data.get("income", 1)
        self.passive_income = data.get("passive_income", 0)
        self.temperature = data.get("temperature", 20.0)
        self.room_temperature = data.get("room_temperature", 20.0)
        self.penalty = data.get("penalty", 10)

        # difficulty
        self.current_difficulty = data.get("difficulty", "NONE")
        self.difficulty_locked = self.current_difficulty != "NONE"

        # upgrady – jeśli nowy upgrade → zostaje domyślny
        saved_upgrades = data.get("upgrades", {})
        for name, u in self.upgrades.items():
            saved = saved_upgrades.get(name, {})
            owned = saved.get("owned", 0)
            u["owned"] = min(owned, u["max"])
            u["cost"] = saved.get("cost", u["cost"])

        # przelicz statystyki od nowa (bezpiecznie!)
        self.income = 1
        self.passive_income = 0
        self.temperature_increase = 15.0
        self.penalty = 10

        for name, u in self.upgrades.items():
            for _ in range(u["owned"]):
                if "income_bonus" in u:
                    self.income += u["income_bonus"]
                if "passive_bonus" in u:
                    self.passive_income += u["passive_bonus"]
                if "cooling_bonus" in u:
                    self.temperature_increase -= u["cooling_bonus"]
                if "penalty" in u:
                    self.penalty += u["penalty"]

# ================== SIDE MENU ==================
class SideMenu:
    def __init__(self, screen, bulb):
        self.screen = screen
        self.bulb = bulb
        self.visible = True
        self.font = pygame.font.Font(None, 36)

        self.upgrade_rect = pygame.Rect(20, 250, 180, 40)
        self.exit_rect = pygame.Rect(20, 290, 180, 40)
        self.diff_rect = pygame.Rect(20, 210, 180, 40)

    def draw(self):
        if not self.visible:
            return

        pygame.draw.rect(self.screen, (240, 240, 240), (0, 0, 300, BASE_H))
        pygame.draw.line(self.screen, (0, 0, 0), (300, 0), (300, BASE_H), 2)

        y = 20
        lines = [
            f"Score: {math.floor(self.bulb.score)}",
            f"Income/click: {self.bulb.income}",
            f"Passive/sec: {self.bulb.passive_income}",
            f"Temp: {self.bulb.temperature:.1f}°C / {self.bulb.overheat_threshold}°C",
            f"Difficulty: {self.bulb.current_difficulty}"
        ]
        for text in lines:
            color = (255, 100, 100) if self.bulb.temperature > self.bulb.overheat_threshold - 10 else (0, 0, 0)
            self.screen.blit(self.font.render(text, True, color), (20, y))
            y += 40

        if not self.bulb.difficulty_locked:
            pygame.draw.rect(self.screen, (200,255,200), self.diff_rect)
            self.screen.blit(self.font.render("Difficulty Menu", True, (0,0,0)), (30, 215))

        pygame.draw.rect(self.screen, (200,255,200), self.upgrade_rect)
        self.screen.blit(self.font.render("Upgrades", True, (0,0,0)), (30, 255))
        pygame.draw.rect(self.screen, (200,255,200), self.exit_rect)
        self.screen.blit(self.font.render("Exit", True, (0,0,0)), (30, 295))

    def handle_event(self, event, upgrade_menu, difficulty_menu):
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.upgrade_rect.collidepoint(event.pos):
                upgrade_menu.open()
                return True
            if self.exit_rect.collidepoint(event.pos):
                exit_menu.open()
                return True
            if not self.bulb.difficulty_locked and self.diff_rect.collidepoint(event.pos):
                difficulty_menu.open()
                return True
            if pygame.Rect(0, 0, 300, BASE_H).collidepoint(event.pos):
                return True
        return False

# ================== MENU POPUP ==================
class MENU:
    def __init__(self, screen, options_func, actions_func, center=(BASE_W//2, BASE_H//2), menu_kind="generic"):
        self.screen = screen
        self.options_func = options_func
        self.actions_func = actions_func
        self.center = center
        self.font = pygame.font.Font(None, 36)
        self.visible = False
        self.buttons = []
        self.type = menu_kind
        self.page = 0

    def open(self):
        self.visible = True

    def close(self):
        self.visible = False

    def draw(self):
        if not self.visible:
            return

        options = self.options_func()
        actions = self.actions_func()
        options = options + ["Close"]
        actions = actions + [lambda: self.close()]

        w, h = 460, 720
        menu = pygame.Rect(self.center[0]-w//2, self.center[1]-h//2, w, h)
        pygame.draw.rect(self.screen, (235,235,235), menu)
        pygame.draw.rect(self.screen, (0,0,0), menu, 3)

        self.buttons.clear()
        y = menu.y + 40
        for text, action in zip(options, actions):
            surf = self.font.render(text, True, (0,0,0))
            rect = surf.get_rect(center=(menu.centerx, y))
            self.screen.blit(surf, rect)
            self.buttons.append((rect, action))
            y += 50

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in self.buttons:
                if rect.collidepoint(event.pos):
                    action()
                    if action is self.buttons[-1][1]:
                        if bulb.current_difficulty != "NONE":
                            self.close()
                    elif self.type != "upgrade":
                        self.close()
                    return True
        return False

# ================== PAGED UPGRADES ==================
class PagedUpgrades:
    def __init__(self, bulb, per_page=6):
        self.bulb = bulb
        self.per_page = per_page
        self.page = 0
        self.font = pygame.font.Font(None, 36)
        self.bottom_buttons = []

    def max_page(self):
        return max(0, (len(self.bulb.upgrades) - 1) // self.per_page)

    def options(self):
        names = list(self.bulb.upgrades.keys())
        start = self.page * self.per_page
        end = start + self.per_page
        page_names = names[start:end]

        texts = []
        actions = []
        for name in page_names:
            u = self.bulb.upgrades[name]
            texts.append(f"{name} ({u['owned']}/{u['max']}) - cost: {u['cost']}")
            actions.append(lambda n=name: self.bulb.buy_upgrade(n))
        return texts, actions
    def draw_bottom_bar(self, screen, center, menu_visible):
        if self.max_page() == 0 or not menu_visible:
            self.bottom_buttons.clear()
            return

        width, height = 460, 80
        rect = pygame.Rect(center[0]-width//2, center[1]+200, width, height)
        pygame.draw.rect(screen, (220,220,220), rect)
        pygame.draw.rect(screen, (0,0,0), rect, 2)

        # dynamiczne pozycje
        spacing = width // 4
        left_x = rect.x + spacing
        center_x = rect.centerx
        right_x = rect.right - spacing
        y = rect.centery

        texts = ["<< Back", f"Page {self.page+1} / {self.max_page()+1}", "Next >>"]
        actions = [self.prev_page, lambda: None, self.next_page]

        self.bottom_buttons.clear()
        for pos_x, text, action in zip([left_x, center_x, right_x], texts, actions):
            surf = self.font.render(text, True, (0,0,0))
            text_rect = surf.get_rect(center=(pos_x, y))
            screen.blit(surf, text_rect)
            self.bottom_buttons.append((text_rect, action))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in self.bottom_buttons:
                if rect.collidepoint(event.pos):
                    action()
                    return True
        return False

    def next_page(self):
        if self.page < self.max_page():
            self.page += 1

    def prev_page(self):
        if self.page > 0:
            self.page -= 1

# ================== FUNKCJE MENU ==================
def get_upgrade_texts():
    return [f"{name} ({u['owned']}/{u['max']}) - cost: {u['cost']}" for name,u in bulb.upgrades.items()]

def get_difficulty_texts():
    return [f"{d} (temp +{t}°C)" for d,t in bulb.difficulty.items()]

def scale_mouse_pos(pos):
    win_w, win_h = screen.get_size()
    sx = BASE_W / win_w
    sy = BASE_H / win_h
    return int(pos[0]*sx), int(pos[1]*sy)

def save_game(bulb):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(bulb.to_dict(), f, indent=4)

def load_game(bulb):
    if not os.path.exists(SAVE_FILE):
        return
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        bulb.load_from_dict(data)
    except Exception:
        print("Save file corrupted – starting fresh")

def compute_checksum(data: dict) -> str:
    raw = f"{data['player']}|{data['score']}|{data['play_time']}|{data['random_seed']}"
    return hashlib.sha256(raw.encode()).hexdigest()

# ================== INIT ==================
pygame.init()
screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("Żarówka Clicker - Prerelease")
game_surface = pygame.Surface((BASE_W, BASE_H))
clock = pygame.time.Clock()
fps = 60

bulb = Zarowka()
paged_upgrades = PagedUpgrades(bulb, per_page=6)

upgrade_menu = MENU(
    game_surface,
    lambda: paged_upgrades.options()[0],
    lambda: paged_upgrades.options()[1],
    menu_kind="upgrade"
)

difficulty_menu = MENU(
    game_surface,
    get_difficulty_texts,
    lambda: [lambda d=d: bulb.set_difficulty(d) for d in bulb.difficulty],
    menu_kind="difficulty"
)
exit_menu = MENU(
    game_surface,
    lambda: ["Exit to Desktop", "Save Game", "Load Game"],
    lambda: [
        lambda: pygame.quit() or exit(),
        lambda: save_game(bulb),
        lambda: load_game(bulb)
    ],
    menu_kind="exit"
)

difficulty_menu.open()
side_menu = SideMenu(game_surface, bulb)

# ================== LOOP ==================
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if hasattr(event, 'pos'):
            event_pos = scale_mouse_pos(event.pos)
            event_scaled = pygame.event.Event(event.type, {'pos': event_pos, 'button': getattr(event, 'button', None)})
        else:
            event_scaled = event

        ui_used = False
        ui_used |= upgrade_menu.handle_event(event_scaled)
        ui_used |= difficulty_menu.handle_event(event_scaled)
        ui_used |= side_menu.handle_event(event_scaled, upgrade_menu, difficulty_menu)
        ui_used |= paged_upgrades.handle_event(event_scaled)
        ui_used |= exit_menu.handle_event(event_scaled)

        if ui_used:
            continue

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if bulb.location.collidepoint(event_pos):
                bulb.click()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                bulb.click()

    bulb.tick(fps)

    game_surface.fill((255,255,255))
    side_menu.visible = not difficulty_menu.visible
    side_menu.draw()

    color = (255,255,0) if bulb.state else (100,100,255)
    if bulb.temperature > bulb.overheat_threshold:
        color = (255,100,100)

    pygame.draw.rect(game_surface, color, bulb.location)
    pygame.draw.rect(game_surface, (0,0,0), bulb.location, 3)

    upgrade_menu.draw()
    difficulty_menu.draw()
    exit_menu.draw()
    paged_upgrades.draw_bottom_bar(game_surface, (BASE_W//2, BASE_H//2), upgrade_menu.visible)

    win_w, win_h = screen.get_size()
    scaled = pygame.transform.smoothscale(game_surface, (win_w, win_h))
    screen.blit(scaled, (0, 0))
    pygame.display.flip()

    dt = clock.tick(fps) / 1000
    play_time += dt

pygame.quit()
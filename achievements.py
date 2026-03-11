# achievements.py  –  System osiągnięć, nagród i odblokowywalnych ulepszeń
# Importowany przez main.py

import pygame

# ──────────────────────────────────────────────────────────────────────────────
# KOLORY (referencja do obiektu z main.py wstrzykiwana przy init)
# ──────────────────────────────────────────────────────────────────────────────
_colors = None
_render_w = 1920
_render_h = 1080

def init(colors, rw, rh):
    global _colors, _render_w, _render_h
    _colors = colors
    _render_w = rw
    _render_h = rh

def set_render_size(rw, rh):
    global _render_w, _render_h
    _render_w = rw
    _render_h = rh

# ──────────────────────────────────────────────────────────────────────────────
# SCROLLABLE PANEL  (wspólny komponent UI)
# ──────────────────────────────────────────────────────────────────────────────
class ScrollablePanel:
    def __init__(self, screen, width=520, height=780, row_h=58):
        self.screen = screen
        self.width  = width
        self.height = height
        self.row_h  = row_h
        self.scroll = 0
        self.visible_rows = 0
        self._buttons    = []
        self._close_rect = None
        self.title_font  = pygame.font.Font(None, 42)
        self.body_font   = pygame.font.Font(None, 30)

    def draw(self, title, rows, row_renderer, close_label="Zamknij",
             info_text=None, progress=None):
        cx = _render_w // 2
        cy = _render_h // 2
        panel = pygame.Rect(cx - self.width//2, cy - self.height//2,
                            self.width, self.height)

        pygame.draw.rect(self.screen, _colors.base,   panel)
        pygame.draw.rect(self.screen, _colors.yellow, panel, 3)

        ts = _render_text(self.title_font, title, _colors.yellow)
        self.screen.blit(ts, ts.get_rect(centerx=cx, y=panel.y + 18))
        pygame.draw.line(self.screen, _colors.yellow,
                         (panel.x+20, panel.y+65), (panel.right-20, panel.y+65), 2)

        header_y = panel.y + 72
        if info_text:
            s = _render_text(self.body_font, info_text, _colors.subtext1)
            self.screen.blit(s, s.get_rect(centerx=cx, y=header_y))
            header_y += 28

        if progress:
            done, total = progress
            bx, by = panel.x+30, header_y
            bw, bh = self.width-60, 18
            pygame.draw.rect(self.screen, _colors.surface0, (bx, by, bw, bh))
            if total > 0 and done > 0:
                pygame.draw.rect(self.screen, _colors.yellow,
                                 (bx, by, int(bw*done/total), bh))
            pygame.draw.rect(self.screen, _colors.overlay1, (bx, by, bw, bh), 1)
            header_y += 28

        list_y = header_y
        list_h = panel.bottom - list_y - 60
        self.visible_rows = max(1, list_h // self.row_h)
        max_scroll = max(0, len(rows) - self.visible_rows)
        self.scroll = max(0, min(self.scroll, max_scroll))
        self._buttons.clear()

        for i, row in enumerate(rows[self.scroll:self.scroll+self.visible_rows]):
            ry = list_y + i * self.row_h
            rr = pygame.Rect(panel.x+10, ry, self.width-20, self.row_h-4)
            payload = row_renderer(self.screen, row, rr)
            if payload is not None:
                self._buttons.append((rr, payload))

        if len(rows) > self.visible_rows:
            sbx = panel.right - 14
            sby = list_y
            sbh = self.visible_rows * self.row_h
            pygame.draw.rect(self.screen, _colors.surface0, (sbx, sby, 10, sbh))
            th = max(20, int(sbh * self.visible_rows / len(rows)))
            ty = sby + int((sbh-th)*self.scroll/max_scroll) if max_scroll else sby
            pygame.draw.rect(self.screen, _colors.yellow, (sbx, ty, 10, th))

        self._close_rect = pygame.Rect(cx-80, panel.bottom-50, 160, 36)
        pygame.draw.rect(self.screen, _colors.red,       self._close_rect)
        pygame.draw.rect(self.screen, _colors.rosewater, self._close_rect, 2)
        cs = _render_text(self.body_font, close_label, _colors.base)
        self.screen.blit(cs, cs.get_rect(center=self._close_rect.center))

    def _scroll_up(self):   self.scroll = max(0, self.scroll-1)
    def _scroll_down(self, n):
        self.scroll = min(max(0, n-self.visible_rows), self.scroll+1)

    def handle_event(self, event, rows_len, close_keys=()):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self._close_rect and self._close_rect.collidepoint(event.pos):
                    return "close", None
                for rect, payload in self._buttons:
                    if rect.collidepoint(event.pos):
                        return "select", payload
            elif event.button == 4: self._scroll_up();             return "scroll", None
            elif event.button == 5: self._scroll_down(rows_len);  return "scroll", None
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0: self._scroll_up()
            else:           self._scroll_down(rows_len)
            return "scroll", None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP,   pygame.K_w):
                self._scroll_up();            return "scroll", None
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self._scroll_down(rows_len);  return "scroll", None
            if event.key in close_keys:       return "close", None
        return None, None


def _render_text(font, text, color):
    try:    return font.render(text, True, color)
    except: return font.render("?",  True, color)


# ──────────────────────────────────────────────────────────────────────────────
# ODBLOKOWYWANE ULEPSZENIA  (dostępne tylko po achievemencie)
# ──────────────────────────────────────────────────────────────────────────────
#
# Costs are tuned so early unlocks (Turbo Click, Wind Power) are reachable
# quickly after BL fades, while the mega-tier ones require real late investment.
#
UNLOCKABLE_UPGRADES = {
    # === KLIKANIE ===
    "Turbo Click": {
        "cost":  2_000,   "owned": 0, "max": 5,  "income_bonus": 4,
        "desc": "[ach] Turbo Click – klik +4/szt",
    },
    "Quantum Click": {
        "cost": 30_000,   "owned": 0, "max": 4,  "income_bonus": 15,
        "desc": "[ach] Quantum Click – klik +15/szt",
    },
    "Lightning Click": {
        "cost":250_000,   "owned": 0, "max": 3,  "income_bonus": 60,
        "desc": "[ach] Lightning Click – klik +60/szt",
    },
    "Singularity Click": {
        "cost":3_000_000, "owned": 0, "max": 2,  "income_bonus": 350,
        "desc": "[ach] Singularity Click – klik +350/szt",
    },

    # === PASYWNE ===
    "Wind Power": {
        "cost":  5_000,   "owned": 0, "max": 5,  "passive_bonus": 3,
        "desc": "[ach] Wind Power – passive +3/szt",
    },
    "Fusion Power": {
        "cost": 80_000,   "owned": 0, "max": 4,  "passive_bonus": 10,
        "desc": "[ach] Fusion Power – passive +10/szt",
    },
    "Mega Factory": {
        "cost":700_000,   "owned": 0, "max": 3,  "passive_bonus": 40,
        "desc": "[ach] Mega Factory – passive +40/szt",
    },
    "Dyson Sphere": {
        "cost":6_000_000, "owned": 0, "max": 2,  "passive_bonus": 180,
        "desc": "[ach] Dyson Sphere – passive +180/szt",
    },
    "Dark Matter Plant": {
        "cost":50_000_000,"owned": 0, "max": 1,  "passive_bonus": 1500,
        "desc": "[ach] Dark Matter Plant – passive +1500",
    },

    # === CHŁODZENIE ===
    "Heat Shield": {
        "cost": 15_000,   "owned": 0, "max": 4,  "cooling_bonus": 1.0,
        "desc": "[ach] Heat Shield – chlodzenie +1/szt",
    },
    "Cryo Module": {
        "cost":200_000,   "owned": 0, "max": 3,  "cooling_bonus": 2.5,
        "desc": "[ach] Cryo Module – chlodzenie +2.5/szt",
    },
    "Absolute Zero": {
        "cost":2_000_000, "owned": 0, "max": 2,  "cooling_bonus": 6.0,
        "desc": "[ach] Absolute Zero – chlodzenie +6/szt",
    },

    # === MIESZANE ===
    "Time Crystal": {
        "cost":300_000,   "owned": 0, "max": 2,
        "passive_bonus": 10, "income_bonus": 4,
        "desc": "[ach] Time Crystal – passive +10, klik +4/szt",
    },
    "Inferno Core": {
        "cost":800_000,   "owned": 0, "max": 2,
        "passive_bonus": 60, "cooling_bonus": -20,
        "desc": "[ach] Inferno Core – passive +60, GRZEJE +20/szt!",
    },
    "Overclocked LED": {
        "cost":4_000_000, "owned": 0, "max": 1,
        "income_bonus": 80, "passive_bonus": 20, "cooling_bonus": 2.0,
        "desc": "[ach] Overclocked LED – klik +80, passive +20, chlodzi +2",
    },
    "Quantum Capacitor": {
        "cost":25_000_000,"owned": 0, "max": 1,
        "income_bonus": 250, "passive_bonus": 80,
        "desc": "[ach] Quantum Capacitor – klik +250, passive +80",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# NAGRODY ZA ACHIEVEMENTY
#
# PHILOSOPHY:
#  Early achievements (first click, first 50 clicks, first upgrades, first overheat)
#  give LARGE bonuses so the new player immediately feels progress accelerate.
#  Mid-game achievements (hundreds of clicks, thousands of score) give moderate bonuses.
#  Late-game achievements (tens of thousands of clicks, millions of score) give small
#  incremental bonuses — growth here comes from upgrades, not achievement handouts.
# ──────────────────────────────────────────────────────────────────────────────
ACHIEVEMENT_REWARDS = {
    # --- Klikanie ---
    # Early: BIG bonuses to get the player rolling fast
    "first_click":    {"desc": "+3 klik",                        "income_bonus": 3},
    "clicker_50":     {"desc": "+4 klik",                        "income_bonus": 4},
    "clicker_200":    {"desc": "+5 klik, odbl. Turbo Click",     "income_bonus": 5,
                       "unlock_upgrade": "Turbo Click"},
    # Mid: moderate
    "clicker_1000":   {"desc": "+4 klik",                        "income_bonus": 4},
    "clicker_5000":   {"desc": "+4 klik, odbl. Quantum Click",   "income_bonus": 4,
                       "unlock_upgrade": "Quantum Click"},
    # Late: smaller increments
    "clicker_25000":  {"desc": "+3 klik, odbl. Lightning Click", "income_bonus": 3,
                       "unlock_upgrade": "Lightning Click"},
    "clicker_100000": {"desc": "+3 klik, odbl. Singularity",     "income_bonus": 3,
                       "unlock_upgrade": "Singularity Click"},

    # --- Punkty ---
    # Early: passive jumpstart
    "score_500":        {"desc": "+3 passive/s",                  "passive_bonus": 3},
    "score_5000":       {"desc": "+4 passive/s, odbl. Wind Power","passive_bonus": 4,
                         "unlock_upgrade": "Wind Power"},
    "score_25000":      {"desc": "+4 passive/s",                  "passive_bonus": 4},
    # Mid: still decent
    "score_100000":     {"desc": "+3 passive/s, odbl. Fusion Power","passive_bonus": 3,
                         "unlock_upgrade": "Fusion Power"},
    "score_500000":     {"desc": "+3 passive/s, odbl. Mega Factory","passive_bonus": 3,
                         "unlock_upgrade": "Mega Factory"},
    # Late: small
    "score_2000000":    {"desc": "+2 passive/s, odbl. Dyson Sphere","passive_bonus": 2,
                         "unlock_upgrade": "Dyson Sphere"},
    "score_10000000":   {"desc": "+2 passive/s, odbl. Dark Matter","passive_bonus": 2,
                         "unlock_upgrade": "Dark Matter Plant"},

    # --- Przegrzanie ---
    # First overheat: big penalty reduction so it doesn't feel punishing
    "first_overheat":   {"desc": "Kara -3%",                      "penalty_reduction": 3},
    "overheat_10":      {"desc": "Kara -2%, odbl. Heat Shield",   "penalty_reduction": 2,
                         "unlock_upgrade": "Heat Shield"},
    "overheat_30":      {"desc": "Prog +3C, odbl. Cryo Module",   "overheat_threshold_bonus": 3,
                         "unlock_upgrade": "Cryo Module"},
    "overheat_100":     {"desc": "Prog +3C, odbl. Absolute Zero", "overheat_threshold_bonus": 3,
                         "unlock_upgrade": "Absolute Zero"},
    "no_overheat_5000": {"desc": "+1C chlodz, +3 klik",           "cooling_bonus": 1.0, "income_bonus": 3},
    "no_overheat_50000":{"desc": "+1.5C chlodz, +5 klik",         "cooling_bonus": 1.5, "income_bonus": 5},

    # --- Ulepszenia ---
    # Very early: big reward for buying first upgrade
    "first_upgrade":    {"desc": "+4 klik, +2 passive",           "income_bonus": 4, "passive_bonus": 2},
    "upgrades_5":       {"desc": "+3 klik, +3 passive",           "income_bonus": 3, "passive_bonus": 3},
    "upgrades_20":      {"desc": "+3 passive/s, odbl. Mega Factory","passive_bonus": 3,
                         "unlock_upgrade": "Mega Factory"},
    "upgrades_50":      {"desc": "+5 passive/s, odbl. Time Crystal","passive_bonus": 5,
                         "unlock_upgrade": "Time Crystal"},
    "master_clicker":   {"desc": "+10 klik, odbl. Lightning Click","income_bonus": 10,
                         "unlock_upgrade": "Lightning Click"},
    "power_district":   {"desc": "+15 passive/s, odbl. Q. Capacitor","passive_bonus": 15,
                         "unlock_upgrade": "Quantum Capacitor"},
    "led_owner":        {"desc": "+1.5C chlodz, +6 passive/s",    "cooling_bonus": 1.5, "passive_bonus": 6},
    "all_unlockable":   {"desc": "+30 klik, +30 passive/s",        "income_bonus": 30,   "passive_bonus": 30},

    # --- Randomizer ---
    "first_randomizer": {"desc": "+3 klik",                       "income_bonus": 3},
    "randomizer_10":    {"desc": "+4 klik, -1% kara",             "income_bonus": 4,    "penalty_reduction": 1},
    "randomizer_30":    {"desc": "+8 klik, odbl. Inferno Core",   "income_bonus": 8,
                         "unlock_upgrade": "Inferno Core"},

    # --- Trudność ---
    "hell_mode":        {"desc": "+8 passive/s, odbl. Inferno Core","passive_bonus": 8,
                         "unlock_upgrade": "Inferno Core"},
    "hard_mode":        {"desc": "+4 passive/s, odbl. Cryo Module","passive_bonus": 4,
                         "unlock_upgrade": "Cryo Module"},
    "easy_score_2000":  {"desc": "Kara -2%",                      "penalty_reduction": 2},

    # --- Czas gry ---
    # Short session milestones give nice boosts; marathon milestones give small ones
    "playtime_120":     {"desc": "+3 passive/s",                  "passive_bonus": 3},
    "playtime_600":     {"desc": "+3 passive/s",                  "passive_bonus": 3},
    "playtime_1800":    {"desc": "+2 passive/s, odbl. Time Crystal","passive_bonus": 2,
                         "unlock_upgrade": "Time Crystal"},
    "playtime_7200":    {"desc": "+2 passive/s, odbl. Overclocked LED","passive_bonus": 2,
                         "unlock_upgrade": "Overclocked LED"},

    # --- Pasywny dochód ---
    "passive_20":       {"desc": "+3 passive/s",                  "passive_bonus": 3},
    "passive_100":      {"desc": "+3 passive/s",                  "passive_bonus": 3},
    "passive_500":      {"desc": "+4 passive/s, odbl. Mega Factory","passive_bonus": 4,
                         "unlock_upgrade": "Mega Factory"},
    "passive_2000":     {"desc": "+3 passive/s, odbl. Dyson Sphere","passive_bonus": 3,
                         "unlock_upgrade": "Dyson Sphere"},
    "passive_10000":    {"desc": "+2 passive/s, odbl. Dark Matter","passive_bonus": 2,
                         "unlock_upgrade": "Dark Matter Plant"},

    # --- Temperatura ---
    "temp_control":     {"desc": "+1.5C chlodz, Prog +3C",
                         "cooling_bonus": 1.5, "overheat_threshold_bonus": 3},
    "ice_master":       {"desc": "+2C chlodz, Prog +5C, odbl. Absolute Zero",
                         "cooling_bonus": 2.0, "overheat_threshold_bonus": 5,
                         "unlock_upgrade": "Absolute Zero"},
}


# ──────────────────────────────────────────────────────────────────────────────
# DEFINICJE OSIĄGNIĘĆ
# ──────────────────────────────────────────────────────────────────────────────
ACHIEVEMENTS_DEF = [
    # ── Klikanie ──────────────────────────────────────────────────────────────
    {"id": "first_click",    "name": "Pierwszy Klik!",      "cat": "Klikanie",
     "desc": "Kliknij zarowke po raz pierwszy.",
     "condition": lambda b: b.total_clicks >= 1},
    {"id": "clicker_50",     "name": "Rozgrzewka",          "cat": "Klikanie",
     "desc": "Kliknij 50 razy.",
     "condition": lambda b: b.total_clicks >= 50},
    {"id": "clicker_200",    "name": "Zapalacz",            "cat": "Klikanie",
     "desc": "Kliknij 200 razy.",
     "condition": lambda b: b.total_clicks >= 200},
    {"id": "clicker_1000",   "name": "Maniak Kliku",        "cat": "Klikanie",
     "desc": "Kliknij 1 000 razy.",
     "condition": lambda b: b.total_clicks >= 1_000},
    {"id": "clicker_5000",   "name": "Niestrudzony",        "cat": "Klikanie",
     "desc": "Kliknij 5 000 razy.",
     "condition": lambda b: b.total_clicks >= 5_000},
    {"id": "clicker_25000",  "name": "Autokliker?",         "cat": "Klikanie",
     "desc": "Kliknij 25 000 razy.",
     "condition": lambda b: b.total_clicks >= 25_000},
    {"id": "clicker_100000", "name": "Bóg Kliku",           "cat": "Klikanie",
     "desc": "Kliknij 100 000 razy.",
     "condition": lambda b: b.total_clicks >= 100_000},

    # ── Punkty ────────────────────────────────────────────────────────────────
    {"id": "score_500",       "name": "Pierwsze Setki",     "cat": "Punkty",
     "desc": "Zdobadz 500 punktow.",
     "condition": lambda b: b.score >= 500},
    {"id": "score_5000",      "name": "Tysiacznik",         "cat": "Punkty",
     "desc": "Zdobadz 5 000 punktow.",
     "condition": lambda b: b.score >= 5_000},
    {"id": "score_25000",     "name": "Bogacz",             "cat": "Punkty",
     "desc": "Zdobadz 25 000 punktow.",
     "condition": lambda b: b.score >= 25_000},
    {"id": "score_100000",    "name": "Grubas",             "cat": "Punkty",
     "desc": "Zdobadz 100 000 punktow.",
     "condition": lambda b: b.score >= 100_000},
    {"id": "score_500000",    "name": "Milioner (prawie)",  "cat": "Punkty",
     "desc": "Zdobadz 500 000 punktow.",
     "condition": lambda b: b.score >= 500_000},
    {"id": "score_2000000",   "name": "Milioner!",          "cat": "Punkty",
     "desc": "Zdobadz 2 000 000 punktow.",
     "condition": lambda b: b.score >= 2_000_000},
    {"id": "score_10000000",  "name": "Krezus",             "cat": "Punkty",
     "desc": "Zdobadz 10 000 000 punktow.",
     "condition": lambda b: b.score >= 10_000_000},

    # ── Przegrzanie ───────────────────────────────────────────────────────────
    {"id": "first_overheat",  "name": "Usmazona Zarowka",   "cat": "Temperatura",
     "desc": "Przegrziej zarowke po raz pierwszy.",
     "condition": lambda b: b.total_overheats >= 1},
    {"id": "overheat_10",     "name": "Piroman",            "cat": "Temperatura",
     "desc": "Przegrziej zarowke 10 razy.",
     "condition": lambda b: b.total_overheats >= 10},
    {"id": "overheat_30",     "name": "Straz Pozarna",      "cat": "Temperatura",
     "desc": "Przegrziej zarowke 30 razy.",
     "condition": lambda b: b.total_overheats >= 30},
    {"id": "overheat_100",    "name": "Feniksowy Tryb",     "cat": "Temperatura",
     "desc": "Przegrziej zarowke 100 razy.",
     "condition": lambda b: b.total_overheats >= 100},
    {"id": "no_overheat_5000","name": "Zimna Krew",         "cat": "Temperatura",
     "desc": "Zdobadz 5 000 pkt bez przegrzania.",
     "condition": lambda b: b.score_since_last_overheat >= 5_000},
    {"id": "no_overheat_50000","name":"Lodowiec",           "cat": "Temperatura",
     "desc": "Zdobadz 50 000 pkt bez przegrzania.",
     "condition": lambda b: b.score_since_last_overheat >= 50_000},
    {"id": "temp_control",    "name": "Termodynamik",       "cat": "Temperatura",
     "desc": "Osiagnij temp. chlodzenia >= 20/s.",
     "condition": lambda b: b.temperature_decrease >= 20},
    {"id": "ice_master",      "name": "Pan Mrozu",          "cat": "Temperatura",
     "desc": "Osiagnij temp. chlodzenia >= 60/s.",
     "condition": lambda b: b.temperature_decrease >= 60},

    # ── Ulepszenia ────────────────────────────────────────────────────────────
    {"id": "first_upgrade",   "name": "Modernizacja",       "cat": "Ulepszenia",
     "desc": "Kup pierwsze ulepszenie.",
     "condition": lambda b: b.total_upgrades_bought >= 1},
    {"id": "upgrades_5",      "name": "Inzynier",           "cat": "Ulepszenia",
     "desc": "Kup lacznie 5 ulepszen.",
     "condition": lambda b: b.total_upgrades_bought >= 5},
    {"id": "upgrades_20",     "name": "Upgrade Junkie",     "cat": "Ulepszenia",
     "desc": "Kup lacznie 20 ulepszen.",
     "condition": lambda b: b.total_upgrades_bought >= 20},
    {"id": "upgrades_50",     "name": "Kolekcjoner",        "cat": "Ulepszenia",
     "desc": "Kup lacznie 50 ulepszen.",
     "condition": lambda b: b.total_upgrades_bought >= 50},
    {"id": "master_clicker",  "name": "Master Clicker",     "cat": "Ulepszenia",
     "desc": "Kup max lvl Multi, Mega i Ultra Click.",
     "condition": lambda b: b.total_upgrades_bought >= 1 and all(
         b.upgrades.get(n, {}).get("owned", 0) >= b.upgrades.get(n, {}).get("max", 99)
         for n in ("Multi Click", "Mega Click", "Ultra Click"))},
    {"id": "power_district",  "name": "Power District",     "cat": "Ulepszenia",
     "desc": "Kup max lvl Solar, Coal i Nuclear Power.",
     "condition": lambda b: b.total_upgrades_bought >= 1 and all(
         b.upgrades.get(n, {}).get("owned", 0) >= b.upgrades.get(n, {}).get("max", 99)
         for n in ("Solar Power", "Coal Power", "Nuclear Power"))},
    {"id": "led_owner",       "name": "Ekolog",             "cat": "Ulepszenia",
     "desc": "Kup LED light.",
     "condition": lambda b: b.upgrades.get("LED light", {}).get("owned", 0) >= 1},
    {"id": "all_unlockable",  "name": "Kolekcjoner Ach",    "cat": "Ulepszenia",
     "desc": "Kup przynajmniej 1 szt. kazdego odblokowanego ulepszenia.",
     "condition": lambda b: len([n for n in UNLOCKABLE_UPGRADES if n in b.upgrades]) > 0 and all(
         b.upgrades.get(n, {}).get("owned", 0) >= 1
         for n in UNLOCKABLE_UPGRADES if n in b.upgrades)},

    # ── Randomizer ────────────────────────────────────────────────────────────
    {"id": "first_randomizer","name": "Hazardzista",        "cat": "Randomizer",
     "desc": "Uzyj Randomizera po raz pierwszy.",
     "condition": lambda b: b.upgrades.get("Randomizer", {}).get("owned", 0) >= 1},
    {"id": "randomizer_10",   "name": "Nalogowy Gracz",     "cat": "Randomizer",
     "desc": "Uzyj Randomizera 10 razy.",
     "condition": lambda b: b.upgrades.get("Randomizer", {}).get("owned", 0) >= 10},
    {"id": "randomizer_30",   "name": "Szaleniec RNG",      "cat": "Randomizer",
     "desc": "Uzyj Randomizera 30 razy.",
     "condition": lambda b: b.upgrades.get("Randomizer", {}).get("owned", 0) >= 30},
    
    # ── Kasyno ────────────────────────────────────────────────────────────────
    {"id": "first_blackjack", "name":"Black Jack",             "cat": "Kasyno",
     "desc": "Zagraj po raz pierwszy w Black Jack",
     "condition": lambda b: b.blackjack_played >= 1},

    # ── Trudność ──────────────────────────────────────────────────────────────
    {"id": "hell_mode",       "name": "Szalenstwo",         "cat": "Trudnosc",
     "desc": "Kliknij zarowke na poziomie Hell.",
     "condition": lambda b: b.current_difficulty == "Hell" and b.total_clicks >= 1},
    {"id": "hard_mode",       "name": "Hardkor",            "cat": "Trudnosc",
     "desc": "Zdobadz 10 000 pkt na Hard.",
     "condition": lambda b: b.current_difficulty == "Hard" and b.score >= 10_000},
    {"id": "easy_score_2000", "name": "Easy Money",         "cat": "Trudnosc",
     "desc": "Zdobadz 2 000 pkt na Easy.",
     "condition": lambda b: b.current_difficulty == "Easy" and b.score >= 2_000},

    # ── Czas gry ──────────────────────────────────────────────────────────────
    {"id": "playtime_120",    "name": "Rozgrzewka",         "cat": "Czas",
     "desc": "Graj przez lacznie 2 minuty.", "playtime_check": 120},
    {"id": "playtime_600",    "name": "Godzina Rozrywki",   "cat": "Czas",
     "desc": "Graj przez lacznie 10 minut.", "playtime_check": 600},
    {"id": "playtime_1800",   "name": "Polmaraton",         "cat": "Czas",
     "desc": "Graj przez lacznie 30 minut.", "playtime_check": 1800},
    {"id": "playtime_7200",   "name": "Maraton",            "cat": "Czas",
     "desc": "Graj przez lacznie 2 godziny.","playtime_check": 7200},

    # ── Pasywny dochód ────────────────────────────────────────────────────────
    {"id": "passive_20",      "name": "Rentier",            "cat": "Pasywne",
     "desc": "Osiagnij 20 passive/s.",
     "condition": lambda b: b.passive_income >= 20},
    {"id": "passive_100",     "name": "Spiacy Bogacz",      "cat": "Pasywne",
     "desc": "Osiagnij 100 passive/s.",
     "condition": lambda b: b.passive_income >= 100},
    {"id": "passive_500",     "name": "Magnat",             "cat": "Pasywne",
     "desc": "Osiagnij 500 passive/s.",
     "condition": lambda b: b.passive_income >= 500},
    {"id": "passive_2000",    "name": "Przemyslowiec",      "cat": "Pasywne",
     "desc": "Osiagnij 2 000 passive/s.",
     "condition": lambda b: b.passive_income >= 2_000},
    {"id": "passive_10000",   "name": "Korporacja",         "cat": "Pasywne",
     "desc": "Osiagnij 10 000 passive/s.",
     "condition": lambda b: b.passive_income >= 10_000},
]


# ──────────────────────────────────────────────────────────────────────────────
# KLASA SYSTEMU OSIĄGNIĘĆ
# ──────────────────────────────────────────────────────────────────────────────
class AchievementSystem:
    NOTIF_DURATION  = 5.0   # czas wyświetlania jednego powiadomienia
    NOTIF_FADE      = 0.8   # czas znikania (fade-out)
    NOTIF_INTERVAL  = 1.2   # minimalna przerwa między kolejnymi powiadomieniami
    MAX_VISIBLE     = 4     # ile powiadomień max naraz na ekranie

    def __init__(self):
        self.unlocked: set      = set()
        self.notifications: list = []   # aktywnie wyświetlane
        self._queue: list        = []   # czekające w kolejce
        self._queue_timer: float = 0.0  # odlicza kiedy można pokazać następne
        self.font_big    = pygame.font.Font(None, 40)
        self.font_small  = pygame.font.Font(None, 30)
        self.font_reward = pygame.font.Font(None, 26)
        self.font_cat    = pygame.font.Font(None, 24)
        self.panel = ScrollablePanel(None, width=820, height=840, row_h=82)

    # ── Sprawdzanie warunków ──────────────────────────────────────────────────
    def check(self, bulb, play_time_val: float):
        # Nie sprawdzaj achievementów dopóki gracz nie wybrał trudności
        if not bulb.difficulty_locked:
            return
        for ach in ACHIEVEMENTS_DEF:
            aid = ach["id"]
            if aid in self.unlocked:
                continue
            unlocked = False
            if "playtime_check" in ach:
                unlocked = play_time_val >= ach["playtime_check"]
            else:
                try:   unlocked = ach["condition"](bulb)
                except: pass
            if unlocked:
                self._unlock(ach, bulb)

    def _unlock(self, ach: dict, bulb=None):
        aid = ach["id"]
        self.unlocked.add(aid)
        reward = ACHIEVEMENT_REWARDS.get(aid)
        reward_desc = ""
        if reward and bulb is not None:
            self._apply_reward(reward, bulb)
            reward_desc = reward.get("desc", "")
        # Wrzuć do kolejki zamiast od razu wyświetlać
        self._queue.append({
            "ach": ach, "timer": self.NOTIF_DURATION,
            "reward_desc": reward_desc,
        })

    def _apply_reward(self, reward: dict, bulb):
        if "income_bonus"  in reward: bulb.income              += reward["income_bonus"]
        if "passive_bonus" in reward: bulb.passive_income      += reward["passive_bonus"]
        if "cooling_bonus" in reward: bulb.temperature_decrease+= reward["cooling_bonus"]
        if "penalty_reduction" in reward:
            bulb.penalty = max(0, bulb.penalty - reward["penalty_reduction"])
        if "overheat_threshold_bonus" in reward:
            bulb.overheat_threshold += reward["overheat_threshold_bonus"]
        if "unlock_upgrade" in reward:
            upg_name = reward["unlock_upgrade"]
            if upg_name in UNLOCKABLE_UPGRADES and upg_name not in bulb.upgrades:
                bulb.upgrades[upg_name] = dict(UNLOCKABLE_UPGRADES[upg_name])
                bulb.newly_unlocked_upgrades.add(upg_name)
        # Aktualizuj liczniki buffów dla HUD
        bulb.ach_income_bonus      = sum(
            ACHIEVEMENT_REWARDS.get(a, {}).get("income_bonus", 0) for a in self.unlocked)
        bulb.ach_passive_bonus     = sum(
            ACHIEVEMENT_REWARDS.get(a, {}).get("passive_bonus", 0) for a in self.unlocked)
        bulb.ach_cooling_bonus     = sum(
            ACHIEVEMENT_REWARDS.get(a, {}).get("cooling_bonus", 0.0) for a in self.unlocked)
        bulb.ach_penalty_reduction = sum(
            ACHIEVEMENT_REWARDS.get(a, {}).get("penalty_reduction", 0) for a in self.unlocked)

    # ── Tick ──────────────────────────────────────────────────────────────────
    def tick(self, dt: float):
        # Aktualizuj aktywne powiadomienia
        for n in self.notifications:
            n["timer"] -= dt
        self.notifications = [n for n in self.notifications if n["timer"] > 0]

        # Wypuszczaj z kolejki jedno na raz z odstępem NOTIF_INTERVAL
        self._queue_timer -= dt
        if self._queue and self._queue_timer <= 0 and len(self.notifications) < self.MAX_VISIBLE:
            self.notifications.append(self._queue.pop(0))
            self._queue_timer = self.NOTIF_INTERVAL

    # ── Powiadomienia ─────────────────────────────────────────────────────────
    def draw_notifications(self, surface):
        w, h   = 500, 118
        x      = _render_w - w - 20
        y_base = 20
        for i, notif in enumerate(reversed(self.notifications)):
            ach   = notif["ach"]
            timer = notif["timer"]
            alpha = 255 if timer >= self.NOTIF_FADE else int(255 * timer / self.NOTIF_FADE)
            y     = y_base + i * (h + 8)
            if y + h > _render_h:
                break

            bg = pygame.Surface((w, h), pygame.SRCALPHA)
            bg.fill((*_colors.surface0, min(alpha, 235)))
            pygame.draw.rect(bg, (*_colors.yellow, alpha), (0, 0, w, h), 3)
            pygame.draw.line(bg, (*_colors.overlay1, alpha), (10, 70), (w-10, 70), 1)
            surface.blit(bg, (x, y))

            cat_s = _render_text(self.font_cat, f"[{ach.get('cat','?')}]", _colors.overlay1)
            cat_s.set_alpha(alpha); surface.blit(cat_s, (x+14, y+8))
            title = _render_text(self.font_small, f"  {ach['name']}", _colors.yellow)
            title.set_alpha(alpha); surface.blit(title, (x+14+cat_s.get_width(), y+8))
            desc  = _render_text(self.font_reward, ach["desc"], _colors.subtext0)
            desc.set_alpha(alpha); surface.blit(desc, (x+14, y+38))
            if notif["reward_desc"]:
                rew = _render_text(self.font_reward,
                                   f"  Nagroda: {notif['reward_desc']}", _colors.green)
                rew.set_alpha(alpha); surface.blit(rew, (x+14, y+78))

    # ── Panel osiągnięć ───────────────────────────────────────────────────────
    def draw_panel(self, surface):
        total = len(ACHIEVEMENTS_DEF)
        done  = len(self.unlocked)
        pct   = int(done / total * 100) if total else 0
        self.panel.screen = surface

        # Grupuj po kategoriach
        cats = {}
        for ach in ACHIEVEMENTS_DEF:
            cats.setdefault(ach.get("cat", "Inne"), []).append(ach)

        rows = []
        for cat, achs in cats.items():
            rows.append({"_header": cat})
            rows.extend(achs)

        def row_renderer(dst, row, rr):
            if "_header" in row:
                pygame.draw.rect(dst, _colors.mantle, rr)
                hs = _render_text(self.font_small, f"── {row['_header']} ──", _colors.yellow)
                dst.blit(hs, hs.get_rect(centerx=rr.centerx, centery=rr.centery))
                return None

            aid    = row["id"]
            locked = aid not in self.unlocked
            reward = ACHIEVEMENT_REWARDS.get(aid)

            bg = _colors.surface0 if locked else _colors.surface1
            pygame.draw.rect(dst, bg, rr)

            if not locked and reward:
                pygame.draw.rect(dst, _colors.green, rr, 2)
            elif locked:
                pygame.draw.rect(dst, _colors.overlay0, rr, 1)
            else:
                pygame.draw.rect(dst, _colors.yellow, rr, 1)

            nc  = _colors.overlay1 if locked else _colors.text
            pfx = "[X] " if locked else "[V] "
            ns  = _render_text(self.font_big, pfx + row["name"], nc)
            dst.blit(ns, (rr.x+8, rr.y+4))

            dc  = _colors.overlay0 if locked else _colors.subtext1
            ds  = _render_text(self.font_reward, row["desc"], dc)
            dst.blit(ds, (rr.x+8, rr.y+36))

            if reward:
                rc  = _colors.overlay0 if locked else _colors.green
                rs  = _render_text(self.font_reward,
                                   f"  Nagroda: {reward['desc']}", rc)
                dst.blit(rs, (rr.x+8, rr.y+58))
            return None

        self.panel.draw(
            title="OSIAGNIECIA",
            rows=rows,
            row_renderer=row_renderer,
            close_label="Zamknij  [A]",
            info_text=f"Odblokowano: {done}/{total}  ({pct}%)   [scroll / up / dn]",
            progress=(done, total),
        )

    def handle_panel_event(self, event) -> bool:
        kind, _ = self.panel.handle_event(
            event, rows_len=len(ACHIEVEMENTS_DEF)+len(set(a.get("cat","") for a in ACHIEVEMENTS_DEF)),
            close_keys=(pygame.K_a, pygame.K_ESCAPE),
        )
        return kind == "close"

    # ── Serializacja ──────────────────────────────────────────────────────────
    def to_dict(self) -> dict: return {"unlocked": list(self.unlocked)}
    def load_from_dict(self, data: dict):
        self.unlocked = set(data.get("unlocked", []))
        # Wyczyść kolejkę i powiadomienia – przy wczytaniu nic nie pokazujemy
        self.notifications = []
        self._queue        = []
        self._queue_timer  = 0.0
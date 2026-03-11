# minigames/__init__.py
# Wspólny interfejs mini-gier dla main.py
# Każda gra jest też uruchamialna samodzielnie (python -m minigames.blackjack etc.)

from .blackjack import BlackjackGame
from .rps       import RPSGame
from .plinko    import PlinkoGame

__all__ = ["BlackjackGame", "RPSGame", "PlinkoGame", "MiniGameHub"]


class MiniGameHub:
    """
    Fasada używana przez main.py.
    Przechowuje aktywną grę i przekazuje score z/do Zarowka.
    """

    def __init__(self, screen):
        self.screen      = screen
        self.active_game = None   # None | BlackjackGame | RPSGame | PlinkoGame
        self.visible     = False
        self._menu_open  = False

        # Fonty (Catppuccin Mocha palette injected via init())
        import pygame
        self._font_title = pygame.font.Font(None, 52)
        self._font_btn   = pygame.font.Font(None, 38)
        self._font_sm    = pygame.font.Font(None, 26)
        self._C          = None   # injected by main via init()
        self._rw = 1920
        self._rh = 1080

        # Rect dla przycisków menu gier
        self._btns = []

    # ── Inicjalizacja kontekstu ────────────────────────────────────────────────
    def init(self, colors, rw, rh):
        self._C  = colors
        self._rw = rw
        self._rh = rh

    def set_render_size(self, rw, rh):
        self._rw = rw
        self._rh = rh

    # ── Otwórz/zamknij hub ────────────────────────────────────────────────────
    def open(self):
        self.visible     = True
        self._menu_open  = True
        self.active_game = None

    def close(self):
        self.visible     = False
        self._menu_open  = False
        self.active_game = None

    @property
    def is_open(self):
        return self.visible

    # ── Główna pętla zdarzeń ──────────────────────────────────────────────────
    def handle_event(self, event, bulb) -> bool:
        """Zwraca True jeśli event został skonsumowany."""
        if not self.visible:
            return False

        import pygame
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.active_game:
                # Zablokuj ESC gdy gra czeka na odbiór wyniku
                result_states = ("RESULT", "FINAL")
                if getattr(self.active_game, '_state', None) in result_states:
                    return True   # konsumuj event, ale nic nie rób
                self.active_game = None
                self._menu_open  = True
            else:
                self.close()
            return True

        if self.active_game:
            result = self.active_game.handle_event(event)
            if result is not None:
                bet = self.active_game.bet
                if bet > 0:
                    # result=0 → przegrana (strata stawki)
                    # result=1 → remis (zwrot)
                    # result>1 → wygrana (zysk)
                    delta = bet * result - bet   # ujemne przy przegranej
                    bulb.score = max(0.0, bulb.score + delta)
                self.active_game = None
                self._menu_open  = True
            return True

        # Obsługa menu wyboru gry
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, game_fn in self._btns:
                if rect.collidepoint(event.pos):
                    game_fn(bulb)
                    return True
        return True   # zawsze konsumuj gdy hub otwarty

    # ── Rysowanie ─────────────────────────────────────────────────────────────
    def draw(self, surface, bulb):
        if not self.visible:
            return

        if self.active_game:
            self.active_game.draw(surface)
            return

        self._draw_menu(surface, bulb)

    def _draw_menu(self, surface, bulb):
        import pygame
        C   = self._C
        cx  = self._rw // 2
        cy  = self._rh // 2
        W, H = 600, 500
        panel = pygame.Rect(cx - W//2, cy - H//2, W, H)

        pygame.draw.rect(surface, C.base,   panel, border_radius=12)
        pygame.draw.rect(surface, C.yellow, panel, 3, border_radius=12)

        ts = self._font_title.render("MINI GRY", True, C.yellow)
        surface.blit(ts, ts.get_rect(centerx=cx, y=panel.y + 22))

        score_s = self._font_sm.render(
            f"Twoje score: {bulb.fmt_score()}  |  [ESC] zamknij", True, C.subtext1)
        surface.blit(score_s, score_s.get_rect(centerx=cx, y=panel.y + 72))

        pygame.draw.line(surface, C.overlay0,
                         (panel.x+20, panel.y+98), (panel.right-20, panel.y+98), 1)

        GAMES = [
            ("♠  Czarny Jack",    C.sky,   self._launch_bj),
            ("✂  RPS + Jaszcz.",  C.green, self._launch_rps),
            ("●  Plinko",         C.mauve, self._launch_plinko),
        ]

        self._btns = []
        bw, bh = 480, 72
        by = panel.y + 116
        for label, col, fn in GAMES:
            r = pygame.Rect(cx - bw//2, by, bw, bh)
            pygame.draw.rect(surface, C.surface1, r, border_radius=8)
            pygame.draw.rect(surface, col,        r, 2, border_radius=8)
            ls = self._font_btn.render(label, True, col)
            surface.blit(ls, ls.get_rect(center=r.center))
            self._btns.append((r, fn))
            by += bh + 14

    # ── Launchers ─────────────────────────────────────────────────────────────
    def _launch_bj(self, bulb):
        self._menu_open  = False
        self.active_game = BlackjackGame(
            screen=None, colors=self._C, rw=self._rw, rh=self._rh,
            score=bulb.score, standalone=False)

    def _launch_rps(self, bulb):
        self._menu_open  = False
        self.active_game = RPSGame(
            screen=None, colors=self._C, rw=self._rw, rh=self._rh,
            score=bulb.score, standalone=False)

    def _launch_plinko(self, bulb):
        self._menu_open  = False
        self.active_game = PlinkoGame(
            screen=None, colors=self._C, rw=self._rw, rh=self._rh,
            score=bulb.score, standalone=False)
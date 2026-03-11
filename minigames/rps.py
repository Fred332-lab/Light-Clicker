# minigames/rps.py  –  Kamień Papier Nożyce Jaszczurka Spock  (best-of-5)
# Uruchamialny samodzielnie:  python minigames/rps.py

import pygame
import random

class _CMocha:
    rosewater=(245,224,220); red=(243,139,168); yellow=(249,226,175)
    green=(166,227,161);     teal=(148,226,213); sky=(137,220,235)
    blue=(137,180,250);      lavender=(180,190,254); peach=(250,179,135)
    mauve=(203,166,247);     text=(205,214,244); subtext1=(186,194,222)
    subtext0=(166,173,200);  overlay2=(147,153,178); overlay1=(127,132,156)
    overlay0=(108,112,134);  surface2=(88,91,112); surface1=(69,71,90)
    surface0=(49,50,68);     base=(30,30,46); mantle=(24,24,37); crust=(17,17,27)

# ── Zasady RPSLS ──────────────────────────────────────────────────────────────
# Kamień miażdży Nożyce i depcze Jaszczurkę
# Papier obejmuje Kamień i dyskredytuje Spocka
# Nożyce tną Papier i dekapitują Jaszczurkę
# Jaszczurka zatruwa Spocka i zjada Papier
# Spock rozbija Kamień i waporyzuje Nożyce

CHOICES = ["Kamień", "Papier", "Nożyce", "Jaszczurka", "Spock"]
ICONS   = ["🪨",     "📄",     "✂",      "🦎",         "🖖"]

# beats[i] = lista indeksów które i pokonuje
BEATS = {
    0: [2, 3],   # Kamień bije Nożyce, Jaszczurkę
    1: [0, 4],   # Papier bije Kamień, Spocka
    2: [1, 3],   # Nożyce biją Papier, Jaszczurkę
    3: [1, 4],   # Jaszczurka bije Papier, Spocka
    4: [0, 2],   # Spock bije Kamień, Nożyce
}

BEAT_FLAVOR = {
    (0,2): "Kamień miażdży Nożyce",
    (0,3): "Kamień depcze Jaszczurkę",
    (1,0): "Papier obejmuje Kamień",
    (1,4): "Papier dyskredytuje Spocka",
    (2,1): "Nożyce tną Papier",
    (2,3): "Nożyce dekapitują Jaszczurkę",
    (3,1): "Jaszczurka zjada Papier",
    (3,4): "Jaszczurka zatruwa Spocka",
    (4,0): "Spock rozbija Kamień",
    (4,2): "Spock waporyzuje Nożyce",
}

def _outcome(player_idx: int, cpu_idx: int) -> int:
    """1 = gracz wygrywa, 0 = remis, -1 = gracz przegrywa"""
    if player_idx == cpu_idx:    return 0
    if cpu_idx in BEATS[player_idx]: return 1
    return -1


class RPSGame:
    MAX_ROUNDS = 5

    def __init__(self, screen=None, colors=None, rw=1920, rh=1080,
                 score=0.0, standalone=False):
        self._C         = colors or _CMocha()
        self._rw        = rw
        self._rh        = rh
        self.score      = score
        self.bet        = 0
        self.standalone = standalone

        self._font_title = pygame.font.Font(None, 52)
        self._font_big   = pygame.font.Font(None, 64)
        self._font_btn   = pygame.font.Font(None, 36)
        self._font_sm    = pygame.font.Font(None, 26)
        self._font_info  = pygame.font.Font(None, 32)

        self._reset()

        if standalone:
            self._screen = pygame.display.set_mode((rw, rh), pygame.RESIZABLE)
            pygame.display.set_caption("Kamień Papier Nożyce Jaszczurka Spock")
            self._run_standalone()

    def _reset(self):
        self._state       = "BET"       # BET | CHOOSE | ROUND_RESULT | FINAL
        self._bet_input   = ""
        self._round       = 0           # 0-based
        self._player_wins = 0
        self._cpu_wins    = 0
        self._history     = []          # (player_idx, cpu_idx, outcome, flavor)
        self._last_player = None
        self._last_cpu    = None
        self._last_outcome= None
        self._last_flavor = ""
        self._final_mult  = 0.0
        self._btns        = []

    def _start(self):
        try:
            b = int(self._bet_input)
        except ValueError:
            return
        max_bet = int(self.score) if not self.standalone else 999_999_999
        if b <= 0 or b > max_bet:
            return
        self.bet    = b
        self._round = 0
        self._player_wins = 0
        self._cpu_wins    = 0
        self._history     = []
        self._state = "CHOOSE"

    def _choose(self, idx: int):
        cpu  = random.randrange(5)
        out  = _outcome(idx, cpu)
        flav = BEAT_FLAVOR.get((idx, cpu), BEAT_FLAVOR.get((cpu, idx), "Remis"))
        self._last_player  = idx
        self._last_cpu     = cpu
        self._last_outcome = out
        self._last_flavor  = flav
        self._history.append((idx, cpu, out, flav))
        if out ==  1: self._player_wins += 1
        if out == -1: self._cpu_wins    += 1
        self._round += 1
        self._state = "ROUND_RESULT"

    def _next_round(self):
        # Sprawdź czy ktoś już wygrał serię
        needed = self.MAX_ROUNDS // 2 + 1   # 3 z 5
        if self._player_wins >= needed or self._cpu_wins >= needed \
                or self._round >= self.MAX_ROUNDS:
            self._finish()
        else:
            self._state = "CHOOSE"

    def _finish(self):
        self._state = "FINAL"
        needed = self.MAX_ROUNDS // 2 + 1
        if self._player_wins > self._cpu_wins:
            # Mnożnik rośnie z ilością wygranych rund
            bonus = 1.0 + 0.25 * self._player_wins
            self._final_mult = 1.0 + bonus   # zwrot stawki + bonus
        elif self._player_wins == self._cpu_wins:
            self._final_mult = 1.0   # remis = zwrot stawki
        else:
            self._final_mult = 0.0

    # ── Events ────────────────────────────────────────────────────────────────
    def handle_event(self, event) -> "float | None":
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in self._btns:
                if rect.collidepoint(event.pos):
                    action()
                    if self._state == "FINAL":
                        # Zwróć mnożnik — hub naliczy wynik
                        return self._final_mult
                    return None
        if event.type == pygame.KEYDOWN and self._state == "BET":
            if event.key == pygame.K_RETURN:
                self._start()
            elif event.key == pygame.K_BACKSPACE:
                self._bet_input = self._bet_input[:-1]
            elif event.unicode.isdigit() and len(self._bet_input) < 12:
                self._bet_input += event.unicode
        return None

    # ── Rysowanie ─────────────────────────────────────────────────────────────
    def draw(self, surface):
        C  = self._C
        cx = self._rw // 2
        cy = self._rh // 2
        W, H = 900, 640
        panel = pygame.Rect(cx - W//2, cy - H//2, W, H)
        self._btns = []

        pygame.draw.rect(surface, C.base,  panel, border_radius=14)
        pygame.draw.rect(surface, C.green, panel, 3, border_radius=14)

        ts = self._font_title.render("✂  KPNJS  🖖", True, C.green)
        surface.blit(ts, ts.get_rect(centerx=cx, y=panel.y+16))

        # Pasek postępu rund
        y = panel.y + 70
        self._draw_scorebar(surface, panel, cx, y); y += 48
        pygame.draw.line(surface, C.overlay0,
                         (panel.x+20, y), (panel.right-20, y), 1); y += 16

        if self._state == "BET":
            self._draw_bet(surface, panel, cx, y)
        elif self._state == "CHOOSE":
            self._draw_choose(surface, panel, cx, y)
        elif self._state == "ROUND_RESULT":
            self._draw_round_result(surface, panel, cx, y)
        elif self._state == "FINAL":
            self._draw_final(surface, panel, cx, y)

    def _draw_scorebar(self, surface, panel, cx, y):
        C = self._C
        needed = self.MAX_ROUNDS // 2 + 1
        info = f"Runda {self._round}/{self.MAX_ROUNDS}   " \
               f"Ty: {self._player_wins}   CPU: {self._cpu_wins}   " \
               f"(potrzeba {needed} do wygranej)"
        s = self._font_sm.render(info, True, C.subtext1)
        surface.blit(s, s.get_rect(centerx=cx, y=y)); y += 22
        # Mini historia
        for i, (pi, ci, out, _) in enumerate(self._history):
            col = C.green if out == 1 else (C.yellow if out == 0 else C.red)
            sym = ICONS[pi] + " vs " + ICONS[ci]
            ms  = pygame.font.Font(None, 22).render(sym, True, col)
            surface.blit(ms, (panel.x + 20 + i*120, y))

    def _draw_bet(self, surface, panel, cx, y):
        C = self._C
        info = self._font_info.render("Podaj stawkę  [Enter]:", True, C.text)
        surface.blit(info, info.get_rect(centerx=cx, y=y)); y += 44

        iw, ih = 280, 46
        ir = pygame.Rect(cx - iw//2, y, iw, ih)
        pygame.draw.rect(surface, C.surface0, ir, border_radius=6)
        pygame.draw.rect(surface, C.yellow,   ir, 2, border_radius=6)
        ts = self._font_info.render((self._bet_input or "0") + "|", True, C.yellow)
        surface.blit(ts, ts.get_rect(center=ir.center)); y += 60

        if not self.standalone:
            sc = self._font_sm.render(f"Score: {int(self.score)}", True, C.subtext1)
            surface.blit(sc, sc.get_rect(centerx=cx, y=y)); y += 30

        # Mnożniki info
        lines = [
            "Wygrana: +25% stawki × ile rund wygrałeś  (max +125%)",
            "Remis:   zwrot stawki",
            "Przegrana: tracisz stawkę",
        ]
        for l in lines:
            ls = self._font_sm.render(l, True, C.overlay1)
            surface.blit(ls, ls.get_rect(centerx=cx, y=y)); y += 22
        y += 12

        br = pygame.Rect(cx-110, y, 220, 50)
        pygame.draw.rect(surface, C.green, br, border_radius=8)
        bs = self._font_btn.render("ZAGRAJ", True, C.base)
        surface.blit(bs, bs.get_rect(center=br.center))
        self._btns.append((br, self._start))

    def _draw_choose(self, surface, panel, cx, y):
        C = self._C
        prompt = self._font_info.render("Wybierz:", True, C.text)
        surface.blit(prompt, prompt.get_rect(centerx=cx, y=y)); y += 44

        bw, bh = 130, 110
        gap    = 16
        total  = len(CHOICES)*(bw+gap)-gap
        bx     = cx - total//2

        for i, (name, icon) in enumerate(zip(CHOICES, ICONS)):
            r = pygame.Rect(bx, y, bw, bh)
            pygame.draw.rect(surface, C.surface1, r, border_radius=10)
            pygame.draw.rect(surface, C.green,    r, 2, border_radius=10)
            # Ikona
            icon_s = pygame.font.Font(None, 56).render(icon, True, C.text)
            surface.blit(icon_s, icon_s.get_rect(centerx=r.centerx, y=r.y+8))
            ns = self._font_sm.render(name, True, C.subtext1)
            surface.blit(ns, ns.get_rect(centerx=r.centerx, y=r.bottom-26))
            idx = i
            self._btns.append((r, lambda i=idx: self._choose(i)))
            bx += bw + gap

    def _draw_round_result(self, surface, panel, cx, y):
        C  = self._C
        pi = self._last_player
        ci = self._last_cpu
        out= self._last_outcome

        # Ikony
        ps = pygame.font.Font(None, 90).render(ICONS[pi], True, C.text)
        vs = self._font_btn.render("vs", True, C.overlay1)
        cs = pygame.font.Font(None, 90).render(ICONS[ci], True, C.text)
        surface.blit(ps, ps.get_rect(centerx=cx-120, y=y))
        surface.blit(vs, vs.get_rect(centerx=cx, centery=y+44))
        surface.blit(cs, cs.get_rect(centerx=cx+120, y=y))
        y += 100

        col = C.green if out==1 else (C.yellow if out==0 else C.red)
        msg = "Wygrałeś rundę!" if out==1 else ("Remis!" if out==0 else "Przegrałeś rundę.")
        ms  = self._font_info.render(msg, True, col)
        surface.blit(ms, ms.get_rect(centerx=cx, y=y)); y += 36
        fl  = self._font_sm.render(self._last_flavor, True, C.subtext0)
        surface.blit(fl, fl.get_rect(centerx=cx, y=y)); y += 44

        nr = pygame.Rect(cx-110, y, 220, 50)
        pygame.draw.rect(surface, C.surface1, nr, border_radius=8)
        pygame.draw.rect(surface, C.sky,      nr, 2, border_radius=8)
        ns  = self._font_btn.render("Następna runda", True, C.sky)
        surface.blit(ns, ns.get_rect(center=nr.center))
        self._btns.append((nr, self._next_round))

    def _draw_final(self, surface, panel, cx, y):
        C = self._C
        won = self._player_wins > self._cpu_wins
        tie = self._player_wins == self._cpu_wins
        col = C.green if won else (C.yellow if tie else C.red)
        msg = "🏆 WYGRAŁEŚ SERIĘ!" if won else ("🤝 REMIS" if tie else "💀 PRZEGRAŁEŚ")
        ms  = self._font_title.render(msg, True, col)
        surface.blit(ms, ms.get_rect(centerx=cx, y=y)); y += 60

        score_line = f"Ty: {self._player_wins}   CPU: {self._cpu_wins}"
        ss = self._font_info.render(score_line, True, C.text)
        surface.blit(ss, ss.get_rect(centerx=cx, y=y)); y += 38

        if not self.standalone:
            gain = int(self.bet * self._final_mult - self.bet)
            sign = "+" if gain >= 0 else ""
            gs = self._font_info.render(f"Zmiana score: {sign}{gain}", True, col)
            surface.blit(gs, gs.get_rect(centerx=cx, y=y)); y += 44

        nr = pygame.Rect(cx-110, y, 220, 50)
        pygame.draw.rect(surface, C.surface1, nr, border_radius=8)
        pygame.draw.rect(surface, C.green,    nr, 2, border_radius=8)
        ns  = self._font_btn.render("Zagraj ponownie", True, C.green)
        surface.blit(ns, ns.get_rect(center=nr.center))
        self._btns.append((nr, lambda: (self._reset(), setattr(self, '_state', 'BET'))))

    def _run_standalone(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit(); return
                self.handle_event(event)
            self._screen.fill(self._C.crust)
            self.draw(self._screen)
            hint = pygame.font.Font(None, 24).render("[ESC] wyjdź", True, self._C.overlay0)
            self._screen.blit(hint, (16, 16))
            pygame.display.flip()
            clock.tick(60)


if __name__ == "__main__":
    pygame.init()
    RPSGame(rw=1280, rh=720, standalone=True)

# minigames/plinko.py  –  Plinko!
# 8 rzędów kołków, 9 slotów wynikowych, animowana kulka
# Uruchamialny samodzielnie:  python minigames/plinko.py

import pygame
import random
import math

class _CMocha:
    rosewater=(245,224,220); red=(243,139,168); yellow=(249,226,175)
    green=(166,227,161);     teal=(148,226,213); sky=(137,220,235)
    blue=(137,180,250);      lavender=(180,190,254); peach=(250,179,135)
    mauve=(203,166,247);     text=(205,214,244); subtext1=(186,194,222)
    subtext0=(166,173,200);  overlay2=(147,153,178); overlay1=(127,132,156)
    overlay0=(108,112,134);  surface2=(88,91,112); surface1=(69,71,90)
    surface0=(49,50,68);     base=(30,30,46); mantle=(24,24,37); crust=(17,17,27)

MULTIPLIERS = [10.0, 5.0, 3.0, 1.0, 0.2, 1.0, 3.0, 5.0, 10.0]

def _slot_color(C, idx):
    m = MULTIPLIERS[idx]
    if m >= 5.0:  return C.green
    if m >= 2.0:  return C.yellow
    if m >= 0.5:  return C.peach
    return C.red


class Ball:
    ROWS   = 8
    RADIUS = 10

    def __init__(self, start_x, start_y, peg_spacing_x, peg_spacing_y, slot_rects):
        self.x    = float(start_x)
        self.y    = float(start_y)
        self._sx  = peg_spacing_x
        self._sy  = peg_spacing_y
        self._slot_rects = slot_rects

        self._row  = 0
        self._done = False
        self._slot = None

        self._anim_t   = 0.0
        self._anim_spd = 2.8
        self._from_x   = float(start_x)
        self._from_y   = float(start_y)
        self._target_x = float(start_x)
        self._target_y = float(start_y)

        self._plan_path()
        self._set_next_target()

    def _plan_path(self):
        self._path = [random.choice([-1, 1]) for _ in range(self.ROWS)]
        self._slot = sum(1 for d in self._path if d == 1)

    def _set_next_target(self):
        self._from_x = self.x
        self._from_y = self.y
        if self._row < self.ROWS:
            # Skok między kołkami
            d = self._path[self._row]
            self._target_x = self.x + d * self._sx * 0.5
            self._target_y = self.y + self._sy
        else:
            # Ostatni krok: opuść się do środka slotu
            sr = self._slot_rects[self._slot]
            self._target_x = float(sr.centerx)
            self._target_y = float(sr.centery)

    def update(self, dt):
        if self._done:
            return
        self._anim_t += dt * self._anim_spd
        if self._anim_t >= 1.0:
            self.x = self._target_x
            self.y = self._target_y
            self._anim_t = 0.0
            self._row += 1
            if self._row > self.ROWS:
                # Krok do slotu zakończony
                self._done = True
                return
            self._set_next_target()

        t    = self._anim_t
        ease = math.sin(t * math.pi) * 10
        self.x = self._from_x + (self._target_x - self._from_x) * t
        self.y = self._from_y + (self._target_y - self._from_y) * t - ease

    def draw(self, surface, color):
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.RADIUS)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x) - 3, int(self.y) - 3), 3)

    def skip_to_end(self):
        sr = self._slot_rects[self._slot]
        self.x = float(sr.centerx)
        self.y = float(sr.centery)
        self._row  = self.ROWS + 1
        self._done = True


class PlinkoGame:
    ROWS       = 8
    PEG_RADIUS = 6

    def __init__(self, screen=None, colors=None, rw=1920, rh=1080,
                 score=0.0, standalone=False):
        self._C         = colors or _CMocha()
        self._rw        = rw
        self._rh        = rh
        self.score      = score
        self.bet        = 0
        self.standalone = standalone

        self._font_title = pygame.font.Font(None, 52)
        self._font_btn   = pygame.font.Font(None, 36)
        self._font_sm    = pygame.font.Font(None, 26)
        self._font_info  = pygame.font.Font(None, 32)
        self._font_mult  = pygame.font.Font(None, 28)

        self._RESULT_BTN_SENTINEL = object()

        self._board_w = 560
        self._board_h = 420
        self._compute_geometry()
        self._reset()

        if standalone:
            self._screen = pygame.display.set_mode((rw, rh), pygame.RESIZABLE)
            pygame.display.set_caption("Plinko ●")
            self._run_standalone()

    def _compute_geometry(self):
        cx = self._rw // 2

        pw, ph = 700, 660
        self._panel = pygame.Rect(cx - pw//2, self._rh//2 - ph//2, pw, ph)

        bx = cx - self._board_w // 2
        by = self._panel.y + 90
        self._board_x = bx
        self._board_y = by

        self._peg_sx = self._board_w / (self.ROWS + 1)
        self._peg_sy = (self._board_h - 60) / self.ROWS

        self._pegs = []
        for r in range(self.ROWS):
            row_pegs = r + 2
            row_w    = (row_pegs - 1) * self._peg_sx
            row_x0   = bx + self._board_w/2 - row_w/2
            row_y    = by + (r + 1) * self._peg_sy
            for p in range(row_pegs):
                self._pegs.append((row_x0 + p * self._peg_sx, row_y))

        slot_y   = by + self._board_h - 30
        n_slots  = self.ROWS + 1
        slot_w   = self._board_w / n_slots
        self._slots_y    = slot_y
        self._slot_w     = slot_w
        self._slot_rects = []
        for i in range(n_slots):
            sx = bx + i * slot_w
            self._slot_rects.append(
                pygame.Rect(int(sx), int(slot_y), int(slot_w) - 2, 44))

        self._ball_start_x = bx + self._board_w / 2
        self._ball_start_y = by + 8

    def _reset(self):
        self._state       = "BET"
        self._bet_input   = ""
        self._ball        = None
        self._result_mult = None
        self._result_slot = None
        self._btns        = []

    def _start(self):
        try:
            b = int(self._bet_input)
        except ValueError:
            return
        max_bet = int(self.score) if not self.standalone else 999_999_999
        if b <= 0 or b > max_bet:
            return
        self.bet  = b
        self._ball = Ball(
            self._ball_start_x,
            self._ball_start_y,
            self._peg_sx,
            self._peg_sy,
            self._slot_rects,
        )
        self._result_mult = None
        self._result_slot = None
        self._state       = "DROPPING"

    def _update(self, dt):
        if self._state != "DROPPING" or self._ball is None:
            return
        self._ball.update(dt)
        if self._ball._done:
            self._result_slot = self._ball._slot
            self._result_mult = MULTIPLIERS[self._result_slot]
            self._state       = "RESULT"

    def handle_event(self, event) -> "float | None":
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in self._btns:
                if rect.collidepoint(event.pos):
                    if action is self._RESULT_BTN_SENTINEL:
                        mult = self._result_mult
                        self._reset()
                        self._bet_input = str(self.bet)
                        self._state = "BET"
                        return mult
                    action()
                    return None
        if event.type == pygame.KEYDOWN and self._state == "BET":
            if event.key == pygame.K_RETURN:
                self._start()
            elif event.key == pygame.K_BACKSPACE:
                self._bet_input = self._bet_input[:-1]
            elif event.unicode.isdigit() and len(self._bet_input) < 12:
                self._bet_input += event.unicode
        if event.type == pygame.KEYDOWN and self._state == "DROPPING":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._skip_animation()
        return None

    def _skip_animation(self):
        if self._ball:
            self._ball.skip_to_end()
            self._result_slot = self._ball._slot
            self._result_mult = MULTIPLIERS[self._result_slot]
            self._state       = "RESULT"

    def draw(self, surface):
        self._compute_geometry()
        C  = self._C
        cx = self._rw // 2
        panel = self._panel
        self._btns = []

        pygame.draw.rect(surface, C.base,  panel, border_radius=14)
        pygame.draw.rect(surface, C.mauve, panel, 3, border_radius=14)

        ts = self._font_title.render("●  PLINKO  ●", True, C.mauve)
        surface.blit(ts, ts.get_rect(centerx=cx, y=panel.y + 16))

        if self._state == "BET":
            self._draw_bet(surface, panel, cx)
        else:
            self._draw_board(surface, cx)
            if self._state == "RESULT":
                self._draw_result(surface, panel, cx)
            else:
                sk = self._font_sm.render("[Spacja] pomiń animację", True, C.overlay0)
                surface.blit(sk, sk.get_rect(centerx=cx, y=panel.bottom - 36))

    def _draw_bet(self, surface, panel, cx):
        C = self._C
        self._draw_board(surface, cx, preview=True)

        oy = panel.y + 76
        info = self._font_info.render("Ustaw stawkę i puść kulkę:", True, C.text)
        surface.blit(info, info.get_rect(centerx=cx, y=oy)); oy += 42

        iw, ih = 260, 46
        ir = pygame.Rect(cx - iw//2, oy, iw, ih)
        pygame.draw.rect(surface, C.surface0, ir, border_radius=6)
        pygame.draw.rect(surface, C.yellow,   ir, 2, border_radius=6)
        ts = self._font_info.render((self._bet_input or "0") + "|", True, C.yellow)
        surface.blit(ts, ts.get_rect(center=ir.center)); oy += 58

        if not self.standalone:
            sc = self._font_sm.render(f"Score: {int(self.score)}", True, C.subtext1)
            surface.blit(sc, sc.get_rect(centerx=cx, y=oy)); oy += 30

        br = pygame.Rect(cx - 110, oy, 220, 50)
        pygame.draw.rect(surface, C.mauve, br, border_radius=8)
        bs = self._font_btn.render("PUŚĆ KULKĘ ▼", True, C.base)
        surface.blit(bs, bs.get_rect(center=br.center))
        self._btns.append((br, self._start))

    def _draw_board(self, surface, cx, preview=False):
        C = self._C

        board_rect = pygame.Rect(
            self._board_x - 10, self._board_y - 10,
            self._board_w + 20, self._board_h + 20)
        pygame.draw.rect(surface, C.mantle, board_rect, border_radius=8)

        peg_col = C.overlay2 if preview else C.subtext1
        for px, py in self._pegs:
            pygame.draw.circle(surface, peg_col, (int(px), int(py)), self.PEG_RADIUS)
            pygame.draw.circle(surface, C.overlay0, (int(px), int(py)), self.PEG_RADIUS, 1)

        for i, sr in enumerate(self._slot_rects):
            col   = _slot_color(C, i)
            alpha = 80 if preview else 180
            bg_s  = pygame.Surface((sr.width, sr.height), pygame.SRCALPHA)
            bg_s.fill((*col, alpha))
            surface.blit(bg_s, sr.topleft)
            pygame.draw.rect(surface, col, sr, 2)
            mult  = MULTIPLIERS[i]
            label = f"{mult:.0f}x" if mult >= 1.0 else f"{mult}x"
            ms    = self._font_mult.render(label, True, col)
            surface.blit(ms, ms.get_rect(centerx=sr.centerx, centery=sr.centery))

        if self._ball and not preview:
            if self._ball._done and self._result_slot is not None:
                sr = self._slot_rects[self._result_slot]
                hl = pygame.Surface((sr.width, sr.height), pygame.SRCALPHA)
                hl.fill((*C.peach, 140))
                surface.blit(hl, sr.topleft)
                pygame.draw.rect(surface, C.peach, sr, 3)
            self._ball.draw(surface, C.peach)

    def _draw_result(self, surface, panel, cx):
        C   = self._C
        m   = self._result_mult
        col = _slot_color(C, self._result_slot)

        y = self._slots_y + 60
        label = f"{m:.0f}x" if m >= 1.0 else f"{m}x"
        rs = self._font_title.render(f"Mnożnik: {label}", True, col)
        surface.blit(rs, rs.get_rect(centerx=cx, y=y)); y += 54

        if not self.standalone:
            gain = int(self.bet * m - self.bet)
            sign = "+" if gain >= 0 else ""
            gs = self._font_info.render(f"Zmiana score: {sign}{gain}", True, col)
            surface.blit(gs, gs.get_rect(centerx=cx, y=y)); y += 40

        nr = pygame.Rect(cx - 120, y, 240, 50)
        pygame.draw.rect(surface, C.surface1, nr, border_radius=8)
        pygame.draw.rect(surface, C.mauve,    nr, 2, border_radius=8)
        ns  = self._font_btn.render("Zagraj ponownie", True, C.mauve)
        surface.blit(ns, ns.get_rect(center=nr.center))
        self._btns.append((nr, self._RESULT_BTN_SENTINEL))

    def _run_standalone(self):
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit(); return
                self.handle_event(event)
            self._update(dt)
            self._screen.fill(self._C.crust)
            self.draw(self._screen)
            hint = pygame.font.Font(None, 24).render("[ESC] wyjdź", True, self._C.overlay0)
            self._screen.blit(hint, (16, 16))
            pygame.display.flip()


if __name__ == "__main__":
    pygame.init()
    PlinkoGame(rw=1280, rh=720, standalone=True)
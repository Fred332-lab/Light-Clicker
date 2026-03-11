# minigames/blackjack.py  –  Czarny Jack  (klasyczny, krupier dobiera do 17)
# Uruchamialny samodzielnie:  python minigames/blackjack.py
# Lub importowany przez MiniGameHub

import pygame
import random
import sys
import os

# ── Catppuccin Mocha (fallback gdy uruchomiony standalone) ────────────────────
class _CMocha:
    rosewater=(245,224,220); red=(243,139,168); yellow=(249,226,175)
    green=(166,227,161);     teal=(148,226,213); sky=(137,220,235)
    blue=(137,180,250);      lavender=(180,190,254); peach=(250,179,135)
    mauve=(203,166,247);     text=(205,214,244); subtext1=(186,194,222)
    subtext0=(166,173,200);  overlay2=(147,153,178); overlay1=(127,132,156)
    overlay0=(108,112,134);  surface2=(88,91,112); surface1=(69,71,90)
    surface0=(49,50,68);     base=(30,30,46); mantle=(24,24,37); crust=(17,17,27)

# ── Karty ─────────────────────────────────────────────────────────────────────
SUITS  = ["♠", "♥", "♦", "♣"]
RANKS  = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
SUIT_COLOR = {"♠": None, "♣": None, "♥": "red", "♦": "red"}  # None = text color

def _card_value(rank: str) -> int:
    if rank in ("J","Q","K"): return 10
    if rank == "A":           return 11
    return int(rank)

def _hand_value(hand: list) -> int:
    total = sum(_card_value(r) for r, _ in hand)
    aces  = sum(1 for r, _ in hand if r == "A")
    while total > 21 and aces:
        total -= 10
        aces  -= 1
    return total

def _new_deck() -> list:
    deck = [(r, s) for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck


# ── Klasa gry ─────────────────────────────────────────────────────────────────
class BlackjackGame:
    """
    standalone=True  → własna pętla pygame, gra bez score (dla funu)
    standalone=False → draw(surface) + handle_event(event) → zwraca float|None
    """

    STATES = ("BET", "PLAYER", "DEALER", "RESULT")

    def __init__(self, screen=None, colors=None, rw=1920, rh=1080,
                 score=0.0, standalone=False):
        self._C          = colors or _CMocha()
        self._rw         = rw
        self._rh         = rh
        self.score       = score          # tylko dla trybu embedded
        self.bet         = 0
        self.standalone  = standalone

        self._font_title = pygame.font.Font(None, 52)
        self._font_card  = pygame.font.Font(None, 72)
        self._font_btn   = pygame.font.Font(None, 38)
        self._font_sm    = pygame.font.Font(None, 28)
        self._font_info  = pygame.font.Font(None, 34)

        # Sentinel używany do identyfikacji przycisku "Następna runda" w handle_event
        self._NEXT_BTN_SENTINEL = object()

        self._reset()

        if standalone:
            self._screen = pygame.display.set_mode((rw, rh), pygame.RESIZABLE)
            pygame.display.set_caption("Czarny Jack  ♠")
            self._run_standalone()

    # ── Reset rundy ───────────────────────────────────────────────────────────
    def _reset(self):
        self._deck         = _new_deck()
        self._player_hand  = []
        self._dealer_hand  = []
        self._state        = "BET"
        self._result_msg   = ""
        self._multiplier   = 0.0
        self._bet_input    = ""
        self._doubled      = False
        self._dealer_reveal= False
        self._btns         = []

    def _deal_card(self, hand):
        if not self._deck:
            self._deck = _new_deck()
        hand.append(self._deck.pop())

    # ── Logika ────────────────────────────────────────────────────────────────
    def _start_round(self):
        try:
            b = int(self._bet_input)
        except ValueError:
            return
        max_bet = int(self.score) if not self.standalone else 999_999_999
        if b <= 0 or b > max_bet:
            return
        self.bet     = b
        self._doubled = False
        self._dealer_reveal = False
        self._player_hand = []
        self._dealer_hand = []
        for _ in range(2):
            self._deal_card(self._player_hand)
            self._deal_card(self._dealer_hand)
        pv = _hand_value(self._player_hand)
        if pv == 21:
            self._dealer_reveal = True
            self._end_round()
        else:
            self._state = "PLAYER"

    def _hit(self):
        self._deal_card(self._player_hand)
        if _hand_value(self._player_hand) > 21:
            self._dealer_reveal = True
            self._end_round()

    def _stand(self):
        self._dealer_reveal = True
        while _hand_value(self._dealer_hand) < 17:
            self._deal_card(self._dealer_hand)
        self._end_round()

    def _double_down(self):
        max_bet = int(self.score) if not self.standalone else 999_999_999
        if self.bet * 2 > max_bet:
            return
        self.bet    *= 2
        self._doubled = True
        self._deal_card(self._player_hand)
        if _hand_value(self._player_hand) > 21:
            self._dealer_reveal = True
            self._end_round()
        else:
            self._stand()

    def _end_round(self):
        self._state = "RESULT"
        pv = _hand_value(self._player_hand)
        dv = _hand_value(self._dealer_hand)
        bust_p = pv > 21
        bust_d = dv > 21

        if bust_p:
            self._result_msg = f"BUST! Przegrałeś."
            self._multiplier = 0.0
        elif pv == 21 and len(self._player_hand) == 2 and not self._doubled:
            self._result_msg = f"BLACKJACK! Wygrałeś 1.5×!"
            self._multiplier = 2.5   # zwraca bet + 1.5×bet
        elif bust_d or pv > dv:
            self._result_msg = f"Wygrałeś!"
            self._multiplier = 2.0
        elif pv == dv:
            self._result_msg = f"Remis."
            self._multiplier = 1.0
        else:
            self._result_msg = f"Przegrałeś."
            self._multiplier = 0.0

    # ── Event handler ─────────────────────────────────────────────────────────
    def handle_event(self, event) -> "float | None":
        """
        Zwraca float (mnożnik) gdy runda skończona, None gdy w trakcie.
        Mnożnik: 0=przegrana, 1=remis, 2=wygrana, 2.5=blackjack
        """
        import pygame
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in self._btns:
                if rect.collidepoint(event.pos):
                    if self._state == "RESULT" and action is self._NEXT_BTN_SENTINEL:
                        # Zwróć mnożnik do huba PRZED resetem
                        mult = self._multiplier
                        self._next_round()
                        return mult
                    action()
                    return None

        if event.type == pygame.KEYDOWN:
            if self._state == "BET":
                if event.key == pygame.K_RETURN:
                    self._start_round()
                elif event.key == pygame.K_BACKSPACE:
                    self._bet_input = self._bet_input[:-1]
                elif event.unicode.isdigit():
                    if len(self._bet_input) < 12:
                        self._bet_input += event.unicode
        return None

    def _next_round(self):
        self._bet_input = str(self.bet)
        self._reset()
        self._state = "BET"

    # ── Rysowanie ─────────────────────────────────────────────────────────────
    def draw(self, surface):
        C   = self._C
        cx  = self._rw // 2
        cy  = self._rh // 2
        W, H = 860, 620
        panel = pygame.Rect(cx - W//2, cy - H//2, W, H)
        self._btns = []

        # Tło
        pygame.draw.rect(surface, C.base, panel, border_radius=14)
        pygame.draw.rect(surface, C.sky,  panel, 3, border_radius=14)

        # Tytuł
        ts = self._font_title.render("♠  CZARNY JACK  ♠", True, C.sky)
        surface.blit(ts, ts.get_rect(centerx=cx, y=panel.y+16))
        pygame.draw.line(surface, C.overlay0,
                         (panel.x+20, panel.y+68), (panel.right-20, panel.y+68), 1)

        y = panel.y + 80

        if self._state == "BET":
            self._draw_bet_screen(surface, panel, cx, cy)
        else:
            self._draw_game_screen(surface, panel, cx, y)

    def _draw_bet_screen(self, surface, panel, cx, cy):
        C = self._C
        y = panel.y + 90

        info = self._font_info.render("Podaj stawkę i naciśnij ENTER:", True, C.text)
        surface.blit(info, info.get_rect(centerx=cx, y=y)); y += 44

        # Pole tekstowe
        iw, ih = 300, 48
        ir = pygame.Rect(cx - iw//2, y, iw, ih)
        pygame.draw.rect(surface, C.surface0, ir, border_radius=6)
        pygame.draw.rect(surface, C.yellow,   ir, 2, border_radius=6)
        disp = self._bet_input if self._bet_input else "0"
        ts = self._font_info.render(disp + "|", True, C.yellow)
        surface.blit(ts, ts.get_rect(center=ir.center))
        y += 68

        if not self.standalone:
            sc = self._font_sm.render(
                f"Score: {int(self.score)}  (max: {int(self.score)})", True, C.subtext1)
            surface.blit(sc, sc.get_rect(centerx=cx, y=y)); y += 36

        # Szybkie stawki
        quick = self._font_sm.render("Szybkie stawki:", True, C.overlay1)
        surface.blit(quick, quick.get_rect(centerx=cx, y=y)); y += 28
        max_score = int(self.score) if not self.standalone else 10000
        amounts = [10, 100, 500, 1000, max(1, max_score//4), max(1, max_score//2)]
        bw = 100; gap = 12; total_w = len(amounts)*(bw+gap)-gap
        bx = cx - total_w//2
        for amt in amounts:
            r = pygame.Rect(bx, y, bw, 36)
            pygame.draw.rect(surface, C.surface1, r, border_radius=6)
            pygame.draw.rect(surface, C.peach,    r, 1, border_radius=6)
            ls = self._font_sm.render(str(amt), True, C.peach)
            surface.blit(ls, ls.get_rect(center=r.center))
            amt_copy = amt
            def make_setter(a): return lambda: setattr(self, '_bet_input', str(min(a, max_score)))
            self._btns.append((r, make_setter(amt)))
            bx += bw + gap
        y += 56

        # Przycisk ZAGRAJ
        br = pygame.Rect(cx - 120, y, 240, 52)
        pygame.draw.rect(surface, C.sky,  br, border_radius=8)
        pygame.draw.rect(surface, C.blue, br, 2, border_radius=8)
        gs = self._font_btn.render("ZAGRAJ  [Enter]", True, C.base)
        surface.blit(gs, gs.get_rect(center=br.center))
        self._btns.append((br, self._start_round))

    def _draw_hand(self, surface, hand, label, x, y, hidden_second=False):
        C = self._C
        ls = self._font_sm.render(label, True, C.subtext1)
        surface.blit(ls, (x, y)); y += 26
        cw, ch = 70, 96
        for i, (rank, suit) in enumerate(hand):
            cr = pygame.Rect(x + i*(cw+8), y, cw, ch)
            if hidden_second and i == 1:
                pygame.draw.rect(surface, C.surface2, cr, border_radius=6)
                pygame.draw.rect(surface, C.overlay1, cr, 2, border_radius=6)
                qs = self._font_btn.render("?", True, C.overlay1)
                surface.blit(qs, qs.get_rect(center=cr.center))
            else:
                bg = C.surface0
                pygame.draw.rect(surface, bg, cr, border_radius=6)
                suit_red = suit in ("♥","♦")
                fc = C.red if suit_red else C.text
                pygame.draw.rect(surface, fc, cr, 2, border_radius=6)
                rs = self._font_info.render(rank, True, fc)
                ss = self._font_sm.render(suit, True, fc)
                surface.blit(rs, (cr.x+6, cr.y+4))
                surface.blit(ss, (cr.x+6, cr.y+28))
        return y + ch + 8

    def _draw_game_screen(self, surface, panel, cx, y):
        C = self._C
        reveal = self._dealer_reveal

        # Krupier
        dv_show = _hand_value(self._dealer_hand) if reveal else \
                  _card_value(self._dealer_hand[0][0])
        dlabel = f"Krupier  [{dv_show}]" + ("" if reveal else " + ?")
        y = self._draw_hand(surface, self._dealer_hand, dlabel,
                            panel.x+40, y, hidden_second=not reveal)

        pygame.draw.line(surface, C.overlay0,
                         (panel.x+20, y+10), (panel.right-20, y+10), 1)
        y += 24

        # Gracz
        pv = _hand_value(self._player_hand)
        bust = pv > 21
        pc = C.red if bust else C.text
        plabel = f"Ty  [{pv}]" + (" – BUST!" if bust else "")
        if not self.standalone:
            plabel += f"   Stawka: {self.bet}"
        y = self._draw_hand(surface, self._player_hand, plabel, panel.x+40, y)
        y += 8

        if self._state == "PLAYER":
            # Przyciski akcji
            actions = [("HIT", C.green, self._hit),
                       ("STAND", C.yellow, self._stand)]
            if len(self._player_hand) == 2:
                can_dd = self.standalone or self.bet * 2 <= int(self.score)
                col_dd = C.peach if can_dd else C.overlay1
                actions.append(("DOUBLE", col_dd, self._double_down if can_dd else lambda: None))
            bw = 160; gap = 20
            total = len(actions)*(bw+gap)-gap
            bx = cx - total//2
            for label, col, fn in actions:
                r = pygame.Rect(bx, y, bw, 52)
                pygame.draw.rect(surface, C.surface1, r, border_radius=8)
                pygame.draw.rect(surface, col,        r, 2, border_radius=8)
                ls = self._font_btn.render(label, True, col)
                surface.blit(ls, ls.get_rect(center=r.center))
                self._btns.append((r, fn))
                bx += bw + gap

        elif self._state == "RESULT":
            col = C.green if self._multiplier >= 2.0 else \
                  (C.yellow if self._multiplier == 1.0 else C.red)
            rs = self._font_btn.render(self._result_msg, True, col)
            surface.blit(rs, rs.get_rect(centerx=cx, y=y)); y += 52

            if not self.standalone:
                gain = int(self.bet * self._multiplier - self.bet)
                sign = "+" if gain >= 0 else ""
                gs = self._font_info.render(f"Zmiana score: {sign}{gain}", True, col)
                surface.blit(gs, gs.get_rect(centerx=cx, y=y)); y += 38

            nr = pygame.Rect(cx-140, y, 280, 52)
            pygame.draw.rect(surface, C.surface1, nr, border_radius=8)
            pygame.draw.rect(surface, C.sky,      nr, 2, border_radius=8)
            ns = self._font_btn.render("Następna runda", True, C.sky)
            surface.blit(ns, ns.get_rect(center=nr.center))
            self._btns.append((nr, self._NEXT_BTN_SENTINEL))

    # ── Standalone loop ───────────────────────────────────────────────────────
    def _run_standalone(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                result = self.handle_event(event)
                # W standalone po zakończeniu rundy resetujemy przez _next_round
            self._screen.fill(self._C.crust)
            self.draw(self._screen)
            hint = pygame.font.Font(None, 24).render("[ESC] wyjdź", True, self._C.overlay0)
            self._screen.blit(hint, (16, 16))
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()


# ── Uruchomienie standalone ───────────────────────────────────────────────────
if __name__ == "__main__":
    pygame.init()
    BlackjackGame(rw=1280, rh=720, standalone=True)
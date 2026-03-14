from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.clock import Clock
import random

# --- КЛАСС ИГРЫ ---
class CheckersGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.board = {}
        self.selected = None
        self.turn = "B"
        self.must_continue = None
        self.game_mode = "bot"
        self.setup_board()
        self.bind(pos=self.draw, size=self.draw)

    def setup_board(self):
        self.board = {(r, c): "" for r in range(8) for c in range(8)}
        for r in range(8):
            for c in range(8):
                if (r + c) % 2 != 0:
                    if r < 3: self.board[(r, c)] = "W"
                    if r > 4: self.board[(r, c)] = "B"

    def draw(self, *args):
        self.canvas.clear()
        cell = min(self.width, self.height) / 8
        off_x = (self.width - cell * 8) / 2
        off_y = (self.height - cell * 8) / 2

        with self.canvas:
            for r in range(8):
                for c in range(8):
                    Color(*(0.2, 0.2, 0.2) if (r + c) % 2 != 0 else (0.8, 0.7, 0.6))
                    x, y = off_x + c * cell, off_y + (7 - r) * cell
                    Rectangle(pos=(x, y), size=(cell, cell))
                    if self.selected == (r, c):
                        Color(0, 1, 0, 0.4)
                        Rectangle(pos=(x, y), size=(cell, cell))
                    p = self.board.get((r, c), "")
                    if p:
                        Color(*(0.1, 0.1, 0.1) if "B" in p else (0.9, 0.9, 0.9))
                        Ellipse(pos=(x + cell*0.15, y + cell*0.15), size=(cell*0.7, cell*0.7))
                        if "K" in p:
                            Color(0.8, 0.6, 0)
                            Line(circle=(x+cell/2, y+cell/2, cell*0.2), width=2)

    def on_touch_down(self, touch):
        if self.game_mode == "bot" and self.turn == "W": return
        cell = min(self.width, self.height) / 8
        off_x = (self.width - cell * 8) / 2
        off_y = (self.height - cell * 8) / 2
        c = int((touch.x - off_x) / cell)
        r = 7 - int((touch.y - off_y) / cell)
        if 0 <= r < 8 and 0 <= c < 8:
            piece = self.board.get((r, c), "")
            if self.turn in piece:
                if self.must_continue and self.selected != (r, c): return
                self.selected = (r, c)
            elif self.selected:
                self.try_move(self.selected, (r, c))
            self.draw()

    def get_piece_captures(self, pos):
        r, c = pos
        p = self.board[pos]
        caps = []
        enemy = "W" if "B" in p else "B"
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            mr, mc, nr, nc = r+dr, c+dc, r+dr*2, c+dc*2
            if 0 <= nr < 8 and 0 <= nc < 8:
                if enemy in self.board[(mr, mc)] and self.board[(nr, nc)] == "":
                    caps.append((pos, (nr, nc), (mr, mc)))
        return caps

    def try_move(self, start, end):
        all_caps = []
        for pos, p in self.board.items():
            if self.turn in p: all_caps.extend(self.get_piece_captures(pos))
        
        piece_caps = self.get_piece_captures(start)
        target_cap = next((m for m in piece_caps if m[1] == end), None)
        
        if all_caps:
            if target_cap: self.execute_move(target_cap, True)
        else:
            r1, c1, r2, c2 = start[0], start[1], end[0], end[1]
            dr, dc = r2 - r1, abs(c2 - c1)
            valid = False
            if "K" in self.board[start]: valid = abs(dr) == 1 and dc == 1
            elif self.board[start] == "B": valid = dr == -1 and dc == 1
            elif self.board[start] == "W": valid = dr == 1 and dc == 1
            if valid: self.execute_move((start, end, None), False)

    def execute_move(self, move, is_cap):
        start, end, victim = move
        self.board[end] = self.board[start]
        self.board[start] = ""
        if victim: self.board[victim] = ""
        if (self.turn == "B" and end == 0) or (self.turn == "W" and end == 7):
            self.board[end] = self.turn + "K"
        if is_cap and self.get_piece_captures(end):
            self.selected, self.must_continue = end, end
        else:
            self.must_continue = None
            self.selected = None
            self.turn = "W" if self.turn == "B" else "B"
            if self.game_mode == "bot" and self.turn == "W":
                Clock.schedule_once(self.ai_logic, 0.7)
        self.draw()

    def ai_logic(self, dt):
        all_caps = []
        for pos, p in self.board.items():
            if "W" in p: all_caps.extend(self.get_piece_captures(pos))
        if all_caps:
            self.execute_move(random.choice(all_caps), True)
        else:
            moves = []
            for (r, c), p in self.board.items():
                if "W" in p:
                    for dr, dc in [(1, -1), (1, 1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and self.board[(nr, nc)] == "":
                            moves.append(((r, c), (nr, nc), None))
            if moves: self.execute_move(random.choice(moves), False)

# --- ЭКРАНЫ ---
class MenuScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        box = BoxLayout(orientation='vertical', padding=50, spacing=20)
        box.add_widget(Label(text="ШАШКИ PRO", font_size='40sp', bold=True))
        
        b1 = Button(text="Бой с ботом", size_hint_y=None, height='60dp')
        b1.bind(on_release=lambda x: self.start_game("bot"))
        
        b2 = Button(text="Мультиплеер (Локально)", size_hint_y=None, height='60dp')
        b2.bind(on_release=lambda x: self.start_game("pvp"))
        
        box.add_widget(b1)
        box.add_widget(b2)
        self.add_widget(box)

    def start_game(self, mode):
        game_screen = self.manager.get_screen('game')
        game_screen.game.game_mode = mode
        game_screen.game.setup_board() # Сброс поля при новом входе
        game_screen.game.turn = "B"
        self.manager.current = 'game'

class GameScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.game = CheckersGame()
        self.add_widget(self.game)
        
        # Кнопка выхода в меню
        btn_back = Button(text="Меню", size_hint=(None, None), size=('80dp', '40dp'), pos=('10dp', '10dp'))
        btn_back.bind(on_release=self.go_back)
        self.add_widget(btn_back)

    def go_back(self, instance):
        self.manager.current = 'menu'

class CheckersApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == "__main__":
    CheckersApp().run()
#
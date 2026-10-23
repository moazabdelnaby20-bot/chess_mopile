import threading
from pathlib import Path

import arabic_reshaper
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import (
    Color,
    Ellipse,
    InstructionGroup,
    Line,
    RoundedRectangle,
)
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from bidi.algorithm import get_display

from chess_engine import BOARD_SIZE, ChessGame, PIECE_SYMBOLS


ASSET_DIR = Path(__file__).resolve().parent / "assets"
ARABIC_FONT = "ArabicFont"
CHESS_FONT = "ChessFont"
LabelBase.register(
    name=ARABIC_FONT,
    fn_regular=str(ASSET_DIR / "NotoSansArabic.ttf"),
)
LabelBase.register(
    name=CHESS_FONT,
    fn_regular=str(ASSET_DIR / "NotoSansSymbols2-Regular.ttf"),
)


def _rtl(text):
    return get_display(arabic_reshaper.reshape(str(text)))


APP_BACKGROUND = (0.95, 0.94, 0.89, 1)
PRIMARY_COLOR = (0.16, 0.3, 0.25, 1)
SECONDARY_COLOR = (0.27, 0.41, 0.44, 1)
TEXT_PRIMARY = (0.17, 0.23, 0.2, 1)
TEXT_MUTED = (0.4, 0.43, 0.39, 1)
LIGHT_SQUARE = (0.94, 0.85, 0.71, 1)
DARK_SQUARE = (0.65, 0.43, 0.29, 1)
SELECTED_SQUARE = (0.96, 0.78, 0.35, 1)
LAST_MOVE_SQUARE = (0.75, 0.78, 0.58, 1)
CHECK_SQUARE = (0.84, 0.34, 0.3, 1)
BOARD_FRAME = (0.25, 0.16, 0.11, 1)
WHITE_PIECE_COLOR = (1, 0.992, 0.961, 1)
BLACK_PIECE_COLOR = (0.09, 0.125, 0.165, 1)
WHITE_PIECE_OUTLINE = (0.365, 0.318, 0.282, 1)


class ChessBoard(FloatLayout):
    def __init__(self, on_square, **kwargs):
        super().__init__(**kwargs)
        self.on_square = on_square
        self.cells = {}
        self.game = None
        self.selected = None
        self.legal_moves = []
        self.last_move = None
        self.move_markers = InstructionGroup()
        self.canvas.after.add(self.move_markers)
        with self.canvas.before:
            Color(0.08, 0.06, 0.05, 0.18)
            self.board_shadow = RoundedRectangle()
            Color(*BOARD_FRAME)
            self.board_frame = RoundedRectangle()
            Color(0.58, 0.42, 0.28, 1)
            self.board_border = Line(
                rounded_rectangle=(0, 0, 0, 0, dp(18)),
                width=dp(3),
            )

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cell = Button(
                    text="",
                    font_size=dp(36),
                    font_name=CHESS_FONT,
                    size_hint=(None, None),
                    background_normal="",
                    background_down="",
                )
                cell.bind(
                    on_release=lambda _button, r=row, c=col: self.on_square(r, c)
                )
                self.cells[(row, col)] = cell
                self.add_widget(cell)

        self.bind(pos=self._layout_cells, size=self._layout_cells)
        self._layout_cells()

    def _layout_cells(self, *_args):
        square_size = min(self.width, self.height)
        frame_left = self.x + (self.width - square_size) / 2
        frame_bottom = self.y + (self.height - square_size) / 2
        frame_padding = dp(8)
        shadow_offset = dp(10)
        self.board_shadow.pos = (frame_left + shadow_offset, frame_bottom - shadow_offset)
        self.board_shadow.size = (square_size, square_size)
        self.board_shadow.radius = [dp(18)]
        self.board_frame.pos = (frame_left, frame_bottom)
        self.board_frame.size = (square_size, square_size)
        self.board_frame.radius = [dp(18)]
        self.board_border.rounded_rectangle = (
            frame_left,
            frame_bottom,
            square_size,
            square_size,
            dp(18),
        )
        inset = min(dp(14), square_size / 18)
        cell_size = max(0, square_size - inset * 2) / BOARD_SIZE
        left = frame_left + inset
        bottom = frame_bottom + inset
        for (row, col), cell in self.cells.items():
            cell.size = (cell_size, cell_size)
            cell.pos = (left + col * cell_size, bottom + (BOARD_SIZE - 1 - row) * cell_size)
            cell.font_size = min(dp(54), max(dp(20), cell_size * 0.76))
        self._draw_legal_move_markers()

    def _draw_legal_move_markers(self):
        self.move_markers.clear()
        if self.game is None:
            return

        destinations = {(move[0], move[1]) for move in self.legal_moves}
        for row, col in destinations:
            cell = self.cells[(row, col)]
            center_x, center_y = cell.center
            if self.game.board[row][col] == ".":
                radius = cell.width * 0.11
                self.move_markers.add(Color(0.2, 0.17, 0.14, 0.72))
                self.move_markers.add(
                    Ellipse(
                        pos=(center_x - radius, center_y - radius),
                        size=(radius * 2, radius * 2),
                    )
                )
            else:
                radius = cell.width * 0.39
                self.move_markers.add(Color(0.43, 0.23, 0.14, 0.9))
                self.move_markers.add(
                    Line(circle=(center_x, center_y, radius), width=dp(3))
                )

    def update_position(self, game, selected, legal_moves, last_move):
        self.game = game
        self.selected = selected
        self.legal_moves = legal_moves
        self.last_move = last_move
        checked_king = None
        if game._king_in_check(game.turn):
            king = "K" if game.turn == "w" else "k"
            checked_king = next(
                (
                    (row, col)
                    for row in range(BOARD_SIZE)
                    for col in range(BOARD_SIZE)
                    if game.board[row][col] == king
                ),
                None,
            )

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cell = self.cells[(row, col)]
                piece = game.board[row][col]
                cell.text = PIECE_SYMBOLS.get(piece, "")
                is_white_piece = piece.isupper()
                cell.color = WHITE_PIECE_COLOR if is_white_piece else BLACK_PIECE_COLOR
                cell.outline_color = WHITE_PIECE_OUTLINE
                cell.outline_width = dp(1) if is_white_piece else 0
                cell.background_color = (
                    SELECTED_SQUARE
                    if selected == (row, col)
                    else CHECK_SQUARE
                    if checked_king == (row, col)
                    else LAST_MOVE_SQUARE
                    if last_move is not None
                    and (row, col) in (
                        (last_move[0], last_move[1]),
                        (last_move[2], last_move[3]),
                    )
                    else LIGHT_SQUARE
                    if (row + col) % 2 == 0
                    else DARK_SQUARE
                )
        self._draw_legal_move_markers()


class ChessMobileApp(App):
    def build(self):
        self.title = "لعبة الشطرنج"
        Window.clearcolor = APP_BACKGROUND
        self.player_count = 2
        self.difficulty = "medium"
        self.game = ChessGame()
        self.selected = None
        self.selected_moves = []
        self.last_move = None
        self.last_mover = None
        self.thinking = False
        self._generation = 0
        self.root_layout = BoxLayout(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(10),
        )
        self.show_modes()
        return self.root_layout

    @staticmethod
    def _button(text, callback, font_size=18, height=58, color=PRIMARY_COLOR):
        button = Button(
            text=_rtl(text),
            font_size=dp(font_size),
            font_name=ARABIC_FONT,
            size_hint_y=None,
            height=dp(height),
            background_normal="",
            background_down="",
            background_color=color,
            color=(1, 1, 1, 1),
        )
        button.bind(on_release=lambda _button: callback())
        return button

    def show_modes(self):
        self._generation += 1
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(
            Label(
                text=_rtl("الشطرنج"),
                font_size=dp(34),
                font_name=ARABIC_FONT,
                bold=True,
                size_hint_y=None,
                height=dp(82),
                color=PRIMARY_COLOR,
            )
        )
        self.root_layout.add_widget(
            Label(
                text=_rtl("اختر طريقة اللعب"),
                font_size=dp(18),
                font_name=ARABIC_FONT,
                size_hint_y=None,
                height=dp(36),
                color=TEXT_MUTED,
            )
        )
        self.root_layout.add_widget(Widget())
        self.root_layout.add_widget(
            self._button(
                "ضد الكمبيوتر\nاختر مستوى التحدي",
                self.show_difficulties,
                font_size=22,
                height=116,
                color=PRIMARY_COLOR,
            )
        )
        self.root_layout.add_widget(
            self._button(
                "لاعبان على الجهاز نفسه\nالعبا بالتناوب على الرقعة",
                lambda: self.start_game(2, "medium"),
                font_size=20,
                height=116,
                color=SECONDARY_COLOR,
            )
        )
        self.root_layout.add_widget(Widget())

    def show_difficulties(self):
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(
            Label(
                text=_rtl("مستوى التحدي"),
                font_size=dp(28),
                font_name=ARABIC_FONT,
                bold=True,
                size_hint_y=None,
                height=dp(66),
                color=PRIMARY_COLOR,
            )
        )
        self.root_layout.add_widget(
            Label(
                text=_rtl("اختر المستوى المناسب لك"),
                font_size=dp(16),
                font_name=ARABIC_FONT,
                size_hint_y=None,
                height=dp(34),
                color=TEXT_MUTED,
            )
        )
        for title, level, color in (
            ("سهل\nتحدٍ بسيط ومناسب للمبتدئين", "easy", (0.27, 0.47, 0.35, 1)),
            ("متوسط\nتحدٍ متوازن", "medium", SECONDARY_COLOR),
            ("صعب\nتحدٍ أقوى ويتطلب تركيزًا", "hard", (0.48, 0.34, 0.31, 1)),
        ):
            self.root_layout.add_widget(
                self._button(
                    title,
                    lambda selected_level=level: self.start_game(
                        1, selected_level
                    ),
                    font_size=18,
                    height=88,
                    color=color,
                )
            )
        self.root_layout.add_widget(Widget())
        self.root_layout.add_widget(
            self._button(
                "رجوع لاختيار نمط اللعب",
                self.show_modes,
                font_size=15,
                height=48,
                color=TEXT_MUTED,
            )
        )

    def start_game(self, player_count, difficulty):
        self._generation += 1
        self.player_count = player_count
        self.difficulty = difficulty
        self.game = ChessGame(difficulty)
        self.selected = None
        self.selected_moves = []
        self.last_move = None
        self.last_mover = None
        self.thinking = False
        self._build_game_screen()
        self.refresh_game()
        if self.player_count == 1 and self.game.turn == "w":
            Clock.schedule_once(
                lambda dt: self._start_computer_move(dt, self._generation), 0.15
            )

    def _build_game_screen(self):
        self.root_layout.clear_widgets()
        toolbar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )
        toolbar.add_widget(
            self._button("القائمة", self.show_modes, font_size=14, height=48)
        )
        toolbar.add_widget(
            self._button(
                "لعبة جديدة",
                lambda: self.start_game(self.player_count, self.difficulty),
                font_size=14,
                height=48,
                color=PRIMARY_COLOR,
            )
        )
        self.root_layout.add_widget(toolbar)
        self.turn_label = Label(
            text="",
            font_size=dp(18),
            font_name=ARABIC_FONT,
            bold=True,
            size_hint_y=None,
            height=dp(38),
            color=TEXT_PRIMARY,
        )
        self.root_layout.add_widget(self.turn_label)
        self.status_label = Label(
            text="",
            font_size=dp(15),
            font_name=ARABIC_FONT,
            size_hint_y=None,
            height=dp(38),
            color=TEXT_MUTED,
        )
        self.root_layout.add_widget(self.status_label)
        self.board_view = ChessBoard(
            self.on_square, size_hint=(1, 1)
        )
        self.root_layout.add_widget(self.board_view)

    def on_square(self, row, col):
        if self.thinking or (self.player_count == 1 and self.game.turn == "w"):
            return

        if self.selected is not None:
            for move in self.selected_moves:
                if move[0] == row and move[1] == col:
                    if move[2] == "promotion":
                        self._choose_promotion(move)
                    else:
                        self._play_move(self.selected[0], self.selected[1], move)
                    return

        piece = self.game.board[row][col]
        if self.game._color(piece) == self.game.turn:
            self.selected = (row, col)
            self.selected_moves = self.game.legal_moves_from(row, col)
        else:
            self.selected = None
            self.selected_moves = []
        self.refresh_game()

    def _choose_promotion(self, move):
        popup_content = BoxLayout(
            orientation="vertical", spacing=dp(8), padding=dp(12)
        )
        popup = Popup(
            title=_rtl("اختر قطعة الترقية"),
            content=popup_content,
            size_hint=(0.82, None),
            height=dp(330),
            auto_dismiss=False,
        )
        choices = (
            ("Q", "وزير"),
            ("R", "قلعة"),
            ("B", "فيل"),
            ("N", "حصان"),
        )
        for piece, title in choices:
            popup_content.add_widget(
                self._button(
                    title,
                    lambda selected_piece=piece: self._finish_promotion(
                        popup, move, selected_piece
                    ),
                    font_size=17,
                    height=58,
                )
            )
        popup.open()

    def _finish_promotion(self, popup, move, choice):
        popup.dismiss()
        piece = choice if self.game.turn == "w" else choice.lower()
        self._play_move(self.selected[0], self.selected[1], (move[0], move[1], piece, None))

    def _play_move(self, from_row, from_col, move):
        self.last_mover = self.game.turn
        self.game.play_move(from_row, from_col, move)
        self.last_move = (from_row, from_col, move[0], move[1])
        self.selected = None
        self.selected_moves = []
        self.refresh_game()
        if self.player_count == 1 and self.game.turn == "w":
            generation = self._generation
            Clock.schedule_once(
                lambda dt: self._start_computer_move(dt, generation), 0.15
            )

    def _start_computer_move(self, _dt, generation):
        if (
            generation != self._generation
            or self.player_count != 1
            or self.game.turn != "w"
            or self.thinking
        ):
            return
        self.thinking = True
        self.status_label.text = _rtl("الكمبيوتر يفكر...")
        game = self.game
        generation = self._generation
        threading.Thread(
            target=self._calculate_computer_move,
            args=(game, generation),
            daemon=True,
        ).start()

    def _calculate_computer_move(self, game, generation):
        try:
            move = game.choose_computer_move()
            error = None
        except Exception as exc:
            move = None
            error = str(exc)
        Clock.schedule_once(
            lambda _dt: self._finish_computer_move(
                game, generation, move, error
            ),
            0,
        )

    def _finish_computer_move(self, game, generation, result, error):
        if generation != self._generation or game is not self.game:
            return
        self.thinking = False
        if error is not None:
            self.status_label.text = _rtl(
                f"تعذّر حساب نقلة الكمبيوتر: {error}"
            )
            return
        if result is None:
            self.refresh_game()
            return
        from_row, from_col, move = result
        self.last_mover = self.game.turn
        self.game.play_move(from_row, from_col, move)
        self.last_move = (from_row, from_col, move[0], move[1])
        self.refresh_game()

    def refresh_game(self):
        if not hasattr(self, "board_view"):
            return
        self.board_view.update_position(
            self.game, self.selected, self.selected_moves, self.last_move
        )
        self.turn_label.text = _rtl(
            "دور الكمبيوتر (الأبيض)"
            if self.player_count == 1 and self.game.turn == "w"
            else "دورك (الأسود)"
            if self.player_count == 1 and self.game.turn == "b"
            else "دور الأبيض"
            if self.game.turn == "w"
            else "دور الأسود"
        )
        moves = self.game.all_legal_moves()
        if not moves:
            if self.game._king_in_check(self.game.turn):
                winner = "الأبيض" if self.last_mover == "w" else "الأسود"
                self.status_label.text = _rtl(
                    "كش مات! فاز الأبيض"
                    if winner == "الأبيض"
                    else "كش مات! فاز الأسود"
                )
            else:
                self.status_label.text = _rtl("تعادل: لا توجد نقلات قانونية")
        elif self.game._king_in_check(self.game.turn):
            player = "الأبيض" if self.game.turn == "w" else "الأسود"
            self.status_label.text = _rtl(f"كش! ملك {player} مهدد")
        else:
            self.status_label.text = _rtl(
                "المس قطعة لعرض نقلاتها القانونية"
            )


if __name__ == "__main__":
    ChessMobileApp().run()

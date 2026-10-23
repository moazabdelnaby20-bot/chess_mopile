"""Chess rules and computer opponent shared by the mobile app."""

import random

BOARD_SIZE = 8


COMPUTER_MISTAKE_CHANCE = 0.2


COMPUTER_DIFFICULTIES = {
    "easy": (0.7, 1),
    "medium": (COMPUTER_MISTAKE_CHANCE, 2),
    "hard": (0.0, 3),
}


PIECE_SYMBOLS = {
    "K": "\u2654",
    "Q": "\u2655",
    "R": "\u2656",
    "B": "\u2657",
    "N": "\u2658",
    "P": "\u2659",
    "k": "\u265a",
    "q": "\u265b",
    "r": "\u265c",
    "b": "\u265d",
    "n": "\u265e",
    "p": "\u265f",
}


class ChessGame:
    # تهيئة حالة المباراة ومواضع القطع الأساسية.
    def __init__(self, difficulty="medium"):
        if difficulty not in COMPUTER_DIFFICULTIES:
            raise ValueError("مستوى صعوبة الكمبيوتر غير معروف")
        self.difficulty = difficulty
        # تهيئة وضع القطع وبيانات الدور والتبييت والأخذ بالتجاوز.
        self.board = [
            list("rnbqkbnr"),
            list("pppppppp"),
            list("........"),
            list("........"),
            list("........"),
            list("........"),
            list("PPPPPPPP"),
            list("RNBQKBNR"),
        ]
        self.turn = "w"
        self.castling_rights = set("KQkq")
        self.en_passant = None

    # إرجاع لون القطعة أو قيمة فارغة للمربع الخالي.
    @staticmethod
    def _color(piece):
        # تحديد لون القطعة، مع اعتبار المربع الفارغ بلا لون.
        if piece == ".":
            return None
        return "w" if piece.isupper() else "b"

    # فحص صحة إحداثيات المربع على رقعة الشطرنج.
    @staticmethod
    def _inside(row, col):
        # التحقق من أن إحداثيات المربع تقع داخل حدود اللوحة.
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    # التحقق من تعرض مربع لهجوم من قطع لون معين.
    def _square_attacked(self, row, col, by_color):
        # فحص ما إذا كانت أي قطعة من اللون المحدد تهاجم المربع.
        pawn = "P" if by_color == "w" else "p"
        pawn_source_row = row + 1 if by_color == "w" else row - 1
        for pawn_col in (col - 1, col + 1):
            if (
                self._inside(pawn_source_row, pawn_col)
                and self.board[pawn_source_row][pawn_col] == pawn
            ):
                return True

        knight = "N" if by_color == "w" else "n"
        for row_step, col_step in (
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1),
        ):
            target_row, target_col = row + row_step, col + col_step
            if (
                self._inside(target_row, target_col)
                and self.board[target_row][target_col] == knight
            ):
                return True

        king = "K" if by_color == "w" else "k"
        for row_step in (-1, 0, 1):
            for col_step in (-1, 0, 1):
                if row_step == 0 and col_step == 0:
                    continue
                target_row, target_col = row + row_step, col + col_step
                if (
                    self._inside(target_row, target_col)
                    and self.board[target_row][target_col] == king
                ):
                    return True

        directions = (
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        )
        for direction_index, (row_step, col_step) in enumerate(directions):
            target_row, target_col = row + row_step, col + col_step
            distance = 1
            while self._inside(target_row, target_col):
                piece = self.board[target_row][target_col]
                if piece != ".":
                    if self._color(piece) == by_color:
                        kind = piece.upper()
                        diagonal = direction_index >= 4
                        if (
                            kind == "Q"
                            or (diagonal and kind == "B")
                            or (not diagonal and kind == "R")
                            or (distance == 1 and kind == "K")
                        ):
                            return True
                    break
                target_row += row_step
                target_col += col_step
                distance += 1
        return False

    # تحديد ما إذا كان ملك اللون المحدد في حالة كش.
    def _king_in_check(self, color):
        # العثور على الملك والتحقق من تعرضه لهجوم الخصم.
        king = "K" if color == "w" else "k"
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.board[row][col] == king:
                    return self._square_attacked(
                        row, col, "b" if color == "w" else "w"
                    )
        return True

    # توليد النقلات المرشحة لقطعة واحدة قبل فحص سلامة الملك.
    def _pseudo_moves(self, row, col):
        # توليد النقلات الممكنة هندسيًا للقطعة قبل استبعاد ما يكشف الملك.
        piece = self.board[row][col]
        color = self._color(piece)
        kind = piece.upper()
        moves = []

        def add_if_available(target_row, target_col, special=None):
            if not self._inside(target_row, target_col):
                return
            target = self.board[target_row][target_col]
            if target == "." or self._color(target) != color:
                moves.append((target_row, target_col, special, None))

        # إضافة نقلات البيدق، بما فيها الترقية والأخذ بالتجاوز.
        if kind == "P":
            direction = -1 if color == "w" else 1
            start_row = 6 if color == "w" else 1
            promotion_row = 0 if color == "w" else 7
            next_row = row + direction
            if self._inside(next_row, col) and self.board[next_row][col] == ".":
                add_if_available(
                    next_row, col, "promotion" if next_row == promotion_row else None
                )
                double_row = row + 2 * direction
                if (
                    row == start_row
                    and self.board[double_row][col] == "."
                ):
                    add_if_available(double_row, col, "double_pawn")
            for target_col in (col - 1, col + 1):
                if not self._inside(next_row, target_col):
                    continue
                target = self.board[next_row][target_col]
                if target != "." and self._color(target) != color:
                    add_if_available(
                        next_row,
                        target_col,
                        "promotion" if next_row == promotion_row else None,
                    )
                elif self.en_passant == (next_row, target_col):
                    moves.append((next_row, target_col, "en_passant", None))

        # إضافة نقلات الحصان القافزة.
        elif kind == "N":
            for row_step, col_step in (
                (-2, -1), (-2, 1), (-1, -2), (-1, 2),
                (1, -2), (1, 2), (2, -1), (2, 1),
            ):
                add_if_available(row + row_step, col + col_step)

        # إضافة نقلات الفيل والقلعة والوزير على خطوط الحركة المناسبة.
        elif kind in ("B", "R", "Q"):
            directions = []
            if kind in ("B", "Q"):
                directions.extend(
                    ((-1, -1), (-1, 1), (1, -1), (1, 1))
                )
            if kind in ("R", "Q"):
                directions.extend(((-1, 0), (1, 0), (0, -1), (0, 1)))
            for row_step, col_step in directions:
                target_row, target_col = row + row_step, col + col_step
                while self._inside(target_row, target_col):
                    target = self.board[target_row][target_col]
                    if target == ".":
                        moves.append((target_row, target_col, None, None))
                    else:
                        if self._color(target) != color:
                            moves.append((target_row, target_col, None, None))
                        break
                    target_row += row_step
                    target_col += col_step

        # إضافة نقلات الملك والتحقق من شروط التبييت.
        elif kind == "K":
            for row_step in (-1, 0, 1):
                for col_step in (-1, 0, 1):
                    if row_step != 0 or col_step != 0:
                        add_if_available(row + row_step, col + col_step)

            home_row = 7 if color == "w" else 0
            opponent = "b" if color == "w" else "w"
            if (
                row == home_row
                and col == 4
                and not self._king_in_check(color)
            ):
                king_side = "K" if color == "w" else "k"
                if (
                    king_side in self.castling_rights
                    and self.board[home_row][5] == "."
                    and self.board[home_row][6] == "."
                    and self.board[home_row][7] == ("R" if color == "w" else "r")
                    and not self._square_attacked(home_row, 5, opponent)
                    and not self._square_attacked(home_row, 6, opponent)
                ):
                    moves.append((home_row, 6, "castle", (home_row, 7, home_row, 5)))
                queen_side = "Q" if color == "w" else "q"
                if (
                    queen_side in self.castling_rights
                    and self.board[home_row][1] == "."
                    and self.board[home_row][2] == "."
                    and self.board[home_row][3] == "."
                    and self.board[home_row][0] == ("R" if color == "w" else "r")
                    and not self._square_attacked(home_row, 3, opponent)
                    and not self._square_attacked(home_row, 2, opponent)
                ):
                    moves.append((home_row, 2, "castle", (home_row, 0, home_row, 3)))
        return moves

    # تطبيق النقلة وتحديث تفاصيلها الخاصة وحقوق التبييت.
    def _apply_move(self, from_row, from_col, move):
        # تنفيذ النقلة وتحديث الحالات الخاصة مثل التبييت والأخذ بالتجاوز.
        to_row, to_col, special, castle_rook = move
        piece = self.board[from_row][from_col]
        captured = self.board[to_row][to_col]
        self.en_passant = None

        # إزالة البيدق المأخوذ بالتجاوز من مربعه الأصلي.
        if special == "en_passant":
            captured_row = to_row + (1 if piece.isupper() else -1)
            captured = self.board[captured_row][to_col]
            self.board[captured_row][to_col] = "."

        self.board[from_row][from_col] = "."
        self.board[to_row][to_col] = (
            special if special in ("Q", "R", "B", "N", "q", "r", "b", "n") else piece
        )
        # نقل القلعة إلى جوار الملك عند تنفيذ التبييت.
        if special == "castle":
            rook_from_row, rook_from_col, rook_to_row, rook_to_col = castle_rook
            self.board[rook_to_row][rook_to_col] = self.board[rook_from_row][rook_from_col]
            self.board[rook_from_row][rook_from_col] = "."

        # تسجيل المربع المستهدف المحتمل للأخذ بالتجاوز بعد حركة مزدوجة.
        if special == "double_pawn":
            self.en_passant = ((from_row + to_row) // 2, from_col)

        # تحديث حقوق التبييت عند تحريك الملك أو القلعة أو أخذها.
        if piece == "K":
            self.castling_rights.discard("K")
            self.castling_rights.discard("Q")
        elif piece == "k":
            self.castling_rights.discard("k")
            self.castling_rights.discard("q")

        rook_squares = {
            (7, 0): "Q",
            (7, 7): "K",
            (0, 0): "q",
            (0, 7): "k",
        }
        if piece.upper() == "R":
            self.castling_rights.discard(rook_squares.get((from_row, from_col), ""))
        if captured.upper() == "R":
            self.castling_rights.discard(rook_squares.get((to_row, to_col), ""))

    # إرجاع النقلات التي لا تعرض ملك اللاعب للهجوم.
    def legal_moves_from(self, row, col):
        # تصفية النقلات المرشحة والإبقاء على ما لا يترك الملك في كش.
        piece = self.board[row][col]
        if piece == "." or self._color(piece) != self.turn:
            return []

        legal_moves = []
        for move in self._pseudo_moves(row, col):
            board_before = [board_row[:] for board_row in self.board]
            rights_before = self.castling_rights.copy()
            en_passant_before = self.en_passant
            self._apply_move(row, col, move)
            if not self._king_in_check(self.turn):
                legal_moves.append(move)
            self.board = board_before
            self.castling_rights = rights_before
            self.en_passant = en_passant_before
        return legal_moves

    # جمع كل النقلات القانونية المتاحة للاعب الحالي.
    def all_legal_moves(self):
        # جمع النقلات القانونية لجميع قطع اللاعب صاحب الدور.
        moves = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self._color(self.board[row][col]) == self.turn:
                    for move in self.legal_moves_from(row, col):
                        moves.append((row, col, move))
        return moves

    # تنفيذ نقلة فعلية وتبديل اللاعب صاحب الدور.
    def play_move(self, from_row, from_col, move):
        # تنفيذ نقلة اللاعب ثم تمرير الدور إلى الخصم.
        self._apply_move(from_row, from_col, move)
        self.turn = "b" if self.turn == "w" else "w"

    # حساب تقييم تقريبي لمصلحة أحد اللونين في الوضع الحالي.
    def _evaluate_position(self):
        # تقدير قوة الوضع اعتمادًا على قيمة القطع ومواقعها على اللوحة.
        piece_values = {
            "P": 100,
            "N": 320,
            "B": 330,
            "R": 500,
            "Q": 900,
            "K": 0,
        }
        score = 0
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece == ".":
                    continue

                kind = piece.upper()
                value = piece_values[kind]
                center = max(
                    0,
                    3 - abs(row - 3.5) - abs(col - 3.5),
                )
                if kind == "P":
                    advancement = 6 - row if piece.isupper() else row - 1
                    value += advancement * 5
                elif kind == "N":
                    value += center * 8
                elif kind == "B":
                    value += center * 4
                elif kind == "Q":
                    value += center * 2

                score += value if piece.isupper() else -value

        return score if self.turn == "w" else -score

    # إعطاء أولوية للنقلات التي تتضمن أسرًا أو ترقية.
    def _move_order_score(self, move_data):
        # ترتيب النقلات لتجربة الأسر والترقية ذات القيمة الأعلى أولًا.
        from_row, from_col, move = move_data
        target = self.board[move[0]][move[1]]
        score = 0
        if move[2] == "en_passant":
            score += 100
        elif target != ".":
            piece_values = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}
            score += piece_values[target.upper()] - piece_values[
                self.board[from_row][from_col].upper()
            ] // 10
        if move[2] == "promotion":
            score += 900
        return score

    # استكشاف شجرة النقلات مع تقليم الفروع الأقل فائدة.
    def _search(self, depth, alpha, beta, ply):
        # البحث عن أفضل نتيجة مستقبلية باستخدام خوارزمية ألفا-بيتا.
        moves = self.all_legal_moves()
        if not moves:
            if self._king_in_check(self.turn):
                return -100000 + ply
            return 0
        if depth == 0:
            return self._evaluate_position()

        moves.sort(key=self._move_order_score, reverse=True)
        best_score = -float("inf")
        for from_row, from_col, move in moves:
            board_before = [board_row[:] for board_row in self.board]
            rights_before = self.castling_rights.copy()
            en_passant_before = self.en_passant
            turn_before = self.turn

            if move[2] == "promotion":
                move = (move[0], move[1], "q" if self.turn == "b" else "Q", None)
            self._apply_move(from_row, from_col, move)
            self.turn = "b" if self.turn == "w" else "w"
            score = -self._search(depth - 1, -beta, -alpha, ply + 1)

            self.board = board_before
            self.castling_rights = rights_before
            self.en_passant = en_passant_before
            self.turn = turn_before

            best_score = max(best_score, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        return best_score

    # اختيار أفضل نقلة للكمبيوتر من النقلات القانونية.
    def choose_computer_move(self):
        # تحليل النقلات القانونية واختيار واحدة من أفضل نقلات الكمبيوتر.
        moves = self.all_legal_moves()
        if not moves:
            return None

        mistake_chance, search_depth = COMPUTER_DIFFICULTIES[self.difficulty]
        # أحيانًا يختار الكمبيوتر نقلة قانونية عشوائية ليبدو أقل إتقانًا.
        if random.random() < mistake_chance:
            return random.choice(moves)

        moves.sort(key=self._move_order_score, reverse=True)
        best_score = -float("inf")
        alpha = -float("inf")
        best_moves = []
        for from_row, from_col, move in moves:
            board_before = [board_row[:] for board_row in self.board]
            rights_before = self.castling_rights.copy()
            en_passant_before = self.en_passant
            turn_before = self.turn

            if move[2] == "promotion":
                move = (move[0], move[1], "q" if self.turn == "b" else "Q", None)
            self._apply_move(from_row, from_col, move)
            self.turn = "b" if self.turn == "w" else "w"
            score = -self._search(search_depth, -float("inf"), -alpha, 1)

            self.board = board_before
            self.castling_rights = rights_before
            self.en_passant = en_passant_before
            self.turn = turn_before

            if score > best_score:
                best_score = score
                best_moves = [(from_row, from_col, move)]
            elif score == best_score:
                best_moves.append((from_row, from_col, move))
            alpha = max(alpha, score)

        return random.choice(best_moves)

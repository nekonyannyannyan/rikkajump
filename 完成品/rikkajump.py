import random
import pyxel
import math

# 画面サイズ（横を広げた）
WIDTH = 360
HEIGHT = 240

# 物理パラメータ
GRAVITY = 0.2          # 重力
JUMP_VELOCITY = -4.0   # 自動ジャンプ時の上向き初速
SCROLL_SPEED = 0.5     # 足場側を下に流す速度

# プレイヤー（キャラは 16x16）
PLAYER_W = 16
PLAYER_H = 16
PLAYER_SPEED = 2.0     # 横移動速度

# 足場タイルサイズ（この高さは固定で使う）
PLATFORM_TILE_W = 8
PLATFORM_TILE_H = 8

# 足場の横タイル数（幅）をランダムにする範囲
PLATFORM_MIN_TILES = 2   # 2タイル = 16px
PLATFORM_MAX_TILES = 6   # 6タイル = 48px（大きすぎない範囲）

# 足場の出現範囲（上下・横の揺れ）
PLATFORM_MIN_DY = 18    # 縦の最小間隔
PLATFORM_MAX_DY = 50    # 縦の最大間隔
PLATFORM_MAX_DX = 95   # 横の最大ズレ

# コイン
COIN_COLLISION_R = 8    # 当たり判定用半径

# スコア
SCORE_COIN_SMALL = 1
SCORE_COIN_BIG = 5      # S コイン

# ========= dot.pyxres のスプライト定義 =========

IMG_BANK = 0

# リッカ
RIKKA_U = 0
RIKKA_V = 0
RIKKA_W = 16
RIKKA_H = 16

# コイン（S付きの大きいコイン）
COIN_BIG_U = 16
COIN_BIG_V = 0
COIN_BIG_W = 16
COIN_BIG_H = 16

# 小さいコイン
COIN_SMALL_U = 32
COIN_SMALL_V = 0
COIN_SMALL_W = 16
COIN_SMALL_H = 16

# 足場タイル（木の模様の1タイル。左上 0,16 にある想定）
PLATFORM_U = 0
PLATFORM_V = 16


class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        # 実際の位置は Game 側で足場の上に置き直す
        self.x = WIDTH // 2
        self.y = HEIGHT - 40
        self.vy = 0.0
        self.is_alive = True

    def update(self, platforms):
        if not self.is_alive:
            return

        # 左右移動 (キーボード)
        if pyxel.btn(pyxel.KEY_LEFT):
            self.x -= PLAYER_SPEED
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.x += PLAYER_SPEED

        # 左右移動 (タッチ/マウス)
        # スマホ対応: 画面左半分タッチで左、右半分で右
        if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            if pyxel.mouse_x < WIDTH // 2:
                self.x -= PLAYER_SPEED
            else:
                self.x += PLAYER_SPEED

        # 画面外に出ないよう制限
        self.x = max(0, min(WIDTH - PLAYER_W, self.x))

        # 重力
        self.vy += GRAVITY
        self.y += self.vy

        # 足場との当たり判定（落下中のみ）
        if self.vy >= 0:
            for p in platforms:
                if (
                    self.x + PLAYER_W > p.x
                    and self.x < p.x + p.w
                    and self.y + PLAYER_H > p.y
                    and self.y + PLAYER_H < p.y + p.h + 5
                ):
                    self.y = p.y - PLAYER_H
                    self.vy = JUMP_VELOCITY  # ホッピングジャンプ
                    break

        # 画面下まで落ちたら死亡
        if self.y > HEIGHT:
            self.is_alive = False

    def draw(self):
        # 左キーまたはマウス左側タッチ時に反転
        is_left = pyxel.btn(pyxel.KEY_LEFT) or (pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and pyxel.mouse_x < WIDTH // 2)
        flip = -1 if is_left else 1
        pyxel.blt(
            self.x,
            self.y,
            IMG_BANK,
            RIKKA_U,
            RIKKA_V,
            RIKKA_W * flip,
            RIKKA_H,
            0,
        )


class Platform:
    def __init__(self, x, y, w):
        self.x = x
        self.y = y
        self.w = w                      # ピクセル幅（タイル枚数 × 8）
        self.h = PLATFORM_TILE_H

    def update(self):
        self.y += SCROLL_SPEED

    def draw(self):
        # 幅に応じてタイルを横に並べて描画
        tiles = self.w // PLATFORM_TILE_W
        for i in range(tiles):
            pyxel.blt(
                self.x + i * PLATFORM_TILE_W,
                self.y,
                IMG_BANK,
                PLATFORM_U,
                PLATFORM_V,
                PLATFORM_TILE_W,
                PLATFORM_TILE_H,
                0,
            )


class Coin:
    def __init__(self, x, y, is_big=False):
        self.x = x
        self.y = y
        self.is_big = is_big   # True = Sコイン(★), False = 通常コイン
        self.collected = False

    def update(self):
        self.y += SCROLL_SPEED

    def draw(self):
        if self.collected:
            return

        if self.is_big:
            u, v, w, h = COIN_BIG_U, COIN_BIG_V, COIN_BIG_W, COIN_BIG_H
        else:
            u, v, w, h = COIN_SMALL_U, COIN_SMALL_V, COIN_SMALL_W, COIN_SMALL_H

        pyxel.blt(
            self.x - w // 2,
            self.y - h // 2,
            IMG_BANK,
            u,
            v,
            w,
            h,
            0,
        )


class Game:
    def __init__(self):
        # タッチ操作のためにマウスカーソルを表示（PC確認用、スマホでは見えないが重要）
        # capture=True にするとマウスが見えなくなるが、スマホタップのエミュレーションには影響なし
        # ここでは分かりやすく表示したままにする、あるいは消す
        pyxel.init(WIDTH, HEIGHT, title="RikkaJump", fps=60)
        pyxel.mouse(True) # マウスカーソル表示
        pyxel.load("dot.pyxres")
        
        self.setup_background()

        self.state = "TITLE"  # "TITLE" / "PLAY" / "GAMEOVER"

        self.player = Player()
        self.platforms = []
        self.coins = []
        self.score = 0
        self.height_score = 0.0
        self.world_offset = 0.0

        self.init_world()
        self.place_player_on_bottom_platform()

        pyxel.run(self.update, self.draw)

    def setup_background(self):
        # -----------------------------------------------------
        # 1. テクスチャ生成 (Image Bank 1)
        # -----------------------------------------------------
        # 木の内壁（樹皮）のようなテクスチャを生成
        # 足場と同じような色合い（オレンジとベージュ）にする
        # ベース: 9(Orange)
        pyxel.image(1).rect(0, 0, 64, 64, 9) 
        
        # 明るい筋（ベージュ）と少し暗い筋（茶色）を入れて木目感を出す
        for y in range(64):
            for x in range(64):
                if random.random() < 0.2:
                    # 15(Beige) or 4(Brown) for variation
                    c = 15 if random.random() < 0.6 else 4
                    pyxel.image(1).pset(x, y, c)

        # 縦の深い溝 (アクセント)
        for i in range(8):
            x = random.randint(0, 63)
            for y in range(64):
                if random.random() > 0.3:
                    pyxel.image(1).pset(x, y, 4)

    # -------- 描画 --------
    def draw(self):
        if self.state == "TITLE":
            self.draw_title()
        elif self.state == "PLAY":
            self.draw_play()
        elif self.state == "GAMEOVER":
            self.draw_gameover()

    def draw_background(self):
        # 木の中身（空洞）の部分を濃い茶色で表現
        pyxel.cls(4)  # Brown (Pyxelのパレットで標準的な茶色)
        
        # もしもっと暗い茶色が良ければ、2(Dark Purple)と4を市松模様にする手もあるが
        # 一旦 4(Brown) で塗りつぶす

        # 左右に壁を描画
        # 壁の幅 = 40px
        wall_w = 40
        uv_scroll = (self.world_offset * 0.5) % 64
        
        for y in range(-64, HEIGHT, 64):
            draw_y = y + uv_scroll
            
            # 左壁
            pyxel.blt(0, draw_y, 1, 0, 0, wall_w, 64)
            # 右壁 (テクスチャを反転して少し見た目を変える)
            pyxel.blt(WIDTH - wall_w, draw_y, 1, 0, 0, -wall_w, 64)
            
        # 境界線（少し明るくして立体感を出す）
        pyxel.line(wall_w, 0, wall_w, HEIGHT, 4)
        pyxel.line(WIDTH - wall_w - 1, 0, WIDTH - wall_w - 1, HEIGHT, 4)

    # 足場の横タイル数をランダムに決めて、幅（px）を返す
    def random_platform_width(self):
        tiles = random.randint(PLATFORM_MIN_TILES, PLATFORM_MAX_TILES)
        return tiles * PLATFORM_TILE_W

    # 一番下の足場にプレイヤーを乗せる
    def place_player_on_bottom_platform(self):
        if not self.platforms:
            return
        bottom = max(self.platforms, key=lambda p: p.y)
        self.player.x = bottom.x + bottom.w // 2 - PLAYER_W // 2
        self.player.y = bottom.y - PLAYER_H
        self.player.vy = 0.0

    # -------- ワールド初期化 --------
    def init_world(self):
        self.platforms.clear()
        self.coins.clear()

        start_y = HEIGHT - 20
        # 最初の足場の幅（タイル数ランダム）
        start_w = self.random_platform_width()
        start_x = WIDTH // 2 - start_w // 2

        first = Platform(start_x, start_y, start_w)
        self.platforms.append(first)

        prev_x = start_x
        y = start_y

        # 上方向に足場を生成
        while y > -HEIGHT:
            dy = random.randint(PLATFORM_MIN_DY, PLATFORM_MAX_DY)
            y -= dy

            # 次の足場の幅（タイル数ランダム）
            w = self.random_platform_width()

            dx = random.randint(-PLATFORM_MAX_DX, PLATFORM_MAX_DX)
            new_x = prev_x + dx

            # 左右の画面外に出ないよう制限（左右壁マージン40px）
            new_x = max(40, min(WIDTH - w - 40, new_x))

            plat = Platform(new_x, y, w)
            self.platforms.append(plat)

            # コイン配置（たまにSコイン）
            r = random.random()
            if r < 0.6:
                # 通常コイン
                cx = new_x + w // 2
                cy = y - 12
                self.coins.append(Coin(cx, cy, is_big=False))
            elif r < 0.7:
                # レアなSコイン
                cx = new_x + w // 2
                cy = y - 12
                self.coins.append(Coin(cx, cy, is_big=True))

            prev_x = new_x

    # -------- 画面上のさらに上に足場を追加 --------
    def spawn_new_platforms(self):
        if not self.platforms:
            return

        top_p = min(self.platforms, key=lambda p: p.y)
        y = top_p.y
        prev_x = top_p.x

        while y > -PLATFORM_MAX_DY:
            dy = random.randint(PLATFORM_MIN_DY, PLATFORM_MAX_DY)
            y -= dy

            w = self.random_platform_width()

            dx = random.randint(-PLATFORM_MAX_DX, PLATFORM_MAX_DX)
            new_x = prev_x + dx
            # 左右壁マージン 40px
            new_x = max(40, min(WIDTH - w - 40, new_x))

            plat = Platform(new_x, y, w)
            self.platforms.append(plat)

            # コイン（同じく通常メイン・Sはレア）
            r = random.random()
            if r < 0.6:
                cx = new_x + w // 2
                cy = y - 12
                self.coins.append(Coin(cx, cy, is_big=False))
            elif r < 0.7:
                cx = new_x + w // 2
                cy = y - 12
                self.coins.append(Coin(cx, cy, is_big=True))

            prev_x = new_x

    # -------- カメラ追従 --------
    def adjust_camera(self):
        target_y = HEIGHT * 0.55  # プレイヤーの理想高さ

        if self.player.y < target_y:
            dy = target_y - self.player.y

            self.player.y += dy
            for p in self.platforms:
                p.y += dy
            for c in self.coins:
                c.y += dy

            self.world_offset += dy

    # -------- 状態別 update --------
    def update(self):
        if self.state == "TITLE":
            self.update_title()
        elif self.state == "PLAY":
            self.update_play()
        elif self.state == "GAMEOVER":
            self.update_gameover()

    def update_title(self):
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.start_game()

    def start_game(self):
        self.init_world()
        self.player.reset()
        self.place_player_on_bottom_platform()

        self.score = 0
        self.height_score = 0.0
        self.world_offset = 0.0
        self.state = "PLAY"

    def update_play(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        self.player.update(self.platforms)
        self.adjust_camera()

        # 高さスコア
        self.world_offset += SCROLL_SPEED
        self.height_score = self.world_offset / 10.0

        # 足場・コインをスクロール
        for p in self.platforms:
            p.update()
        for c in self.coins:
            c.update()

        # 画面外を削除
        self.platforms = [p for p in self.platforms if p.y < HEIGHT + 20]
        self.coins = [c for c in self.coins if c.y < HEIGHT + 20 and not c.collected]

        # 新規足場生成
        self.spawn_new_platforms()

        # コイン取得判定
        for c in self.coins:
            if c.collected:
                continue
            dx = (self.player.x + PLAYER_W / 2) - c.x
            dy = (self.player.y + PLAYER_H / 2) - c.y
            if dx * dx + dy * dy < COIN_COLLISION_R * COIN_COLLISION_R:
                c.collected = True
                if c.is_big:
                    self.score += SCORE_COIN_BIG
                else:
                    self.score += SCORE_COIN_SMALL

        # 落下したらゲームオーバー
        if not self.player.is_alive:
            self.state = "GAMEOVER"

    def update_gameover(self):
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.start_game()





    def draw_ui_common(self):
        pyxel.text(5, 5, f"SCORE: {self.score}", 7)
        pyxel.text(5, 14, f"HEIGHT: {int(self.height_score)}", 7)

    def draw_title(self):
        self.draw_background()
        pyxel.text(WIDTH // 2 - 40, 80, "RIKKA JUMP", pyxel.frame_count % 16)
        pyxel.text(WIDTH // 2 - 52, 120, "PRESS SPACE / ENTER", 7)
        pyxel.text(WIDTH // 2 - 50, 150, "← → : MOVE   Q : QUIT", 6)

    def draw_play(self):
        self.draw_background()
        for p in self.platforms:
            p.draw()
        for c in self.coins:
            c.draw()
        self.player.draw()
        self.draw_ui_common()

    def draw_gameover(self):
        self.draw_play()
        pyxel.rect(WIDTH // 2 - 60, 80, 120, 80, 0)
        pyxel.text(WIDTH // 2 - 30, 90, "GAME OVER", 8)
        pyxel.text(WIDTH // 2 - 45, 115, f"SCORE  : {self.score}", 7)
        pyxel.text(WIDTH // 2 - 45, 125, f"HEIGHT : {int(self.height_score)}", 7)
        pyxel.text(WIDTH // 2 - 55, 145, "PRESS SPACE / ENTER", 10)


if __name__ == "__main__":
    Game()

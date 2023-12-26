import pygame
from pygame.locals import *
import os
import sys
import time

class Block(pygame.sprite.Sprite):
    """ブロック"""
    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        
        
class Enemy(pygame.sprite.Sprite):
    speed = 1        # 移動速度
    animcycle = 18   # アニメーション速度
    frame = 0
    move_width = 50  # 横方向の移動範囲
    def __init__(self, pos, shots):
        pygame.sprite.Sprite.__init__(self, self.containers)
        # self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.left = pos[0]  # 移動できる左端
        self.right = self.left + self.move_width  # 移動できる右端
        self.shots = shots  # 衝突判定用

    def update(self):
        # 横方向への移動
        self.rect.move_ip(self.speed, 0)
        if self.rect.center[0] < self.left or self.rect.center[0] > self.right:
            self.speed = -self.speed
        # キャラクターアニメーション
        self.frame += 1
        # self.image = self.images[int(self.frame/self.animcycle%2)]
        self.collision()  # ミサイルとの衝突判定処理
    
    def collision(self):
        # ミサイルとの衝突判定
        for shot in self.shots:
            collide = self.rect.colliderect(shot.rect)
            if collide:  # 衝突するミサイルあり
                self.kill()
                

class Shot(pygame.sprite.Sprite):
    def __init__(self, pos, player_x, blocks):
        # imageとcontainersはmain()でセット
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.rect = self.image.get_rect()
        self.rect.center = pos   # 中心座標をposに
        self.player_x = player_x # プレーヤーの向き判定
        self.blocks = blocks     # 衝突判定用
        self.speed = 9           # ミサイルの移動速度

    def update(self):
        if self.player_x == 1:
            self.rect.move_ip(self.speed, 0)  # 右へ移動
        elif self.player_x == 0:
            self.rect.move_ip(-self.speed, 0)  # 左へ移動

        """衝突判定"""
        # ブロックとミサイルの衝突判定
        for block in self.blocks:
            collide = self.rect.colliderect(block.rect)
            if collide:  # 衝突するブロックあり
                self.kill()
                
        
class Kokaton(pygame.sprite.Sprite):
    """エネミー"""
    # MOVE_SPEED = 2.5    # 移動速度
    # JUMP_SPEED = 6.0    # ジャンプの初速度
    # GRAVITY = 0.2       # 重力加速度
    # MAX_JUMP_COUNT = 2  # ジャンプ段数の回数

    """こうかとん"""
    MOVE_SPEED = 5.0    # 移動速度
    JUMP_SPEED = 4.0    # ジャンプの初速度
    GRAVITY = 0.2       # 重力加速度
    MAX_JUMP_COUNT = 8  # ジャンプ段数の回数
    RELOAD_TIME = 15     # リロード時間

    def __init__(self, pos, blocks, enemys):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.right_image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos[0], pos[1]  # 座標設定
        self.blocks = blocks   # 衝突判定用
        self.enemys = enemys   # 衝突判定用
        self.reload_timer = 0  # リロード時間
        self.life = 100  # こうかとんのライフ数
        self.coltm = 0

        # ジャンプ回数
        self.jump_count = 0

        # 浮動小数点の位置と速度
        self.fpx = float(self.rect.x)
        self.fpy = float(self.rect.y)
        self.fpvx = 0.0
        self.fpvy = 0.0

        # 地面にいるか？
        self.on_floor = False

        # プレーヤーの向き add
        self.player_x = 1

    def update(self):
        """スプライトの更新"""
        # キー入力取得
        pressed_keys = pygame.key.get_pressed()

        # 左右移動
        if pressed_keys[K_RIGHT]:
            self.image = self.right_image
            self.fpvx = self.MOVE_SPEED
            self.player_x = 1
        elif pressed_keys[K_LEFT]:
            self.image = self.left_image
            self.fpvx = -self.MOVE_SPEED
            self.player_x = 0
        else:
            self.fpvx = 0.0

        # ジャンプ
        if pressed_keys[K_SPACE]:
            if self.on_floor:
                self.fpvy = - self.JUMP_SPEED  # 上向きに初速度を与える
                self.on_floor = False
                self.jump_count = 1
            elif not self.prev_button and self.jump_count < self.MAX_JUMP_COUNT:
                self.fpvy = -self.JUMP_SPEED
                self.jump_count += 1

        # ミサイルの発射 add
        if pressed_keys[K_s]:
            # リロード時間が5になるまで再発射できない
            if self.reload_timer > self.RELOAD_TIME:
                Shot(self.rect.center, self.player_x, self.blocks)  # 作成すると同時にallに追加される
                self.reload_timer = 0
            else:
                self.reload_timer += 1 # リロード中

        # 速度を更新
        if not self.on_floor:
            self.fpvy += self.GRAVITY  # 下向きに重力をかける

        self.collision_x()  # X方向の衝突判定処理
        self.collision_y()  # Y方向の衝突判定処理
        self.collision_e()  # 敵との衝突判定処理

        # 浮動小数点の位置を整数座標に戻す
        # スプライトを動かすにはself.rectの更新が必要！
        self.rect.x = int(self.fpx)
        self.rect.y = int(self.fpy)

        # ボタンのジャンプキーの状態を記録
        self.prev_button = pressed_keys[K_SPACE]

    def collision_e(self):
        # ミサイルとの衝突判定
        for enemy in self.enemys:
            collide = self.rect.colliderect(enemy.rect)
            if self.coltm == 0:
                if collide:  # 衝突するミサイルあり
                    self.image = self.down_image
                    self.life -= 10  # ライフを一つ減少
                    self.coltm += 1
                    self.fpvy = - self.JUMP_SPEED * 2  # 上向きに初速度を与える
            elif 1 <= self.coltm < 180:
                self.coltm += 1
            else:
                self.down_flag = 0
                self.coltm = 0
        # return down_flag

    def collision_x(self):
        """X方向の衝突判定処理"""
        # エネミーのサイズ
        width = self.rect.width
        height = self.rect.height

        # X方向の移動先の座標と矩形を求める
        newx = self.fpx + self.fpvx
        newrect = Rect(newx, self.fpy, width, height)

        # ブロックとの衝突判定
        for block in self.blocks:
            collide = newrect.colliderect(block.rect)
            if collide:  # 衝突するブロックあり
                if self.fpvx > 0:    # 右に移動中に衝突
                    # めり込まないように調整して速度を0に
                    self.fpx = block.rect.left - width
                    self.fpvx = 0
                elif self.fpvx < 0:  # 左に移動中に衝突
                    self.fpx = block.rect.right
                    self.fpvx = 0
                break  # 衝突ブロックは1個調べれば十分
            else:
                # 衝突ブロックがない場合、位置を更新
                self.fpx = newx

    def collision_y(self):
        """Y方向の衝突判定処理"""
        # エネミーのサイズ
        width = self.rect.width
        height = self.rect.height

        # Y方向の移動先の座標と矩形を求める
        newy = self.fpy + self.fpvy
        newrect = Rect(self.fpx, newy, width, height)

        # ブロックとの衝突判定
        for block in self.blocks:
            collide = newrect.colliderect(block.rect)
            if collide:  # 衝突するブロックあり
                if self.fpvy > 0:    # 下に移動中に衝突
                    # めり込まないように調整して速度を0に
                    self.fpy = block.rect.top - height
                    self.fpvy = 0
                    # 下に移動中に衝突したなら床の上にいる
                    self.on_floor = True
                    self.jump_count = 0  # ジャンプカウントをリセット
                elif self.fpvy < 0:  # 上に移動中に衝突
                    self.fpy = block.rect.bottom
                    self.fpvy = 0
                break  # 衝突ブロックは1個調べれば十分
            else:
                # 衝突ブロックがない場合、位置を更新
                self.fpy = newy
                # 衝突ブロックがないなら床の上にいない
                self.on_floor = False


class Kokaton_Life:
    """こうかとんの残りライフを表示するためのクラス"""
    def __init__(self, life):
        self.font = pygame.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.img = self.font.render(f"残りライフ：{life}", 0, (0, 0, 255))
        
    def update(self, life, screen):
        self.img = self.font.render(f"残りライフ：{life}", 0, (255, 0, 0))
        screen.blit(self.img, (400, 30))        
                

class Map:
    """マップ（プレイヤーや内部のスプライトを含む）"""
    GS = 33  # グリッドサイズ

    def __init__(self, filename):
        # スプライトグループの登録
        self.all = pygame.sprite.RenderUpdates()
        self.blocks = pygame.sprite.Group()
        self.enemys = pygame.sprite.Group()  # エイリアングループ
        self.shots = pygame.sprite.Group()   # ミサイルグループ
        Kokaton.containers = self.all
        Block.containers = self.all, self.blocks
        Shot.containers = self.all, self.shots  # add
        Enemy.containers = self.all, self.enemys # add

        # プレイヤーの作成
        self.kokaton = Kokaton((300,200), self.blocks, self.enemys)

        # 敵を作成
        # self.enemys = Enemy((100,100))
        # self.enemys = Enemy((300,300))
        self.make_enemy(filename)

        # マップをロードしてマップ内スプライトの作成
        self.load(filename)

        # マップサーフェイスを作成
        self.surface = pygame.Surface((self.col*self.GS, self.row*self.GS)).convert()

    def draw(self):
        """マップサーフェイスにマップ内スプライトを描画"""
        self.surface.fill((0,0,0))
        self.all.draw(self.surface)

    def update(self):
        """マップ内スプライトを更新"""
        self.all.update()

    def calc_offset(self):
        """オフセットを計算"""
        offsetx = self.kokaton.rect.topleft[0] - SCR_RECT.width/2
        offsety = self.kokaton.rect.topleft[1] - SCR_RECT.height/2
        return offsetx, offsety

    def load(self, filename):
        """マップをロードしてスプライトを作成"""
        map = []
        fp = open(filename, "r")
        for line in fp:
            line = line.rstrip()  # 改行除去
            map.append(list(line))
            self.row = len(map)
            self.col = len(map[0])
        self.width = self.col * self.GS
        self.height = self.row * self.GS
        fp.close()

        # マップからスプライトを作成
        for i in range(self.row):
            for j in range(self.col):
                if map[i][j] == 'B':
                    Block((j*self.GS, i*self.GS))  # ブロック

    def make_enemy(self, filename):
        """マップをロードしてスプライトを作成"""
        map = []
        fp = open(filename, "r")
        for line in fp:
            line = line.rstrip()  # 改行除去
            map.append(list(line))
            self.row = len(map)
            self.col = len(map[0])
        self.width = self.col * self.GS
        self.height = self.row * self.GS
        fp.close()

        # マップからスプライトを作成
        for i in range(self.row):
            for j in range(self.col):
                if map[i][j] == 'E':
                    Enemy((j*self.GS, i*self.GS+20), self.shots)  # 敵
                    
                    
def load_image(filename, colorkey=None):
    """画像をロードして画像と矩形を返す"""
    filename = os.path.join("data", filename)
    try:
        image = pygame.image.load(filename)
    except pygame.error as message:
        print("Cannot load image:", filename)
        raise SystemExit(message)
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image


def game_end(surface, life, screen):
    font = pygame.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 70)
    bg = surface
    pygame.draw.rect(bg,(0, 0, 0), (0, 0, 1600, 900))
    bg.set_alpha(128)
    screen.blit(bg, (0,0))
    if life <= 0:
        img = load_image("game_over.png")
        img = pygame.transform.rotozoom(img, 0, 2.0)
        str = font.render(f"Game Over", 0, (255, 0, 0))

    screen.blit(img, (250, 240))
    screen.blit(str, (150, 50))
    pygame.display.update()
    time.sleep(3)

       
class Kokaton_Game:
    def __init__(self):
        pygame.init()
        screen = pygame.display.set_mode(SCR_RECT.size)
        pygame.display.set_caption("マップスクロール")

        # 画像のロード
        Kokaton.left_image = load_image("kokaton.png")
        Kokaton.right_image = pygame.transform.flip(Kokaton.left_image, 1, 0)  # 左向き
        Kokaton.down_image = pygame.transform.flip(Kokaton.right_image, 0, 1)  # 下向き
        Block.image = load_image("block.png", -1)
        Shot.image = load_image("fireball.png")    # add
        Enemy.image = load_image("enemy.png", -1) # add               # 左向き
        
        # マップのロード
        self.map = Map("data/test2.map")
        self.klife = Kokaton_Life(self.map.kokaton.life)

        # メインループ
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            self.draw(screen)
            self.update(screen)
            pygame.display.update()
            self.key_handler()
            #print(self.map.kokaton.life)
            # print(self.map.kokaton.coltm)
            if self.map.kokaton.life <= 0:
                game_end(self.map.surface, self.map.kokaton.life, screen)
                return

    def update(self, screen):
        self.klife.update(self.map.kokaton.life, screen)
        self.map.update()

    def draw(self, screen):
        self.map.draw()

        # オフセッとに基づいてマップの一部を画面に描画
        offsetx, offsety = self.map.calc_offset()

        # 端ではスクロールしない
        if offsetx < 0:
            offsetx = 0
        elif offsetx > self.map.width - SCR_RECT.width:
            offsetx = self.map.width - SCR_RECT.width

        if offsety < 0:
            offsety = 0
        elif offsety > self.map.height - SCR_RECT.height:
            offsety = self.map.height - SCR_RECT.height

        # マップの一部を画面に描画
        screen.blit(self.map.surface, (0,0), (offsetx, offsety, SCR_RECT.width, SCR_RECT.height))

    def key_handler(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
                
SCR_RECT = Rect(0, 0, 640, 480)
Kokaton_Game()                
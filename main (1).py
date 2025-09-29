import pygame
import os
import random
from pygame.locals import *

pygame.init()
pygame.mixer.init()

# --- Configuração da tela ---
LARGURA_TELA, ALTURA_TELA = 771, 384
screen = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Car Rampage")

# --- Diretório base ---
BASE_DIR = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()

# --- Trilha sonora ---
caminho_musica_inicial = os.path.join(BASE_DIR, "audio", "Top Gear Soundtrack - Title.mp3")
caminho_musica_jogo = os.path.join(BASE_DIR, "audio", "Top Gear Soundtrack - Track 4.mp3")

def tocar_musica(caminho, volume=0.5):
    if os.path.exists(caminho):
        pygame.mixer.music.stop()
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)
    else:
        print(f"[AVISO] música não encontrada: {caminho}")

tocar_musica(caminho_musica_inicial)

# --- Helper para carregar imagens ---
def safe_load_image(path, fallback_size=(100,100)):
    if os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    else:
        print(f"[AVISO] arquivo não encontrado: {path}")
        s = pygame.Surface(fallback_size, pygame.SRCALPHA)
        s.fill((150,150,150,255))
        return s

# --- Sprite sheet do cenário ---
caminho_sprite_cenario = os.path.join(BASE_DIR, "img", "cenario_sprite-sheet.png")
sprite_sheet = safe_load_image(caminho_sprite_cenario, fallback_size=(LARGURA_TELA, ALTURA_TELA))

FRAME_WIDTH = LARGURA_TELA
FRAME_HEIGHT = ALTURA_TELA

frames_cenario = []
sheet_w, sheet_h = sprite_sheet.get_width(), sprite_sheet.get_height()
cols = max(1, sheet_w // FRAME_WIDTH)
rows = max(1, sheet_h // FRAME_HEIGHT)

if sheet_w < FRAME_WIDTH or sheet_h < FRAME_HEIGHT:
    frames_cenario = [pygame.transform.scale(sprite_sheet, (LARGURA_TELA, ALTURA_TELA))]
else:
    for r in range(rows):
        for c in range(cols):
            rect = (c * FRAME_WIDTH, r * FRAME_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT)
            frame = sprite_sheet.subsurface(rect).copy()
            frames_cenario.append(pygame.transform.scale(frame, (LARGURA_TELA, ALTURA_TELA)))

NUM_FRAMES = len(frames_cenario)

# --- Carro ---
caminho_carro = os.path.join(BASE_DIR, "img", "carro3.png")
img_carro = safe_load_image(caminho_carro, fallback_size=(64, 32))
x_carro_inicial = 300
y_carro = ALTURA_TELA - img_carro.get_height() - 20
rect_carro = img_carro.get_rect(topleft=(x_carro_inicial, y_carro))

# --- Obstáculo ---
LANES = [335, 365, 400]
Y_START = 65

# --- Velocidade extra global para dificuldade ---
velocidade_extra = 0

class Obstaculo:
    def __init__(self, img, lane):
        self.img_base = img
        self.y = Y_START
        self.lane = lane
        self.scale_x = 20
        self.scale_y = 20
        self.speed = 4
        if lane == LANES[1]:
            self.dx = 0
            self.dy = self.speed
        elif lane == LANES[0]:
            self.dx = -5
            self.dy = self.speed
        else:
            self.dx = 5
            self.dy = self.speed
        self.img = pygame.transform.scale(self.img_base, (int(self.scale_x), int(self.scale_y)))
        # Hitbox inicial
        self.rect = pygame.Rect(0,0,int(self.scale_x*0.6), int(self.scale_y*0.2))
        self.rect.midtop = (self.lane, self.y + self.scale_y * 1.0)
        
    def update(self):
        self.y += self.dy + velocidade_extra
        self.lane += self.dx
        self.scale_x += 2.5
        self.scale_y += 2.0
        self.img = pygame.transform.scale(self.img_base, (int(self.scale_x), int(self.scale_y)))
        # Hitbox ajustado para a base d o obstaculo
        self.rect.width = int(self.scale_x * 1.0)
        self.rect.height = int(self.scale_y * 0.28)
        self.rect.midtop = (self.lane, self.y + self.scale_y * 0.5)

    def draw(self, surface, mostrar_hitbox=False):
        surface.blit(self.img, (self.rect.left, self.rect.top - int(self.scale_y * 0.8)))
        if mostrar_hitbox:
            pygame.draw.rect(surface, (255,0,0), self.rect, 1)

caminho_obs = os.path.join(BASE_DIR, "img", "cone3.png")
img_obs = safe_load_image(caminho_obs, fallback_size=(50, 50))
obstaculos = []

TEMPO_ROCHA = 950
ultimo_spawn = 0

# --- Tela inicial ---
caminho_tela_inicial = os.path.join(BASE_DIR, "img", "Tela_inicial.png")
img_tela_inicial = safe_load_image(caminho_tela_inicial, fallback_size=(600,250))
img_tela_inicial = pygame.transform.scale(img_tela_inicial, (600,250))

# --- Fonte ---
caminho_fonte = os.path.join(BASE_DIR, "fontes", "VCR_OSD_MONO_1.001.ttf")
try:
    fonte_pixel = pygame.font.Font(caminho_fonte, 20)
except:
    fonte_pixel = pygame.font.SysFont(None, 20)

texto_inicial = fonte_pixel.render('APERTE "ESPAÇO" PARA JOGAR', True, (0,0,0))

controles = [
    "CONTROLES:",
    " ’   MOVER CARRO",
    "P ’ PAUSAR/DESPAUSAR",
    "R ’ REINICIAR",
    "ESPAÇO ’ AVANÇAR",
    "H ’ Mostrar hitboxes"
]
texto_controles = [fonte_pixel.render(linha, True, (0,0,0)) for linha in controles]

# --- Estados ---
tela_inicial = True
tela_controles = False
jogo_iniciado = False
paused = False
game_over = False
vitoria = False
mostrar_hitbox = False

# --- Animação ---
frame_atual = 0
contador_animacao = 0.0
velocidade_animacao = 0.25

# --- Pontuação ---
pontuacao = 0
ultimo_ponto = 0
pontuacao_final = 0

# --- Controle FPS ---
relogio = pygame.time.Clock()
fps = 60

# --- Loop principal ---
while True:
    agora = pygame.time.get_ticks()
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            exit()
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_SPACE:
                if tela_inicial:
                    tela_inicial = False
                    tela_controles = True
                elif tela_controles:
                    tela_controles = False
                    jogo_iniciado = True
                    paused = False
                    game_over = False
                    vitoria = False
                    obstaculos.clear()
                    ultimo_spawn = agora
                    pontuacao = 0
                    ultimo_ponto = agora
                    tocar_musica(caminho_musica_jogo)

            elif evento.key == pygame.K_p and jogo_iniciado:
                paused = not paused

            elif evento.key == pygame.K_r:
                game_over = False
                vitoria = False
                tela_inicial = True
                jogo_iniciado = False
                paused = False
                pontuacao = 0
                obstaculos.clear()
                ultimo_spawn = agora
                tocar_musica(caminho_musica_inicial)

            elif evento.key == pygame.K_h:
                mostrar_hitbox = not mostrar_hitbox

    # --- Atualizações ---
    if jogo_iniciado and not paused and not game_over and not vitoria:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            rect_carro.x -= 10
            rect_carro.left = max(rect_carro.left, 0)
        if keys[pygame.K_RIGHT]:
            rect_carro.x += 10
            rect_carro.right = min(rect_carro.right, LARGURA_TELA)

        if NUM_FRAMES > 0:
            contador_animacao += velocidade_animacao
            if contador_animacao >= 1:
                contador_animacao -= 1
                frame_atual = (frame_atual + 1) % NUM_FRAMES

        if agora - ultimo_ponto >= 1000:
            pontuacao += 1
            ultimo_ponto = agora

        if pontuacao >= 80:
            velocidade_extra = 1.86
        elif pontuacao >= 50:
            velocidade_extra = 1.3
        elif pontuacao >= 20:
            velocidade_extra = 1
        else:
            velocidade_extra = 0

        if agora - ultimo_spawn >= TEMPO_ROCHA:
            lane = random.choice(LANES)
            obstaculos.append(Obstaculo(img_obs, lane))
            ultimo_spawn = agora

        for o in obstaculos[:]:
            o.update()
            if rect_carro.colliderect(o.rect):
                game_over = True
                jogo_iniciado = False
                pontuacao_final = pontuacao
                tocar_musica(caminho_musica_inicial)
            if o.y - o.scale_y > ALTURA_TELA or o.lane + o.scale_x < 0 or o.lane - o.scale_x > LARGURA_TELA:
                obstaculos.remove(o)

        if pontuacao >= 100:
            vitoria = True
            jogo_iniciado = False
            tocar_musica(caminho_musica_inicial)

    if jogo_iniciado:
        if paused:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()

    # --- Desenho ---
    screen.fill((200,200,255))

    if tela_inicial:
        screen.blit(img_tela_inicial, ((LARGURA_TELA - img_tela_inicial.get_width())//2, (ALTURA_TELA - img_tela_inicial.get_height())//2))
        screen.blit(texto_inicial, ((LARGURA_TELA - texto_inicial.get_width())//2, (ALTURA_TELA + img_tela_inicial.get_height())//2))
    elif tela_controles:
        y_offset = 60
        for linha in texto_controles:
            x_linha = (LARGURA_TELA - linha.get_width()) // 2
            screen.blit(linha, (x_linha, y_offset))
            y_offset += linha.get_height() + 12
    elif game_over:
        screen.fill((0,0,0))
        texto_go = fonte_pixel.render("GAME OVER", True, (255,0,0))
        texto_pts = fonte_pixel.render(f"Sua pontuação final: {pontuacao_final}", True, (255,255,255))
        texto_restart = fonte_pixel.render("Pressione R para reiniciar", True, (200,200,200))
        screen.blit(texto_go, ((LARGURA_TELA - texto_go.get_width())//2, ALTURA_TELA//2 - 60))
        screen.blit(texto_pts, ((LARGURA_TELA - texto_pts.get_width())//2, ALTURA_TELA//2 - 10))
        screen.blit(texto_restart, ((LARGURA_TELA - texto_restart.get_width())//2, ALTURA_TELA//2 + 40))
    elif vitoria:
        screen.fill((0, 100, 0))
        texto_vitoria = fonte_pixel.render("VOCÊ VENCEU!", True, (255, 255, 0))
        texto_pts = fonte_pixel.render(f"Sua pontuação: {pontuacao}", True, (255, 255, 255))
        texto_restart = fonte_pixel.render("Pressione R para reiniciar", True, (200,200,200))
        screen.blit(texto_vitoria, ((LARGURA_TELA - texto_vitoria.get_width())//2, ALTURA_TELA//2 - 60))
        screen.blit(texto_pts, ((LARGURA_TELA - texto_pts.get_width())//2, ALTURA_TELA//2 - 10))
        screen.blit(texto_restart, ((LARGURA_TELA - texto_restart.get_width())//2, ALTURA_TELA//2 + 40))
    elif jogo_iniciado:
        if NUM_FRAMES > 0:
            screen.blit(frames_cenario[frame_atual], (0,0))
        for o in obstaculos:
            o.draw(screen, mostrar_hitbox)
        screen.blit(img_carro, rect_carro)
        txt_pontos = fonte_pixel.render(f"Pontos: {pontuacao}", True, (0,0,0))
        screen.blit(txt_pontos, (10,10))
        if paused:
            txt = fonte_pixel.render("PAUSADO - pressione P para continuar", True, (255,0,0))
            screen.blit(txt, ((LARGURA_TELA - txt.get_width())//2, 10))

    pygame.display.flip()
    relogio.tick(fps)

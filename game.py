import pygame 
import sys
import random
import math
from pygame.locals import *

# Inicializar Pygame
pygame.init()

# Configuración de la pantalla
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Outlast Python")

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)

# Cámara/Jugador
class Player:
    def __init__(self):
        self.x = 100
        self.y = 100
        self.width = 30  # Ajustado para que coincida mejor con una imagen típica
        self.height = 40  # Ajustado para que coincida mejor con una imagen típica
        self.speed = 3
        self.has_camera = True
        self.camera_battery = 100
        self.camera_on = False
        self.stamina = 100
        self.max_stamina = 100
        self.is_running = False
        self.is_hidden = False
        self.hiding_spot = None
        self.night_vision = False
        
        # Cargar la imagen del jugador
        try:
            self.image = pygame.image.load('player.png')  # Asegúrate de tener este archivo en el mismo directorio
            # Redimensionar la imagen para que coincida con el tamaño del jugador
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        except:
            # Si no se puede cargar la imagen, usar un color predeterminado
            self.image = None
            print("No se pudo cargar la imagen del jugador. Usando rectángulo por defecto.")

    def move(self, keys, walls, hiding_spots):
        dx, dy = 0, 0
        speed = self.speed * 1.5 if self.is_running else self.speed
        
        # Permitir salir del escondite
        if self.is_hidden and keys[K_e]:
            self.is_hidden = False
            self.hiding_spot = None
            return
            
        if self.is_hidden:
            return
            
        if keys[K_w]:
            dy = -speed
        if keys[K_s]:
            dy = speed
        if keys[K_a]:
            dx = -speed
        if keys[K_d]:
            dx = speed
            
        # Sprint
        if keys[K_LSHIFT] and self.stamina > 0:
            self.is_running = True
            self.stamina -= 0.5
        else:
            self.is_running = False
            if self.stamina < self.max_stamina:
                self.stamina += 0.1
                
        # Verificar colisiones con paredes
        new_x = self.x + dx
        new_y = self.y + dy
        
        player_rect = pygame.Rect(new_x, new_y, self.width, self.height)
        
        can_move_x = True
        can_move_y = True
        
        for wall in walls:
            wall_rect = pygame.Rect(wall[0], wall[1], wall[2], wall[3])
            if pygame.Rect(new_x, self.y, self.width, self.height).colliderect(wall_rect):
                can_move_x = False
            if pygame.Rect(self.x, new_y, self.width, self.height).colliderect(wall_rect):
                can_move_y = False
                
        if can_move_x:
            self.x = new_x
        if can_move_y:
            self.y = new_y
            
        # Verificar escondite
        if not self.is_hidden:  # Solo verificar si no está ya escondido
            for spot in hiding_spots:
                spot_rect = pygame.Rect(spot[0], spot[1], spot[2], spot[3])
                if player_rect.colliderect(spot_rect) and keys[K_e]:
                    self.is_hidden = True
                    self.hiding_spot = spot
                    break
                
    def toggle_camera(self):
        if self.has_camera and self.camera_battery > 0:
            self.camera_on = not self.camera_on
            if self.camera_on:
                self.night_vision = True
            else:
                self.night_vision = False
                
    def update_camera(self):
        if self.camera_on and self.camera_battery > 0:
            self.camera_battery -= 0.05
            if self.camera_battery <= 0:
                self.camera_on = False
                self.night_vision = False
                
    def draw(self, screen):
        if not self.is_hidden:
            if self.image is not None:
                screen.blit(self.image, (self.x, self.y))
            else:
                # Dibujar un rectángulo si no hay imagen
                pygame.draw.rect(screen, GREEN, (self.x, self.y, self.width, self.height))
        
    def draw_ui(self, screen):
        # Batería
        battery_width = 100
        pygame.draw.rect(screen, GRAY, (20, 20, battery_width, 20))
        pygame.draw.rect(screen, GREEN, (20, 20, battery_width * (self.camera_battery / 100), 20))
        
        # Estamina
        stamina_width = 100
        pygame.draw.rect(screen, GRAY, (20, 50, stamina_width, 20))
        pygame.draw.rect(screen, GREEN, (20, 50, stamina_width * (self.stamina / 100), 20))
        
        # Indicador de cámara
        if self.camera_on:
            font = pygame.font.SysFont(None, 24)
            text = font.render("REC", True, RED)
            screen.blit(text, (130, 20))
            
        # Indicador de escondite
        if self.is_hidden:
            font = pygame.font.SysFont(None, 24)
            text = font.render("ESCONDIDO", True, WHITE)
            screen.blit(text, (WIDTH // 2 - 50, 20))

# Enemigo
class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.speed = 1.5
        self.patrol_points = [(x, y), (x + 200, y), (x + 200, y + 200), (x, y + 200)]
        self.current_point = 0
        self.is_chasing = False
        self.detection_range = 150
        self.chase_timer = 0
        self.direction = 0  # Ángulo en radianes
        
        # También se podría cargar una imagen para el enemigo si se desea
        try:
            self.image = pygame.image.load('enemy.png')
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        except:
            self.image = None
        
    def update(self, player, walls):
        # Comprobar si puede ver al jugador
        if not player.is_hidden:
            dx = player.x - self.x
            dy = player.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Detectar al jugador si está cerca
            if distance < self.detection_range:
                # Comprobar si hay paredes entre el enemigo y el jugador
                can_see_player = True
                for wall in walls:
                    wall_rect = pygame.Rect(wall[0], wall[1], wall[2], wall[3])
                    if line_intersects_rect((self.x + self.width/2, self.y + self.height/2), 
                                           (player.x + player.width/2, player.y + player.height/2), wall_rect):
                        can_see_player = False
                        break
                
                if can_see_player:
                    self.is_chasing = True
                    self.chase_timer = 180  # 3 segundos a 60 fps
                    # Calcular dirección hacia el jugador
                    self.direction = math.atan2(dy, dx)
            
        # Si está persiguiendo al jugador
        if self.is_chasing:
            self.chase_timer -= 1
            if self.chase_timer <= 0 and not player.is_hidden:
                # Verificar nuevamente si puede ver al jugador
                dx = player.x - self.x
                dy = player.y - self.y
                distance = math.sqrt(dx*dx + dy*dy)
                if distance < self.detection_range:
                    self.chase_timer = 180
                else:
                    self.is_chasing = False
            
            # Moverse hacia el jugador
            speed = self.speed
            move_x = math.cos(self.direction) * speed
            move_y = math.sin(self.direction) * speed
            
            # Verificar colisiones con paredes
            new_x = self.x + move_x
            new_y = self.y + move_y
            
            enemy_rect = pygame.Rect(new_x, new_y, self.width, self.height)
            can_move = True
            
            for wall in walls:
                wall_rect = pygame.Rect(wall[0], wall[1], wall[2], wall[3])
                if enemy_rect.colliderect(wall_rect):
                    can_move = False
                    break
                    
            if can_move:
                self.x = new_x
                self.y = new_y
        else:
            # Patrullar
            target_x, target_y = self.patrol_points[self.current_point]
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 5:
                self.current_point = (self.current_point + 1) % len(self.patrol_points)
            else:
                self.direction = math.atan2(dy, dx)
                self.x += math.cos(self.direction) * (self.speed * 0.7)
                self.y += math.sin(self.direction) * (self.speed * 0.7)
    
    def draw(self, screen, night_vision):
        if self.image is not None:
            screen.blit(self.image, (self.x, self.y))
        else:
            color = RED if night_vision else (150, 0, 0)
            pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        
    def check_caught_player(self, player):
        if player.is_hidden:
            return False
            
        player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
        enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        return player_rect.colliderect(enemy_rect)

# Funciones auxiliares
def line_intersects_rect(p1, p2, rect):
    """Comprueba si una línea intersecta con un rectángulo"""
    # Comprueba las cuatro aristas del rectángulo
    r_left = rect.left
    r_right = rect.right
    r_top = rect.top
    r_bottom = rect.bottom
    
    return (line_intersects_line(p1, p2, (r_left, r_top), (r_right, r_top)) or
            line_intersects_line(p1, p2, (r_right, r_top), (r_right, r_bottom)) or
            line_intersects_line(p1, p2, (r_right, r_bottom), (r_left, r_bottom)) or
            line_intersects_line(p1, p2, (r_left, r_bottom), (r_left, r_top)))

def line_intersects_line(p1, p2, p3, p4):
    """Comprueba si dos líneas se intersectan"""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    
    # Cálculo de determinantes
    den = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if den == 0:
        return False
        
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / den
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / den
    
    return ua >= 0 and ua <= 1 and ub >= 0 and ub <= 1

def create_map():
    walls = [
        # Bordes exteriores
        (0, 0, WIDTH, 20),
        (0, 0, 20, HEIGHT),
        (0, HEIGHT - 20, WIDTH, 20),
        (WIDTH - 20, 0, 20, HEIGHT),
        
        # Paredes interiores
        (100, 100, 200, 20),
        (100, 100, 20, 200),
        (300, 200, 20, 200),
        (300, 200, 200, 20),
        (500, 300, 20, 200),
        (500, 300, 200, 20),
        (200, 400, 200, 20),
    ]
    
    hiding_spots = [
        (150, 150, 40, 40),
        (500, 100, 40, 40),
        (700, 500, 40, 40),
        (100, 500, 40, 40),
    ]
    
    # Elementos de colección (documentos)
    documents = [
        (200, 200),
        (600, 400),
        (400, 500),
    ]
    
    # Baterías para la cámara
    batteries = [
        (300, 100),
        (700, 300),
        (100, 400),
    ]
    
    return walls, hiding_spots, documents, batteries

def draw_map(screen, walls, hiding_spots, documents, batteries, night_vision, collected_docs, collected_batteries):
    # Dibujar paredes
    for wall in walls:
        pygame.draw.rect(screen, WHITE if night_vision else GRAY, wall)
    
    # Dibujar escondites
    for spot in hiding_spots:
        pygame.draw.rect(screen, (0, 0, 150) if night_vision else (0, 0, 100), spot)
    
    # Dibujar documentos
    for i, doc in enumerate(documents):
        if i not in collected_docs:
            pygame.draw.rect(screen, (200, 200, 0) if night_vision else (100, 100, 0), (doc[0], doc[1], 15, 15))
    
    # Dibujar baterías
    for i, battery in enumerate(batteries):
        if i not in collected_batteries:
            pygame.draw.rect(screen, (0, 200, 200) if night_vision else (0, 100, 100), (battery[0], battery[1], 10, 15))

def game_over_screen():
    screen.fill(BLACK)
    font = pygame.font.SysFont(None, 48)
    text = font.render("GAME OVER", True, RED)
    screen.blit(text, (WIDTH//2 - 100, HEIGHT//2 - 24))
    
    font = pygame.font.SysFont(None, 24)
    text = font.render("Presiona R para reiniciar o ESC para salir", True, WHITE)
    screen.blit(text, (WIDTH//2 - 180, HEIGHT//2 + 30))
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_r:
                    return True
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
    
def win_screen():
    screen.fill(BLACK)
    font = pygame.font.SysFont(None, 48)
    text = font.render("¡HAS ESCAPADO!", True, GREEN)
    screen.blit(text, (WIDTH//2 - 150, HEIGHT//2 - 24))
    
    font = pygame.font.SysFont(None, 24)
    text = font.render("Presiona R para jugar de nuevo o ESC para salir", True, WHITE)
    screen.blit(text, (WIDTH//2 - 200, HEIGHT//2 + 30))
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_r:
                    return True
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

# Función para crear una imagen de jugador predeterminada si no se encuentra 'player.png'
def create_default_player_image():
    image = pygame.Surface((30, 40), pygame.SRCALPHA)
    # Dibujar un personaje simple (tipo muñeco de palo)
    pygame.draw.circle(image, (100, 200, 100), (15, 10), 8)  # Cabeza
    pygame.draw.line(image, (100, 200, 100), (15, 18), (15, 30), 3)  # Cuerpo
    pygame.draw.line(image, (100, 200, 100), (15, 20), (5, 28), 2)  # Brazo izquierdo
    pygame.draw.line(image, (100, 200, 100), (15, 20), (25, 28), 2)  # Brazo derecho
    pygame.draw.line(image, (100, 200, 100), (15, 30), (8, 39), 2)  # Pierna izquierda
    pygame.draw.line(image, (100, 200, 100), (15, 30), (22, 39), 2)  # Pierna derecha
    return image

def main():
    clock = pygame.time.Clock()
    running = True
    game_active = True
    
    # Crear mapa
    walls, hiding_spots, documents, batteries = create_map()
    
    # Crear jugador
    player = Player()
    
    # Verificar si se pudo cargar la imagen del jugador
    if player.image is None:
        # Crear una imagen de jugador predeterminada
        player.image = create_default_player_image()
    
    # Crear enemigo
    enemies = [Enemy(500, 500), Enemy(300, 300)]
    
    # Documentos y baterías recogidas
    collected_docs = set()
    collected_batteries = set()
    
    # Puerta de salida
    exit_door = (750, 50, 30, 50)
    
    # Loop principal del juego
    while running:
        # Manejo de eventos
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                if event.key == K_f:
                    player.toggle_camera()
            
        if game_active:
            # Actualizar posición del jugador
            keys = pygame.key.get_pressed()
            player.move(keys, walls, hiding_spots)
            player.update_camera()
            
            # Actualizar enemigos
            for enemy in enemies:
                enemy.update(player, walls)
                if enemy.check_caught_player(player):
                    game_active = False
                    if game_over_screen():
                        # Reiniciar el juego
                        return main()
            
            # Comprobar si el jugador recoge documentos
            player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
            for i, doc in enumerate(documents):
                if i not in collected_docs:
                    doc_rect = pygame.Rect(doc[0], doc[1], 15, 15)
                    if player_rect.colliderect(doc_rect):
                        collected_docs.add(i)
            
            # Comprobar si el jugador recoge baterías
            for i, battery in enumerate(batteries):
                if i not in collected_batteries:
                    battery_rect = pygame.Rect(battery[0], battery[1], 10, 15)
                    if player_rect.colliderect(battery_rect):
                        collected_batteries.add(i)
                        player.camera_battery = min(100, player.camera_battery + 30)
            
            # Comprobar si el jugador ha recogido todos los documentos y llegado a la salida
            exit_rect = pygame.Rect(exit_door)
            if len(collected_docs) == len(documents) and player_rect.colliderect(exit_rect):
                if win_screen():
                    # Reiniciar el juego
                    return main()
            
            # Dibujar todo
            screen.fill(BLACK)
            
            # Efecto de oscuridad/noche
            if player.night_vision:
                draw_map(screen, walls, hiding_spots, documents, batteries, True, collected_docs, collected_batteries)
                for enemy in enemies:
                    enemy.draw(screen, True)
                player.draw(screen)
                
                # Dibujar salida
                pygame.draw.rect(screen, (0, 150, 0), exit_door)
                
                # Borde de cámara
                pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, 30))
                pygame.draw.rect(screen, BLACK, (0, 0, 30, HEIGHT))
                pygame.draw.rect(screen, BLACK, (0, HEIGHT-30, WIDTH, 30))
                pygame.draw.rect(screen, BLACK, (WIDTH-30, 0, 30, HEIGHT))
                
                # HUD de la cámara
                pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, 3))
                pygame.draw.rect(screen, BLACK, (0, HEIGHT-3, WIDTH, 3))
                pygame.draw.rect(screen, BLACK, (0, 0, 3, HEIGHT))
                pygame.draw.rect(screen, BLACK, (WIDTH-3, 0, 3, HEIGHT))
                
                # Contador de documentos
                font = pygame.font.SysFont(None, 24)
                text = font.render(f"Documentos: {len(collected_docs)}/{len(documents)}", True, WHITE)
                screen.blit(text, (WIDTH - 200, 20))
            else:
                # Simular visión limitada en la oscuridad
                visible_radius = 100
                
                # Primero dibuja todo en negro
                screen.fill(BLACK)
                
                # Luego dibuja el área visible alrededor del jugador
                surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                surf.fill((0, 0, 0, 200))  # Oscuridad semitransparente
                
                # Crea un círculo de visibilidad
                pygame.draw.circle(surf, (0, 0, 0, 0), (int(player.x + player.width/2), int(player.y + player.height/2)), visible_radius)
                
                # Dibuja el mapa en una superficie temporal
                temp_surf = pygame.Surface((WIDTH, HEIGHT))
                temp_surf.fill(BLACK)
                draw_map(temp_surf, walls, hiding_spots, documents, batteries, False, collected_docs, collected_batteries)
                for enemy in enemies:
                    enemy.draw(temp_surf, False)
                player.draw(temp_surf)
                
                # Dibujar salida
                pygame.draw.rect(temp_surf, (0, 80, 0), exit_door)
                
                # Aplica la superficie de oscuridad
                screen.blit(temp_surf, (0, 0))
                screen.blit(surf, (0, 0))
                
                # Contador de documentos
                font = pygame.font.SysFont(None, 24)
                text = font.render(f"Documentos: {len(collected_docs)}/{len(documents)}", True, WHITE)
                screen.blit(text, (WIDTH - 200, 20))
            
            # Dibujar UI
            player.draw_ui(screen)
            
            # Instrucciones
            font = pygame.font.SysFont(None, 20)
            if player.is_hidden:
                text = font.render("Presiona E para salir del escondite", True, WHITE)
                screen.blit(text, (WIDTH//2 - 120, HEIGHT - 50))
            else:
                # Verificar si hay un escondite cercano
                player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
                for spot in hiding_spots:
                    spot_rect = pygame.Rect(spot[0], spot[1], spot[2], spot[3])
                    if player_rect.colliderect(spot_rect):
                        text = font.render("Presiona E para esconderte", True, WHITE)
                        screen.blit(text, (WIDTH//2 - 120, HEIGHT - 50))
                        break
            
            pygame.display.flip()
            
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()


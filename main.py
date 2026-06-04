import pygame
import sys
import os
from car import Car, WIDTH, HEIGHT
from track_config import TRACK_CONFIG

# === Setup ===
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 20)
pygame.display.set_caption("Manual Car Test")

# === Track ===
TRACK_NAME = "silverstone_clean.png"
TRACK_PATH = os.path.join("tracks", TRACK_NAME)

try:
    track = pygame.image.load(TRACK_PATH).convert()
except FileNotFoundError:
    sys.exit(f"Track not found at {TRACK_PATH}")

track = pygame.transform.scale(track, (WIDTH, HEIGHT))

# === Spawn — use track_config if available, else centre ===
cfg = TRACK_CONFIG.get(TRACK_NAME)
if cfg and "spawn" in cfg:
    sp = cfg["spawn"]
    start_x, start_y, start_angle = sp["x"], sp["y"], sp["angle"]
    print(f"Spawning from track_config: ({start_x}, {start_y}) angle={start_angle}")
else:
    start_x, start_y, start_angle = WIDTH // 2, HEIGHT // 2, 0
    print("No spawn config found for this track — using centre. Run track_selector.py to set one.")

car = Car(start_x, start_y, angle=start_angle)

# === Main loop ===
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # R = respawn
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            car = Car(start_x, start_y, angle=start_angle)

    keys = pygame.key.get_pressed()

    if car.alive:
        if keys[pygame.K_LEFT]:
            car.steer_left()
        if keys[pygame.K_RIGHT]:
            car.steer_right()
        if keys[pygame.K_UP]:
            car.accelerate()
        else:
            car.brake()

    car.update(track)

    screen.blit(track, (0, 0))
    car.draw(screen, draw_sensors=True)

    status = f"Speed: {car.speed:.2f} | Alive: {car.alive}"
    if not car.alive:
        status += "  (press R to respawn)"
    info = font.render(status, True, (255, 255, 255))
    screen.blit(info, (20, 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()

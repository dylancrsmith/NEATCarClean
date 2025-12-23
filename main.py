import pygame
import sys
from car import Car, WIDTH, HEIGHT

# === Setup ===
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("Manual Car Test")

# === Load Track ===
TRACK_PATH = "tracks/silverstone_clean.png"

try:
    track = pygame.image.load(TRACK_PATH).convert()
except FileNotFoundError:
    sys.exit(f"❌ Track not found at {TRACK_PATH}")

track = pygame.transform.scale(track, (WIDTH, HEIGHT))

# === Spawn Car ===
# Pick a safe area. You can overwrite this once you know your spawn.
start_x = WIDTH // 2
start_y = HEIGHT // 2

car = Car(start_x, start_y, angle=0)

# === Main loop ===
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # movement controls
    if keys[pygame.K_LEFT]:
        car.steer_left()

    if keys[pygame.K_RIGHT]:
        car.steer_right()

    if keys[pygame.K_UP]:
        car.accelerate()
    else:
        # natural deceleration when not pressing UP
        car.brake()

    # update
    car.update(track)

    # draw
    screen.blit(track, (0, 0))
    car.draw(screen, draw_sensors=True)

    # display info text
    font = pygame.font.SysFont("consolas", 20)
    info = font.render(f"Speed: {car.speed:.2f} | Alive: {car.alive}", True, (255,255,255))
    screen.blit(info, (20, 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()

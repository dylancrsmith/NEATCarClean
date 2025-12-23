import pygame
import sys
import math
import os

from car import WIDTH, HEIGHT

pygame.init()


TRACKS_DIR = "tracks"
SPAWN_CONFIG_PATH = "spawn_config.py"
FONT = pygame.font.SysFont("consolas", 28)


# ============================================================
#         TRACK SELECTION MENU
# ============================================================
def select_track_menu():
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("Select Track")

    # load all cleaned tracks
    clean_tracks = [f for f in os.listdir(TRACKS_DIR) if f.endswith("_clean.png")]

    if not clean_tracks:
        print("❌ No cleaned tracks found.")
        sys.exit()

    running = True
    while running:
        screen.fill((20, 20, 20))

        title = FONT.render("Select a Track (Press Number):", True, (255, 255, 255))
        screen.blit(title, (40, 20))

        # display tracks with numbers
        for i, t in enumerate(clean_tracks):
            entry = FONT.render(f"{i+1}. {t}", True, (200, 200, 0))
            screen.blit(entry, (40, 80 + i * 40))

        pygame.display.update()

        # keypress detection
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                key = event.key - pygame.K_1
                if 0 <= key < len(clean_tracks):
                    pygame.display.quit()
                    return clean_tracks[key]


# ============================================================
#         SAVE SPAWN
# ============================================================
def save_spawn(track_name, pos, angle):
    x, y = pos

    if not os.path.exists(SPAWN_CONFIG_PATH):
        with open(SPAWN_CONFIG_PATH, "w") as f:
            f.write("SPAWN_POINTS = {}\n")

    namespace = {}
    with open(SPAWN_CONFIG_PATH, "r") as f:
        exec(f.read(), namespace)

    spawns = namespace.get("SPAWN_POINTS", {})

    spawns[track_name] = {"x": x, "y": y, "angle": angle}

    with open(SPAWN_CONFIG_PATH, "w") as f:
        f.write("SPAWN_POINTS = " + repr(spawns) + "\n")

    print(f"💾 Saved spawn for {track_name}: pos={pos}, angle={angle}")


# ============================================================
#         SPAWN SELECTOR
# ============================================================
def run_spawn_selector(track_name):
    pygame.display.set_caption(f"Spawn Selector — {track_name}")

    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    track_path = os.path.join(TRACKS_DIR, track_name)
    track_img = pygame.image.load(track_path).convert()
    track_img = pygame.transform.scale(track_img, (WIDTH, HEIGHT))

    font = pygame.font.SysFont("consolas", 22)

    spawn_pos = None
    spawn_angle = 0

    running = True
    while running:
        screen.blit(track_img, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # left click = set position
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                spawn_pos = event.pos
                print(f"📍 Position set: {spawn_pos}")

            # rotate Q/E
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    spawn_angle += 5
                elif event.key == pygame.K_e:
                    spawn_angle -= 5

                # ENTER = save
                elif event.key == pygame.K_RETURN:
                    if spawn_pos:
                        save_spawn(track_name, spawn_pos, spawn_angle)
                    else:
                        print("⚠️ Click to set position first!")

        # draw preview
        if spawn_pos:
            x, y = spawn_pos
            pygame.draw.circle(screen, (255, 255, 0), (x, y), 6)

            rad = math.radians(spawn_angle)
            end_x = x + math.cos(rad) * 50
            end_y = y + math.sin(rad) * 50
            pygame.draw.line(screen, (255, 0, 0), (x, y), (end_x, end_y), 4)

            angle_text = font.render(f"angle={spawn_angle}", True, (255, 255, 0))
            screen.blit(angle_text, (x + 10, y + 10))

        pygame.display.update()


# ============================================================
#                  MAIN ENTRY POINT
# ============================================================
if __name__ == "__main__":
    chosen_track = select_track_menu()
    run_spawn_selector(chosen_track)

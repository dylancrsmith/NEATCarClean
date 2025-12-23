import pygame
import sys
import math
import os

from car import WIDTH, HEIGHT

pygame.init()

TRACKS_DIR = "tracks"
CONFIG_PATH = "track_config.py"
FONT = pygame.font.SysFont("consolas", 28)


# ============================================================
#         LOAD/SAVE CONFIG
# ============================================================
def load_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write("TRACK_CONFIG = {}\n")

    namespace = {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        exec(f.read(), namespace)

    return namespace.get("TRACK_CONFIG", {})


def save_config(track_config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write("TRACK_CONFIG = " + repr(track_config) + "\n")


# ============================================================
#         TRACK SELECTION MENU
# ============================================================
def select_track_menu():
    screen = pygame.display.set_mode((650, 500))
    pygame.display.set_caption("Select Track")

    clean_tracks = [f for f in os.listdir(TRACKS_DIR) if f.endswith("_clean.png")]
    if not clean_tracks:
        print("❌ No cleaned tracks found.")
        sys.exit()

    while True:
        screen.fill((20, 20, 20))

        title = FONT.render("Select a Track (Press Number):", True, (255, 255, 255))
        screen.blit(title, (40, 20))

        for i, t in enumerate(clean_tracks):
            entry = FONT.render(f"{i+1}. {t}", True, (200, 200, 0))
            screen.blit(entry, (40, 80 + i * 40))

        pygame.display.update()

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
#         MAIN EDITOR (SPAWN + FINISH)
# ============================================================
def run_track_editor(track_name):
    pygame.display.set_caption(f"Track Editor — {track_name}")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 22)

    track_path = os.path.join(TRACKS_DIR, track_name)
    track_img = pygame.image.load(track_path).convert()
    track_img = pygame.transform.scale(track_img, (WIDTH, HEIGHT))

    cfg = load_config()
    track_entry = cfg.get(track_name, {})

    # existing values (if any)
    spawn = track_entry.get("spawn")
    finish = track_entry.get("finish")

    spawn_pos = (spawn["x"], spawn["y"]) if spawn else None
    spawn_angle = spawn["angle"] if spawn else 0

    finish_rect = pygame.Rect(0, 0, 60, 60)
    if finish:
        finish_rect = pygame.Rect(finish["x"], finish["y"], finish["w"], finish["h"])
    else:
        finish_rect.center = (WIDTH // 2, HEIGHT // 2)

    mode = "spawn"  # "spawn" or "finish"

    while True:
        clock.tick(60)
        screen.blit(track_img, (0, 0))

        # draw overlays
        if spawn_pos:
            x, y = spawn_pos
            pygame.draw.circle(screen, (255, 255, 0), (x, y), 6)
            rad = math.radians(spawn_angle)
            end_x = x + math.cos(rad) * 50
            end_y = y + math.sin(rad) * 50
            pygame.draw.line(screen, (255, 0, 0), (x, y), (end_x, end_y), 4)

        pygame.draw.rect(screen, (255, 0, 0), finish_rect, 2)

        # UI text
        ui1 = font.render(f"MODE: {mode.upper()}   [TAB switch]  [ENTER save]", True, (255, 255, 255))
        ui2 = font.render("SPAWN: click to set | Q/E rotate", True, (255, 255, 0))
        ui3 = font.render("FINISH: click to move | +/- resize", True, (255, 80, 80))
        screen.blit(ui1, (10, 10))
        screen.blit(ui2, (10, 40))
        screen.blit(ui3, (10, 70))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # switch mode
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                mode = "finish" if mode == "spawn" else "spawn"

            # click sets current mode object
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if mode == "spawn":
                    spawn_pos = (mx, my)
                    print(f"📍 Spawn set: {spawn_pos}")
                else:
                    finish_rect.center = (mx, my)
                    print(f"🏁 Finish moved: {finish_rect}")

            if event.type == pygame.KEYDOWN:
                if mode == "spawn":
                    if event.key == pygame.K_q:
                        spawn_angle += 5
                    elif event.key == pygame.K_e:
                        spawn_angle -= 5

                if mode == "finish":
                    if event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                        finish_rect.w += 5
                        finish_rect.h += 5
                    elif event.key == pygame.K_MINUS:
                        finish_rect.w = max(10, finish_rect.w - 5)
                        finish_rect.h = max(10, finish_rect.h - 5)

                # save
                if event.key == pygame.K_RETURN:
                    if not spawn_pos:
                        print("⚠️ Set spawn first (click in spawn mode).")
                        continue

                    cfg[track_name] = {
                        "spawn": {"x": spawn_pos[0], "y": spawn_pos[1], "angle": spawn_angle},
                        "finish": {"x": finish_rect.x, "y": finish_rect.y, "w": finish_rect.w, "h": finish_rect.h},
                    }
                    save_config(cfg)
                    print(f"💾 Saved track config for {track_name}: {cfg[track_name]}")
                    return


# ============================================================
#                  MAIN ENTRY POINT
# ============================================================
if __name__ == "__main__":
    chosen_track = select_track_menu()
    run_track_editor(chosen_track)

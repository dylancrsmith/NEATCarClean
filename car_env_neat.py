import os
import pygame
import neat

from car import Car, WIDTH, HEIGHT
from track_config import TRACK_CONFIG  # ✅ unified config

FPS = 60
TRACKS_DIR = "tracks"

TRACK_NAME = "DriveIt_clean.png"
TRACK_PATH = os.path.join(TRACKS_DIR, TRACK_NAME)

# =========================
# Reward shaping (minimal)
# =========================
PER_FRAME_SPEED_REWARD = 0.05   # tiny encouragement to move
CRASH_PENALTY = 50              # mild exploration penalty

# Finish rewards (main objective)
FINISH_BASE_REWARD = 3000               # finishing is always good
FINISH_SLOW_REWARD = 1500               # finished but not a PB

# ✅ BIG “personal best” reward logic
PB_BASE_REWARD = 15000                  # major reward if new best time
PB_BONUS_PER_FRAME = 30                 # extra per frame faster than old best

# Optional cap
MAX_FRAMES = FPS * 30


class CarEnv:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("NEAT Car Env")

        # load track
        self.track = pygame.image.load(TRACK_PATH).convert()
        self.track = pygame.transform.scale(self.track, (WIDTH, HEIGHT))

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20)
        self.generation = 0

        # =========================
        # Load spawn + finish from config
        # =========================
        cfg = TRACK_CONFIG.get(TRACK_NAME)

        if cfg is None:
            print("⚠ No TRACK_CONFIG entry for this track. Using defaults.")
            self.spawn_x = WIDTH // 2
            self.spawn_y = HEIGHT // 2
            self.spawn_angle = 0
            self.finish_rect = pygame.Rect(WIDTH // 2, HEIGHT // 2, 60, 60)
        else:
            sp = cfg.get("spawn", {"x": WIDTH // 2, "y": HEIGHT // 2, "angle": 0})
            fn = cfg.get("finish", {"x": WIDTH // 2, "y": HEIGHT // 2, "w": 60, "h": 60})

            self.spawn_x = sp["x"]
            self.spawn_y = sp["y"]
            self.spawn_angle = sp["angle"]
            self.finish_rect = pygame.Rect(fn["x"], fn["y"], fn["w"], fn["h"])

        # BEST LAP TIME (frames) seen so far
        self.best_finish_time = None

        # Optional: start gating (prevents “finish right next to spawn” cheating)
        self.start_rect = pygame.Rect(self.spawn_x - 60, self.spawn_y - 60, 120, 120)

    # =====================================================================
    #                           FINISH DETECTION
    # =====================================================================
    def is_finished(self, car: Car) -> bool:
        return self.finish_rect.collidepoint(int(car.x), int(car.y))

    # =====================================================================
    #                           EVALUATION
    # =====================================================================
    def eval_genomes(self, genomes, config):
        self.generation += 1

        nets = []
        cars = []
        ge = []

        # create cars
        for _, genome in genomes:
            genome.fitness = 0.0
            ge.append(genome)

            net = neat.nn.FeedForwardNetwork.create(genome, config)
            nets.append(net)

            car = Car(self.spawn_x, self.spawn_y, self.spawn_angle)
            car.speed = 1.0

            # ✅ must leave start area before finish counts (prevents instant finish)
            car.left_start = False

            cars.append(car)

        while True:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

            alive = 0

            for i, car in enumerate(cars):
                if not car.alive:
                    continue

                alive += 1

                # hard cap
                if MAX_FRAMES is not None and car.time_alive >= MAX_FRAMES:
                    car.alive = False
                    continue

                # INPUTS
                inputs = car.get_inputs()

                # OUTPUTS = [steer, throttle]
                steer, throttle = nets[i].activate(inputs)

                # Steering
                if steer > 0.3:
                    car.steer_right()
                elif steer < -0.3:
                    car.steer_left()

                # Throttle
                if throttle > 0.2:
                    car.accelerate()
                else:
                    car.brake()

                car.update(self.track)

                # crashed?
                if not car.alive:
                    ge[i].fitness -= CRASH_PENALTY
                    continue

                # tiny per-frame reward (doesn't dominate)
                ge[i].fitness += car.speed * PER_FRAME_SPEED_REWARD

                # ✅ mark when the car has truly left the spawn zone
                if not car.left_start and not self.start_rect.collidepoint(int(car.x), int(car.y)):
                    car.left_start = True

                # FINISH CHECK (only after leaving start)
                if car.left_start and self.is_finished(car):
                    finish_time = car.time_alive  # frames to finish

                    # always reward finishing
                    ge[i].fitness += FINISH_BASE_REWARD

                    if self.best_finish_time is None:
                        # first ever finish sets baseline (treat as PB)
                        self.best_finish_time = finish_time
                        ge[i].fitness += PB_BASE_REWARD
                    else:
                        improvement = self.best_finish_time - finish_time

                        if improvement > 0:
                            # ✅ MAJOR reward for new best time
                            ge[i].fitness += PB_BASE_REWARD + improvement * PB_BONUS_PER_FRAME
                            self.best_finish_time = finish_time
                        else:
                            # finished but slower than PB
                            ge[i].fitness += FINISH_SLOW_REWARD

                    car.alive = False
                    continue

            if alive == 0:
                break

            self.render(cars)

    # =====================================================================
    #                              RENDER
    # =====================================================================
    def render(self, cars):
        self.screen.blit(self.track, (0, 0))

        # finish rect
        pygame.draw.rect(self.screen, (255, 0, 0), self.finish_rect, 2)

        # start rect (debug only; remove later if you want)
        pygame.draw.rect(self.screen, (0, 120, 255), self.start_rect, 2)

        for car in cars:
            if car.alive:
                car.draw(self.screen)

        best_txt = "None" if self.best_finish_time is None else str(self.best_finish_time)
        text = self.font.render(f"Gen {self.generation} | BestFinish(frames): {best_txt}", True, (255, 255, 255))
        self.screen.blit(text, (10, 10))

        pygame.display.flip()

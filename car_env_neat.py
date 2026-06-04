import os
import pygame
import neat

from car import Car, WIDTH, HEIGHT
from track_config import TRACK_CONFIG  # ✅ unified config

FPS = 60
TRACKS_DIR = "tracks"

# =========================
# Reward shaping
# =========================
DISTANCE_REWARD = 0.1           # reward per pixel travelled
FINISH_BONUS = 5000             # bonus for completing a lap
PB_BONUS = 10000                # extra bonus for a new best lap time
PB_BONUS_PER_FRAME = 20         # extra per frame faster than old best

# Stagnation cull — kill cars that stop making progress
STAGNATION_FRAMES = 60          # check every N frames (every 1s)
STAGNATION_MIN_DIST = 60        # must have moved at least this many pixels

MAX_FRAMES = FPS * 60           # 60s hard cap per generation


class CarEnv:
    def __init__(self, track_name="DriveIt_clean.png"):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("NEAT Car Env")

        track_path = os.path.join(TRACKS_DIR, track_name)
        self.track = pygame.image.load(track_path).convert()
        self.track = pygame.transform.scale(self.track, (WIDTH, HEIGHT))

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20)
        self.generation = 0

        # =========================
        # Load spawn + finish from config
        # =========================
        cfg = TRACK_CONFIG.get(track_name)

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
            car.left_start = False
            car.last_check_dist = 0.0   # distance at last stagnation check

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

                # stagnation cull — kill cars not making progress
                if car.time_alive % STAGNATION_FRAMES == 0 and car.time_alive > 0:
                    dist_gained = car.distance - car.last_check_dist
                    if dist_gained < STAGNATION_MIN_DIST:
                        car.alive = False
                        continue
                    car.last_check_dist = car.distance

                # INPUTS
                inputs = car.get_inputs()

                # OUTPUTS = [steer, throttle]
                steer, throttle = nets[i].activate(inputs)

                if steer > 0.3:
                    car.steer_right()
                elif steer < -0.3:
                    car.steer_left()

                if throttle > 0.2:
                    car.accelerate()
                else:
                    car.brake()

                car.update(self.track)

                # crashed — fitness is whatever distance they reached
                if not car.alive:
                    ge[i].fitness = car.distance * DISTANCE_REWARD
                    continue

                # mark when car leaves spawn zone
                if not car.left_start and not self.start_rect.collidepoint(int(car.x), int(car.y)):
                    car.left_start = True

                # finish check (only after leaving start)
                if car.left_start and self.is_finished(car):
                    finish_time = car.time_alive

                    ge[i].fitness = car.distance * DISTANCE_REWARD + FINISH_BONUS

                    if self.best_finish_time is None:
                        self.best_finish_time = finish_time
                        ge[i].fitness += PB_BONUS
                    else:
                        improvement = self.best_finish_time - finish_time
                        if improvement > 0:
                            ge[i].fitness += PB_BONUS + improvement * PB_BONUS_PER_FRAME
                            self.best_finish_time = finish_time

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


        for car in cars:
            if car.alive:
                car.draw(self.screen)

        best_txt = "None" if self.best_finish_time is None else str(self.best_finish_time)
        text = self.font.render(f"Gen {self.generation} | BestFinish(frames): {best_txt}", True, (255, 255, 255))
        self.screen.blit(text, (10, 10))

        pygame.display.flip()

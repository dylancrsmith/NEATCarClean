import os
import pygame
import neat

from car import Car, WIDTH, HEIGHT
from track_config import TRACK_CONFIG

FPS = 60
TRACKS_DIR = "tracks"

# =========================
# Reward shaping
# =========================
PER_FRAME_SPEED_REWARD = 0.05
CRASH_PENALTY = 50

FINISH_BASE_REWARD = 3000
FINISH_SLOW_REWARD = 1500

PB_BASE_REWARD = 15000
PB_BONUS_PER_FRAME = 30

MAX_FRAMES = FPS * 30


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

        cfg = TRACK_CONFIG.get(track_name)

        if cfg is None:
            print(f"No TRACK_CONFIG entry for {track_name}. Run track_selector.py first.")
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

        self.best_finish_time = None
        self.start_rect = pygame.Rect(self.spawn_x - 60, self.spawn_y - 60, 120, 120)

    def is_finished(self, car: Car) -> bool:
        return self.finish_rect.collidepoint(int(car.x), int(car.y))

    def eval_genomes(self, genomes, config):
        self.generation += 1

        nets = []
        cars = []
        ge = []

        for _, genome in genomes:
            genome.fitness = 0.0
            ge.append(genome)
            net = neat.nn.FeedForwardNetwork.create(genome, config)
            nets.append(net)
            car = Car(self.spawn_x, self.spawn_y, self.spawn_angle)
            car.speed = 1.0
            car.left_start = False
            car.last_checkpoint_dist = 0.0
            car.last_checkpoint_frame = 0
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

                if car.time_alive >= MAX_FRAMES:
                    car.alive = False
                    continue

                # kill cars not making distance progress (every 90 frames, must have moved 40px)
                if car.time_alive - car.last_checkpoint_frame >= 90:
                    if car.distance - car.last_checkpoint_dist < 40:
                        car.alive = False
                        continue
                    car.last_checkpoint_dist = car.distance
                    car.last_checkpoint_frame = car.time_alive

                inputs = car.get_inputs()
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

                if not car.alive:
                    ge[i].fitness -= CRASH_PENALTY
                    continue

                ge[i].fitness += car.speed * PER_FRAME_SPEED_REWARD

                if not car.left_start and not self.start_rect.collidepoint(int(car.x), int(car.y)):
                    car.left_start = True

                if car.left_start and self.is_finished(car):
                    finish_time = car.time_alive
                    ge[i].fitness += FINISH_BASE_REWARD

                    if self.best_finish_time is None:
                        self.best_finish_time = finish_time
                        ge[i].fitness += PB_BASE_REWARD
                    else:
                        improvement = self.best_finish_time - finish_time
                        if improvement > 0:
                            ge[i].fitness += PB_BASE_REWARD + improvement * PB_BONUS_PER_FRAME
                            self.best_finish_time = finish_time
                        else:
                            ge[i].fitness += FINISH_SLOW_REWARD

                    car.alive = False

            if alive == 0:
                break

            self.render(cars)

    def render(self, cars):
        self.screen.blit(self.track, (0, 0))
        pygame.draw.rect(self.screen, (255, 0, 0), self.finish_rect, 2)

        for car in cars:
            if car.alive:
                car.draw(self.screen)

        best_txt = "None" if self.best_finish_time is None else str(self.best_finish_time)
        text = self.font.render(f"Gen {self.generation} | Best: {best_txt} frames", True, (255, 255, 255))
        self.screen.blit(text, (10, 10))
        pygame.display.flip()

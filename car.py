import math
import pygame

# ===== Constants =====
WIDTH = 1440
HEIGHT = 770

CAR_W = 8
CAR_H = 8

BORDER_COLOR = (0, 0, 0)       # black = off track
MAX_SENSOR_DIST = 350


class Car:
    def __init__(self, x, y, angle=0):
        base = pygame.Surface((CAR_W, CAR_H), pygame.SRCALPHA)
        base.fill((0, 255, 0))
        self.sprite = base
        self.rotated = base

        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)

        self.distance = 0.0
        self.time_alive = 0
        self.last_x = self.x
        self.last_y = self.y

        # movement
        self.speed = 1.0
        self.max_speed = 3.0
        self.acceleration = 0.12
        self.deceleration = 0.08
        self.turn_rate = 3.0

        # sensors
        self.sensor_angles = [-60, -30, -15, 0, 15, 30, 60]
        self.sensor_readings = [MAX_SENSOR_DIST] * len(self.sensor_angles)

        self.alive = True

    # =====================================================================
    #                          MAIN UPDATE
    # =====================================================================
    def update(self, track_surf):
        if not self.alive:
            return

        self.speed = max(self.speed, 0.8)

        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed

        dx = self.x - self.last_x
        dy = self.y - self.last_y
        self.distance += math.hypot(dx, dy)
        self.time_alive += 1
        self.last_x = self.x
        self.last_y = self.y

        self.rotated = pygame.transform.rotate(self.sprite, -self.angle)
        self.rect = self.rotated.get_rect(center=(self.x, self.y))

        if self._hits_wall(track_surf):
            self.alive = False
            self.speed = 0
            return

        self._update_sensors(track_surf)

    # =====================================================================
    #                           CONTROLS
    # =====================================================================
    def steer_left(self):
        self.angle += self.turn_rate

    def steer_right(self):
        self.angle -= self.turn_rate

    def accelerate(self):
        self.speed = min(self.speed + self.acceleration, self.max_speed)

    def brake(self):
        self.speed = max(self.speed - self.deceleration, 0)

    # =====================================================================
    #                           COLLISION
    # =====================================================================
    def _hits_wall(self, track_surf):
        px = int(self.x)
        py = int(self.y)

        if px < 0 or px >= WIDTH or py < 0 or py >= HEIGHT:
            return True

        pixel = track_surf.get_at((px, py))[:3]
        return pixel == BORDER_COLOR

    # =====================================================================
    #                           SENSORS
    # =====================================================================
    def _update_sensors(self, track_surf):
        cx, cy = self.x, self.y
        self.sensor_readings = []

        for rel in self.sensor_angles:
            ang = math.radians(self.angle + rel)
            dist = 0
            x, y = cx, cy

            while dist < MAX_SENSOR_DIST:
                x += math.cos(ang)
                y += math.sin(ang)
                dist += 1

                ix, iy = int(x), int(y)

                if ix < 0 or ix >= WIDTH or iy < 0 or iy >= HEIGHT:
                    break

                if track_surf.get_at((ix, iy))[:3] == BORDER_COLOR:
                    break

            self.sensor_readings.append(dist)

    # =====================================================================
    #                           NEAT INPUTS
    # =====================================================================
    def get_inputs(self):
        return [d / MAX_SENSOR_DIST for d in self.sensor_readings]

    # =====================================================================
    #                           DRAW
    # =====================================================================
    def draw(self, screen, draw_sensors=False):
        if draw_sensors:
            cx, cy = int(self.x), int(self.y)
            for i, rel in enumerate(self.sensor_angles):
                ang = math.radians(self.angle + rel)
                dist = self.sensor_readings[i]
                end_x = int(cx + math.cos(ang) * dist)
                end_y = int(cy + math.sin(ang) * dist)
                pygame.draw.line(screen, (0, 200, 255), (cx, cy), (end_x, end_y), 1)
        screen.blit(self.rotated, self.rect.topleft)

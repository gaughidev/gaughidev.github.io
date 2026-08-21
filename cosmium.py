import math
import random
import sys

import pygame


WIDTH = 900
HEIGHT = 600
FPS = 60

BLACK = (8, 10, 18)
WHITE = (245, 247, 255)
BLUE = (126, 200, 255)
GOLD = (255, 209, 102)
RED = (255, 95, 95)
GRAY = (170, 175, 190)


class Rocket:
    def __init__(self):
        self.x = WIDTH / 2
        self.y = HEIGHT - 70
        self.radius = 18
        self.speed = 360
        self.angle = -90

    def update(self, dt, keys):
        dx = 0
        dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1

        if dx or dy:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length
            self.x += dx * self.speed * dt
            self.y += dy * self.speed * dt
            self.angle = math.degrees(math.atan2(dy, dx)) + 90

        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

    def draw(self, screen):
        cx = int(self.x)
        cy = int(self.y)
        points = []
        for px, py in [(-12, 18), (0, -22), (12, 18), (0, 8)]:
            angle = math.radians(self.angle)
            rx = px * math.cos(angle) - py * math.sin(angle)
            ry = px * math.sin(angle) + py * math.cos(angle)
            points.append((cx + rx, cy + ry))

        pygame.draw.polygon(screen, WHITE, points)
        pygame.draw.polygon(screen, BLUE, points, 2)

        flame_points = []
        for px, py in [(-6, 18), (6, 18), (0, 24 + random.randint(0, 6))]:
            angle = math.radians(self.angle)
            rx = px * math.cos(angle) - py * math.sin(angle)
            ry = px * math.sin(angle) + py * math.cos(angle)
            flame_points.append((cx + rx, cy + ry))
        if random.random() < 0.9:
            pygame.draw.polygon(screen, GOLD, flame_points)


class Asteroid:
    def __init__(self):
        self.size = random.randint(18, 42)
        self.x = random.randint(self.size, WIDTH - self.size)
        self.y = -self.size - random.randint(20, 120)
        self.speed = random.randint(120, 220)
        self.rotation = random.uniform(0, 2 * math.pi)
        self.spin = random.uniform(-1.5, 1.5)
        self.points = []
        for i in range(8):
            angle = i / 8 * (2 * math.pi)
            radius = self.size * random.uniform(0.7, 1.2)
            self.points.append((math.cos(angle) * radius, math.sin(angle) * radius))

    def update(self, dt):
        self.y += self.speed * dt
        self.rotation += self.spin * dt

    def draw(self, screen):
        transformed = []
        for px, py in self.points:
            x = self.x + px * math.cos(self.rotation) - py * math.sin(self.rotation)
            y = self.y + px * math.sin(self.rotation) + py * math.cos(self.rotation)
            transformed.append((x, y))
        pygame.draw.polygon(screen, GRAY, transformed)
        pygame.draw.polygon(screen, RED, transformed, 2)

    def collides_with(self, rocket):
        dx = self.x - rocket.x
        dy = self.y - rocket.y
        return math.hypot(dx, dy) < self.size + rocket.radius


class Stardust:
    def __init__(self):
        self.radius = 7
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = -self.radius - random.randint(10, 90)
        self.speed = random.randint(80, 180)
        self.phase = random.uniform(0, 2 * math.pi)

    def update(self, dt):
        self.y += self.speed * dt
        self.phase += dt * 8

    def draw(self, screen):
        shimmer = 0.5 + 0.5 * math.sin(self.phase)
        radius = int(self.radius * (0.8 + shimmer * 0.8))
        pygame.draw.circle(screen, GOLD, (int(self.x), int(self.y)), radius)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), max(2, radius // 2), 1)

    def collides_with(self, rocket):
        dx = self.x - rocket.x
        dy = self.y - rocket.y
        return math.hypot(dx, dy) < self.radius + rocket.radius


class Starfield:
    def __init__(self):
        self.stars = []
        for _ in range(130):
            self.stars.append({
                'x': random.randint(0, WIDTH),
                'y': random.randint(0, HEIGHT),
                'size': random.randint(1, 3),
                'speed': random.uniform(10, 70),
            })

    def update(self, dt):
        for star in self.stars:
            star['y'] += star['speed'] * dt
            if star['y'] > HEIGHT:
                star['y'] = -5
                star['x'] = random.randint(0, WIDTH)

    def draw(self, screen):
        for star in self.stars:
            pygame.draw.circle(screen, WHITE, (int(star['x']), int(star['y'])), star['size'])


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Cosmium: Stardust Escape')
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('arial', 26, bold=True)
        self.big_font = pygame.font.SysFont('arial', 48, bold=True)
        self.reset()

    def reset(self):
        self.rocket = Rocket()
        self.starfield = Starfield()
        self.asteroids = []
        self.stardust = []
        self.score = 0
        self.health = 100
        self.game_over = False
        self.asteroid_timer = 0.0
        self.dust_timer = 0.0

    def spawn_asteroid(self):
        self.asteroids.append(Asteroid())

    def spawn_dust(self):
        self.stardust.append(Stardust())

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if self.game_over and event.key == pygame.K_SPACE:
                    self.reset()
        return True

    def update(self, dt):
        if self.game_over:
            self.starfield.update(dt)
            return

        self.starfield.update(dt)
        keys = pygame.key.get_pressed()
        self.rocket.update(dt, keys)

        self.asteroid_timer += dt
        self.dust_timer += dt

        spawn_interval = max(0.55, 1.5 - self.score * 0.04)
        if self.asteroid_timer >= spawn_interval:
            self.spawn_asteroid()
            self.asteroid_timer = 0.0

        if self.dust_timer >= 1.15:
            self.spawn_dust()
            self.dust_timer = 0.0

        for asteroid in self.asteroids:
            asteroid.update(dt)
            if asteroid.collides_with(self.rocket):
                self.health -= 1
                self.asteroids.remove(asteroid)
                break

        for dust in self.stardust:
            dust.update(dt)
            if dust.collides_with(self.rocket):
                self.score += 1
                self.stardust.remove(dust)
                break

        self.asteroids = [a for a in self.asteroids if a.y < HEIGHT + 120]
        self.stardust = [d for d in self.stardust if d.y < HEIGHT + 80]

        if self.health <= 0:
            self.game_over = True

    def draw(self):
        self.screen.fill(BLACK)
        self.starfield.draw(self.screen)

        for asteroid in self.asteroids:
            asteroid.draw(self.screen)

        for dust in self.stardust:
            dust.draw(self.screen)

        self.rocket.draw(self.screen)

        score_text = self.font.render(f'Stardust: {self.score}', True, WHITE)
        health_text = self.font.render(f'Health: {self.health}', True, WHITE)
        self.screen.blit(score_text, (20, 18))
        self.screen.blit(health_text, (WIDTH - health_text.get_width() - 20, 18))

        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((11, 14, 25, 180))
            self.screen.blit(overlay, (0, 0))
            title = self.big_font.render('Mission Failed', True, RED)
            restart = self.font.render('Press SPACE to restart', True, WHITE)
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 30))
            self.screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + 30))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    Game().run()

import pygame as pg
import sys


class Introduction():
    def __init__(self, image: str):
        self.image = image
        self.width = 800
        self.height = 600
        self._setup_pygame()

    def _setup_pygame(self):
        r = pg.init()
        print(f"pg.init() returned {r}")
        surface = pg.display.set_mode((self.width, self.height))
        print(f"created surface: {surface}")
        self.surface = surface

    def run(self):        
        speed = [2, 2]
        black = 0, 0, 0

        ball = pg.image.load(self.image)
        ballrect = ball.get_rect()

        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT: sys.exit()

            ballrect = ballrect.move(speed)
            if ballrect.left < 0 or ballrect.right > self.width:
                speed[0] = -speed[0]
            if ballrect.top < 0 or ballrect.bottom > self.height:
                speed[1] = -speed[1]

            self.surface.fill(black)
            self.surface.blit(ball, ballrect)
            pg.display.flip()


import pygame as pg
from simworld.scenes.introduction import Introduction

def start_game():
    pg.init()
    surface = pg.display.set_mode((800, 600))
    Introduction(pg)
    

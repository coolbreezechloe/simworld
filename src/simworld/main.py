import pathlib
from simworld.scenes.introduction import Introduction

def start_game():
    here = pathlib.Path(__file__).parent.resolve()
    intro = Introduction(here / "introduction_assets")
    intro.run()
    

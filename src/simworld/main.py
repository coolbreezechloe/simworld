import pathlib
from simworld.introduction import Introduction

def start_game():
    here = pathlib.Path(__file__).parent.resolve()
    intro = Introduction(here / "introduction_assets")
    intro.run()
    
if __name__ == '__main__':
    start_game()
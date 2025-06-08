import asyncio

#from src.flappy import Flappy
from src.flappy_jump import Flappy

if __name__ == "__main__":
    asyncio.run(Flappy().start())

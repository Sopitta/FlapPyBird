import asyncio
import sys
import os

import pygame
from pygame.locals import K_ESCAPE, K_SPACE, K_UP, KEYDOWN, QUIT

from .entities import (
    Background,
    Floor,
    GameOver,
    Pipes,
    Player,
    PlayerMode,
    Score,
    WelcomeMessage,
)
from .utils import GameConfig, Images, Sounds, Window
from .utils.pose_detector import PoseDetector
import cv2


class Flappy:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Flappy Bird")
        window = Window(288, 512)
        screen = pygame.display.set_mode((window.width, window.height))
        images = Images()

        self.config = GameConfig(
            screen=screen,
            clock=pygame.time.Clock(),
            fps=60,  
            window=window,
            images=images,
            sounds=Sounds(),
        )
        
        # Initialize pose detector
        self.pose_detector = PoseDetector()
        
        # Position the game window next to the camera window
        pygame.display.set_mode((window.width, window.height))
        pygame.display.get_surface().set_alpha(None)
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{640 + 50},50" 

    async def start(self):
        try:
            while True:
                self.background = Background(self.config)
                self.floor = Floor(self.config)
                self.player = Player(self.config)
                self.welcome_message = WelcomeMessage(self.config)
                self.game_over_message = GameOver(self.config)
                self.pipes = Pipes(self.config)
                self.score = Score(self.config)
                await self.splash()
                await self.play()
                await self.game_over()
        finally:
            # Clean up when the game ends
            pygame.quit()
            cv2.destroyAllWindows()

    async def splash(self):
        """Shows welcome splash screen animation of flappy bird"""
        self.player.set_mode(PlayerMode.SHM)

        while True:
            for event in pygame.event.get():
                self.check_quit_event(event)
                if self.is_tap_event(event):
                    return

            self.background.tick()
            self.floor.tick()
            self.player.tick()
            self.welcome_message.tick()

            pygame.display.update()
            await asyncio.sleep(0)
            self.config.tick()

    def check_quit_event(self, event):
        if event.type == QUIT or (
            event.type == KEYDOWN and event.key == K_ESCAPE
        ):
            pygame.quit()
            cv2.destroyAllWindows()
            sys.exit()

    def is_tap_event(self, event):
        m_left, _, _ = pygame.mouse.get_pressed()
        space_or_up = event.type == KEYDOWN and (
            event.key == K_SPACE or event.key == K_UP
        )
        screen_tap = event.type == pygame.FINGERDOWN
        return m_left or space_or_up or screen_tap

    async def play(self):
        self.score.reset()
        self.player.set_mode(PlayerMode.NORMAL)
        last_jump_time = 0
        jump_cooldown = 0.1  # Minimum time between jumps in seconds

        while True:
            if self.player.collided(self.pipes, self.floor):
                return

            current_time = pygame.time.get_ticks() / 1000.0  # Convert to seconds

            for i, pipe in enumerate(self.pipes.upper):
                if self.player.crossed(pipe):
                    self.score.add()

            for event in pygame.event.get():
                self.check_quit_event(event)
                if self.is_tap_event(event):
                    self.player.flap()

            # Check for jump using pose detection with cooldown
            if current_time - last_jump_time > jump_cooldown:
                if self.pose_detector.detect_jump():
                    self.player.flap()
                    last_jump_time = current_time

            self.background.tick()
            self.floor.tick()
            self.pipes.tick()
            self.score.tick()
            self.player.tick()

            pygame.display.update()
            await asyncio.sleep(0)
            self.config.tick()

    async def game_over(self):
        """crashes the player down and shows gameover image"""
        self.player.set_mode(PlayerMode.CRASH)
        self.pipes.stop()
        self.floor.stop()

        while True:
            for event in pygame.event.get():
                self.check_quit_event(event)
                if self.is_tap_event(event):
                    if self.player.y + self.player.h >= self.floor.y - 1:
                        return

            self.background.tick()
            self.floor.tick()
            self.pipes.tick()
            self.score.tick()
            self.player.tick()
            self.game_over_message.tick()

            self.config.tick()
            pygame.display.update()
            await asyncio.sleep(0)

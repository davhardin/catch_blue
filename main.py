import pygame
import sys

pygame.init()

screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("My Pygame Window")

clock = pygame.time.Clock()
dt = 60

# Main loop

running = True

while running:
    for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

screen.fill((255, 255, 255))
pygame.display.flip()
clock.tick(dt)

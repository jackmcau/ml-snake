import pygame
from enum import Enum

class gameState(Enum):
    MENU = 0
    PLAYING = 1
    BOT = 2


# pygame setup
pygame.init()
screen = pygame.display.set_mode((720, 720), flags=pygame.SCALED, vsync=1)
clock = pygame.time.Clock()
running = True
dt = 0
height = 15
width = 15
margin = 30
text = pygame.font.Font(None, 36)
state = gameState.MENU

pygame.display.set_caption("Snake")

player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)

map = [["" for i in range(width)] for j in range(height)]

def drawMap(mapIn):
    squareWidth = (screen.get_width() - (2*margin))/ width
    squareHeight = (screen.get_height() - (2*margin)) / height

    for row, content in enumerate(mapIn):
        for column, item in enumerate(content):
            pygame.draw.polygon(screen,
                                pygame.Color(0, 200+(20*((row+column) % 2)), 0),
                                [(column*squareWidth+margin, row*squareHeight+margin),
                                 ((column+1)*squareWidth+margin, row*squareHeight+margin),
                                 ((column+1)*squareWidth+margin, (row+1)*squareHeight+margin),
                                 (column*squareWidth+margin, (row+1)*squareHeight+margin)])
            if item == "":
                continue
            else:
                # draw
                continue




while running:

    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    
    # fill the screen with a color to wipe away anything from last frame
    screen.fill("green")

    if state == gameState.MENU:
        playButton = pygame.draw.rect(screen, "gray", (screen.get_width()/2-50, screen.get_height()/2-50, 100, 70))
        play = text.render("Play", True, "black")
        screen.blit(play, ((screen.get_width() - play.get_width()) / 2, (screen.get_height() - play.get_height()) / 2 - 16.5))

        keys = pygame.mouse.get_pressed()
        if keys[0]:
            print(playButton.collidepoint(pygame.mouse.get_pos()))
            state = gameState.PLAYING
    else:

        #pygame.draw.polygon(screen, pygame.Color(255,255,255), [(0, 0), (100, 0), (100, 100),(0, 100)])
        drawMap(map)

        # POLL FOR DIRECTION DEPENDING ON GAME STATE
        #keys = pygame.key.get_pressed()
        #if keys[pygame.K_w]:
        #    player_pos.y -= 300 * dt
        #if keys[pygame.K_s]:
        #    player_pos.y += 300 * dt
        #if keys[pygame.K_a]:
        #    player_pos.x -= 300 * dt
        #if keys[pygame.K_d]:
        #    player_pos.x += 300 * dt


        fps = text.render(f"{clock.get_fps():.2f} fps", True, "black")
        screen.blit(fps, (screen.get_width() / 2 - fps.get_width() / 2, screen.get_height() - fps.get_height() - 2))

    dt = clock.tick(60) / 1000
    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.

pygame.quit()
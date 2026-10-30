import pygame
import random
from enum import Enum

class gameState(Enum):
    MENU = 0
    PLAYING = 1
    BOT = 2


# Pygame setup
pygame.init()
screen = pygame.display.set_mode((720, 720), flags=pygame.SCALED, vsync=1)
clock = pygame.time.Clock()
running = True
dt = 0

# Unchanging variables
HEIGHT = 15
WIDTH = 15
MARGIN = 30
TEXT = pygame.font.Font(None, 36)

pygame.display.set_caption("Snake")

# Game Variables
map = [["" for i in range(WIDTH)] for j in range(HEIGHT)]
map[HEIGHT // 2][2:5] = "sss"

state = gameState.MENU
score = -1

def drawMap(mapIn):
    squareWidth = (screen.get_width() - (2*MARGIN))/ WIDTH
    squareHeight = (screen.get_height() - (2*MARGIN)) / HEIGHT

    for row, content in enumerate(mapIn):
        for column, item in enumerate(content):
            pygame.draw.polygon(screen,
                                pygame.Color(0, 200+(20*((row+column) % 2)), 0),
                                [(column*squareWidth+MARGIN, row*squareHeight+MARGIN),
                                 ((column+1)*squareWidth+MARGIN, row*squareHeight+MARGIN),
                                 ((column+1)*squareWidth+MARGIN, (row+1)*squareHeight+MARGIN),
                                 (column*squareWidth+MARGIN, (row+1)*squareHeight+MARGIN)])
            if item == "":
                continue
            elif item == "A":
                screen.blit(appleImg, (column*squareWidth+MARGIN, row*squareHeight+MARGIN))
                continue
            else:
                pygame.draw.polygon(screen,
                                    pygame.Color(255, 255, 255),
                                    [(column*squareWidth+MARGIN, row*squareHeight+MARGIN),
                                     ((column+1)*squareWidth+MARGIN, row*squareHeight+MARGIN),
                                     ((column+1)*squareWidth+MARGIN, (row+1)*squareHeight+MARGIN),
                                     (column*squareWidth+MARGIN, (row+1)*squareHeight+MARGIN)])
                
#Load apple.png
squareSize = int((screen.get_width() - 2*MARGIN) / WIDTH)
appleImg = pygame.image.load("sprites/apple.png").convert_alpha()
appleImg = pygame.transform.scale(appleImg, (squareSize, squareSize))

def spawnApple(grid):
    while True:
        r = random.randrange(HEIGHT)
        c = random.randrange(WIDTH)
        if grid[r][c] == "":               
         grid[r][c] = "A"

        global score
        score += 1
        return (r,c)

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
        play = TEXT.render("Play", True, "black")
        screen.blit(play, ((screen.get_width() - play.get_width()) / 2, (screen.get_height() - play.get_height()) / 2 - 16.5))

        keys = pygame.mouse.get_pressed()
        if keys[0] and playButton.collidepoint(pygame.mouse.get_pos()):
            print(playButton.collidepoint(pygame.mouse.get_pos()))
            state = gameState.PLAYING
            spawnApple(map)
           
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


        fps = TEXT.render(f"{clock.get_fps():.2f} fps", True, "black")
        screen.blit(fps, (screen.get_width() / 2 - fps.get_width() / 2, screen.get_height() - fps.get_height() - 2))

        scoreText = TEXT.render(f"Score: {score}", True, "black")
        screen.blit(scoreText, (screen.get_width() - scoreText.get_width() - 27, screen.get_height() - scoreText.get_height() - 2))

     #Test

    def spawnPlayer():
        global player_pos

                
        

    dt = clock.tick(60) / 1000
    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.

pygame.quit()
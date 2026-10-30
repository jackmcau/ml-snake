from typing import List

import pygame
import random
from enum import Enum

# Enum definition

class gameState(Enum):
    MENU = 0
    PLAYING = 1
    BOT = 2

class direction(Enum):
    North = (-1, 0)
    East = (0, 1)
    South = (1, 0)
    West = (0, -1)

class snakeBody(Enum): # Defines drawing states for the snake, strictly for visual -- in terms of cardinal directions
    NE = 0
    NS = 1
    NW = 2
    ES = 3
    EW = 4
    SW = 5

# Pygame setup
pygame.init()
screen: pygame.Surface = pygame.display.set_mode((720, 720), flags=pygame.SCALED, vsync=1)
clock: pygame.time.Clock = pygame.time.Clock()
running: bool = True
dt: float = 0

# Unchanging variables
HEIGHT: int = 15
WIDTH: int = 15
MARGIN: int = 30
TEXT: pygame.font.Font = pygame.font.Font(None, 36)
UPDATE_MS: int = 350

# apple.png
SQUARE_SIZE: float = int((screen.get_width() - 2*MARGIN) / WIDTH)
APPLE_IMG: pygame.Surface = pygame.image.load("sprites/apple.png").convert_alpha()
APPLE_IMG = pygame.transform.scale(APPLE_IMG, (SQUARE_SIZE, SQUARE_SIZE))

pygame.display.set_caption("Snake")

# Game Variables
game_map: List[List[int]] = [[0 for i in range(WIDTH)] for j in range(HEIGHT)]
for i in range(3):
    game_map[HEIGHT // 2][i+2] = i+1

state: gameState = gameState.MENU
score: int = -1
since_last_update_ms: int = 0
player_facing: direction = direction.East
player_from: direction = direction.West
player_size: int = 3

def resetGame(): # add any new game variables to this
    global game_map
    game_map = [[0 for i in range(WIDTH)] for j in range(HEIGHT)]
    for i in range(3):
      game_map[HEIGHT // 2][i+2] = i+1

    global state
    state = gameState.MENU
    global score
    score = -1
    global since_last_update_ms
    since_last_update_ms = 0
    global player_facing
    player_facing = direction.East
    global player_from
    player_from = direction.West
    global player_size
    player_size = 3

def drawMap(mapIn: List[List[int]]) -> None:
    squareWidth: float = (screen.get_width() - (2*MARGIN))/ WIDTH
    squareHeight: float = (screen.get_height() - (2*MARGIN)) / HEIGHT

    for row, content in enumerate(mapIn):
        for column, item in enumerate(content):
            pygame.draw.polygon(screen,
                                pygame.Color(0, 200+(20*((row+column) % 2)), 0),
                                [(column*squareWidth+MARGIN, row*squareHeight+MARGIN),
                                 ((column+1)*squareWidth+MARGIN, row*squareHeight+MARGIN),
                                 ((column+1)*squareWidth+MARGIN, (row+1)*squareHeight+MARGIN),
                                 (column*squareWidth+MARGIN, (row+1)*squareHeight+MARGIN)])
            if item == 0:
                continue
            elif item == -1:
                screen.blit(APPLE_IMG, (column*squareWidth+MARGIN, row*squareHeight+MARGIN))
                continue
            else:
                play = TEXT.render(str(item), True, "black")
                screen.blit(play, (MARGIN + column*squareWidth + (squareWidth - play.get_width()) / 2, MARGIN + row*squareHeight + (squareHeight - play.get_height()) / 2))

def spawnApple(mapIn: List[List[int]]) -> List[List[int]]:
    zcount = sum(r.count(0) for r in mapIn)
    placeAt = random.randrange(zcount)
    finder = 0
    for r, row in enumerate(mapIn):
        for c, v in enumerate(row):
            if v == 0:
                if finder == placeAt:
                    mapIn[r][c] = -1
                    return mapIn
                finder += 1
    print("encountered an error with apple spawning.")
    return mapIn # no apple was placed
    
def updateMap(mapIn: List[List[int]], towards: direction) -> tuple[List[List[int]], bool, bool]:
    # Returns an updated map, a bool indicating an apple was picked up, and a bool indicating if the game is over
    head_location: tuple = next(((r, c) for r, row in enumerate(mapIn) for c, val in enumerate(row) if val == player_size), (-1, -1))
    new_head = tuple(map(lambda x, y: x + y, head_location, towards.value))
    if new_head[1] >= WIDTH or new_head[1] < 0:
        return mapIn, False, True
    if new_head[0] >= HEIGHT or new_head[0] < 0:
        return mapIn, False, True

    if mapIn[new_head[0]][new_head[1]] == -1: # got apple
        mapIn[new_head[0]][new_head[1]] = player_size + 1
        # Spawn a new apple
        return spawnApple(mapIn), True, False
    elif mapIn[new_head[0]][new_head[1]] > 1:
        return mapIn, False, True
    else: # didnt get apple
        mapOut = [[(i-1 if i > 0 else i) for i in j] for j in mapIn]
        mapOut[new_head[0]][new_head[1]] = player_size
        return mapOut, False, False

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
            game_map = spawnApple(game_map)
           
    elif state == gameState.PLAYING:

        dt = clock.tick(60)

        # poll for direction change
        keys = pygame.key.get_pressed()
        if keys[pygame.key.key_code("W")] and player_from != direction.North:
            player_facing = direction.North
        elif keys[pygame.key.key_code("A")] and player_from != direction.West:
            player_facing = direction.West
        elif keys[pygame.key.key_code("S")] and player_from != direction.South:
            player_facing = direction.South
        elif keys[pygame.key.key_code("D")] and player_from != direction.East:
            player_facing = direction.East

        since_last_update_ms += dt
        if since_last_update_ms >= UPDATE_MS:

            since_last_update_ms = 0

            player_from = direction((-player_facing.value[0], -player_facing.value[1]))

            game_map, gotApple, gameOver = updateMap(game_map, player_facing)
            if gameOver:
                state = gameState.MENU
                resetGame()
                continue
            elif gotApple:
                print(player_from)
                player_size += 1
                score += 1


        drawMap(game_map)

        fps = TEXT.render(f"{clock.get_fps():.2f} fps", True, "black")
        screen.blit(fps, (screen.get_width() / 2 - fps.get_width() / 2, screen.get_height() - fps.get_height() - 2))

        scoreText = TEXT.render(f"Score: {score}", True, "black")
        screen.blit(scoreText, (screen.get_width() - scoreText.get_width() - 27, screen.get_height() - scoreText.get_height() - 2))

    pygame.display.flip()


# Close if out of main running loop
pygame.quit()
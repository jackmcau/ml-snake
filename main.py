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

HEAD_IMG: pygame.Surface = pygame.image.load("sprites/head.png").convert_alpha()
HEAD_IMG = pygame.transform.scale(HEAD_IMG, (SQUARE_SIZE, SQUARE_SIZE))
TAIL_IMG: pygame.Surface = pygame.image.load("sprites/tail.png").convert_alpha()
TAIL_IMG = pygame.transform.scale(TAIL_IMG, (SQUARE_SIZE, SQUARE_SIZE))
STRAIGHT_IMG: pygame.Surface = pygame.image.load("sprites/straight.png").convert_alpha()
STRAIGHT_IMG = pygame.transform.scale(STRAIGHT_IMG, (SQUARE_SIZE, SQUARE_SIZE))
ELBOW_IMG: pygame.Surface = pygame.image.load("sprites/elbow.png").convert_alpha()
ELBOW_IMG = pygame.transform.scale(ELBOW_IMG, (SQUARE_SIZE, SQUARE_SIZE))

pygame.display.set_caption("Snake")

# Game Variables
game_map: List[List[int]] = [[0 for i in range(WIDTH)] for j in range(HEIGHT)]
for i in range(3):
    game_map[HEIGHT // 2][i+2] = i+1

state: gameState = gameState.MENU
score: int = 0
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
    score = 0
    global since_last_update_ms
    since_last_update_ms = 0
    global player_facing
    player_facing = direction.East
    global player_from
    player_from = direction.West
    global player_size
    player_size = 3

def getSnakePart(mapIn: List[List[int]], x: int, y: int) -> tuple[pygame.Surface, int]:
    type = 0x0 # 0000, NESW
    size: int = 0
    rot: int = 0
    if y != 0 and mapIn[y-1][x] != 0 and abs(mapIn[y-1][x] - mapIn[y][x]) == 1:
        type |= 0x8
        size += 1
    if x != WIDTH - 1 and mapIn[y][x+1] != 0 and abs(mapIn[y][x+1] - mapIn[y][x]) == 1:
        type |= 0x4
        size += 1
        rot += 90
    if y != HEIGHT - 1 and mapIn[y+1][x] != 0 and abs(mapIn[y+1][x] - mapIn[y][x]) == 1:
        type |= 0x2
        size += 1
        rot += 180
    if x != 0 and mapIn[y][x-1] != 0 and abs(mapIn[y][x-1] - mapIn[y][x]) == 1:
        type |= 0x1
        size += 1
        rot += 270
    # At this point, type encodes the direction and body type of the snake
    # IF it is of the form 1010, 0101 it is straight
    # 1000, 0100, 0010, 0001 it is either a head or a tail || if map[y][x] == 1 tail
    print(size, type)
    if size == 1:
        if mapIn[y][x] == 1:
            # tail
            return TAIL_IMG, rot
        else:
            return HEAD_IMG, rot
    if type == 10: # 1010
        return STRAIGHT_IMG, 0
    elif type == 5: # 0101
        return STRAIGHT_IMG, 90
    # 1100 12 NE, 0110 6 SE, 0011 SW 3, 1001 NW 9
    if type == 12:
        return ELBOW_IMG, 0
    elif type == 6:
        return ELBOW_IMG, 90
    if type == 9:
        return ELBOW_IMG, 270
    else:
        return ELBOW_IMG, 180

    # rot is clockwise

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
                #play = TEXT.render(str(item), True, "black")
                #screen.blit(play, (MARGIN + column*squareWidth + (squareWidth - play.get_width()) / 2, MARGIN + row*squareHeight + (squareHeight - play.get_height()) / 2))
                draw = getSnakePart(mapIn, column, row)
                screen.blit(pygame.transform.rotate(draw[0], -draw[1]), (MARGIN + column*squareWidth + (squareWidth - play.get_width()) / 2, MARGIN + row*squareHeight + (squareHeight - play.get_height()) / 2))

def spawnApple(mapIn: List[List[int]]) -> List[List[int]]:
    zcount = sum(r.count(0) for r in mapIn)
    if zcount == 0:
        return mapIn
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
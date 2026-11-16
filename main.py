from typing import List

from sklearn.neural_network import MLPClassifier

import pygame
import random
# >>> REMOVED: import pandas as pd (no longer needed)
import numpy as np
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

    def get_encoding(self) -> int:
        if self.name == "North":
            return 1
        elif self.name == "East":
            return 2
        elif self.name == "South":
            return 3
        else:
            return 4

    @classmethod
    def get_direction(cls, num: int):
        if num == 1:
            return cls.North
        elif num == 2:
            return cls.East
        elif num == 3:
            return cls.South
        else:
            return cls.West


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
UPDATE_MS: int = 50

# >>> NEW: constants for the ML bot
DATA_FILE: str = "playstyle2.txt"
KEEP_STRAIGHT_PROB: float = 0.3   # keep only ~30% of "went straight" rows (balances data)
DROP_LAST_ROWS: int = 3           # drop the moves right before a crash (bad data)
MIN_TRAIN_ROWS: int = 200         # refuse to train on too little data
DIRS = [direction.North, direction.East, direction.South, direction.West]

# apple.png
SQUARE_SIZE: float = int((screen.get_width() - 2*MARGIN) / WIDTH)
APPLE_IMG: pygame.Surface = pygame.image.load("sprites/apple.png").convert_alpha()
APPLE_IMG = pygame.transform.scale(APPLE_IMG, (SQUARE_SIZE, SQUARE_SIZE))

HEAD_IMG: pygame.Surface = pygame.image.load("sprites/head_down.png").convert_alpha()
HEAD_IMG = pygame.transform.scale(HEAD_IMG, (SQUARE_SIZE, SQUARE_SIZE))
TAIL_IMG: pygame.Surface = pygame.image.load("sprites/tail_down.png").convert_alpha()
TAIL_IMG = pygame.transform.scale(TAIL_IMG, (SQUARE_SIZE, SQUARE_SIZE))
STRAIGHT_IMG: pygame.Surface = pygame.image.load("sprites/body_vertical.png").convert_alpha()
STRAIGHT_IMG = pygame.transform.scale(STRAIGHT_IMG, (SQUARE_SIZE, SQUARE_SIZE))
ELBOW_IMG: pygame.Surface = pygame.image.load("sprites/body_topright.png").convert_alpha()
ELBOW_IMG = pygame.transform.scale(ELBOW_IMG, (SQUARE_SIZE, SQUARE_SIZE))

pygame.display.set_caption("Snake")

# >>> NEW: fixed button rects so clicks can be detected in the event loop
playButton = pygame.Rect(screen.get_width()/2 - 50, screen.get_height()/2 - 50, 100, 70)
botButton = pygame.Rect(screen.get_width()/2 - 50, screen.get_height()/2 + 30, 100, 70)

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
episode_rows: List[str] = []   # >>> NEW: rows from the current game, saved when it ends

# >>> REMOVED: training_data DataFrame
# >>> CHANGED: hidden layers (10,10) -> (16,16)
mlp = MLPClassifier(hidden_layer_sizes=(16, 16),
                    max_iter=1000)

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
    global episode_rows        # >>> NEW
    episode_rows = []          # >>> NEW

# >>> NEW: turns the board into 10 numbers the MLP can learn from
def getFeatures(mapIn: List[List[int]], heading: direction) -> List[int]:
    # 4 danger flags (N/E/S/W), 2 apple direction signs, 4 heading one-hot
    hr, hc = next(((r, c) for r, row in enumerate(mapIn) for c, v in enumerate(row) if v == player_size), (0, 0))
    # hr, hc == coords of player head
    ar, ac = next(((r, c) for r, row in enumerate(mapIn) for c, v in enumerate(row) if v == -1), (hr, hc))
    # ar, ac == apple coords
    danger = []
    for d in DIRS: # dirs contains all cardinal directions as "direction" data type
        r, c = hr + d.value[0], hc + d.value[1]
        # r, c initialized to the location in the direction of d
        out = not (0 <= r < HEIGHT and 0 <= c < WIDTH)
        # out is initialized to 1 if there is "danger" in direction (death), 0 otherwise, aka out of bounds check
        danger.append(int(out or mapIn[r][c] > 1))
        # danger ends up as a length 4 list, 1 if there is danger in the direction 0 if it is free to move in
    apple = [int(np.sign(ar - hr)), int(np.sign(ac - hc))]
    # apple direction as list [row, column], either -1, 0, or 1 depending on where apple is located relative to player
    heading_onehot = [int(d == heading) for d in DIRS]
    # heading as onehot encoding

    return danger + apple + heading_onehot
    # list of training parameters
    # This will fail sometimes because the snake might think it is free to move in a direction but will trap itself,
    # consider the board
    # 0 > - v
    # a ^ 0 h
    # 0 ^ < 0
    # 0 0 ^ -
    #
    # - > v ^ all refer to directions and h is the head, a is the apple
    # Clearly to us, you need to go down because you will become trapped if you go left and going down is the
    # best option.
    # To the bot, it can not forsee this failure and will just go towards the apple since even with the perfect
    # playing data, this information will make left the optimal move.

# >>> NEW: writes a finished game's rows to disk, dropping the last few if it crashed
def saveEpisode(crashed: bool) -> None:
    rows = episode_rows[:-DROP_LAST_ROWS] if crashed else episode_rows
    if rows:
        with open(DATA_FILE, mode='a', newline='', encoding='utf-8') as file:
            file.write("\n".join(rows) + "\n")

# >>> NEW: loads data, checks size, trains once, returns True if the bot is ready
def trainBot() -> bool:
    try:
        data = np.loadtxt(DATA_FILE, ndmin=2)
    except (OSError, ValueError):
        print("No usable training data yet. Play first.")
        return False
    if len(data) < MIN_TRAIN_ROWS:
        print(f"Only {len(data)} rows, need at least {MIN_TRAIN_ROWS}. Play more games.")
        return False
    X, y = data[:, :-1], data[:, -1].astype(int)
    mlp.fit(X, y)
    print(f"trained on {len(data)} rows, accuracy: {mlp.score(X, y):.2f}")
    return True

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
                draw = getSnakePart(mapIn, column, row)
                screen.blit(pygame.transform.rotate(draw[0], -draw[1]), (MARGIN + column*squareWidth, MARGIN + row*squareHeight))

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
        # >>> NEW: menu clicks handled once per click (was: checked every frame in MENU)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state == gameState.MENU:
            if playButton.collidepoint(event.pos):
                state = gameState.PLAYING
                game_map = spawnApple(game_map)
            elif botButton.collidepoint(event.pos):
                if trainBot():
                    state = gameState.BOT
                    game_map = spawnApple(game_map)

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("green")

    if state == gameState.MENU:
        # >>> CHANGED: buttons only drawn here; click logic moved to the event loop above
        pygame.draw.rect(screen, "gray", playButton)
        play = TEXT.render("Play", True, "black")
        screen.blit(play, ((screen.get_width() - play.get_width()) / 2, (screen.get_height() - play.get_height()) / 2 - 16.5))

        pygame.draw.rect(screen, "gray", botButton)
        bot = TEXT.render("Bot", True, "black")
        screen.blit(bot, ((screen.get_width() - bot.get_width()) / 2, (screen.get_height() - bot.get_height()) / 2 + 63.5))
        # >>> REMOVED: old held-mouse check and pandas training loop (replaced by trainBot())

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

            # >>> NEW: heading BEFORE this move. Features use it, the label is the move you chose.
            prev_heading = direction((-player_from.value[0], -player_from.value[1]))
            turned = player_facing != prev_heading

            # >>> CHANGED: log features (not the raw map); keep all turns, some straight rows
            if turned or random.random() < KEEP_STRAIGHT_PROB:
                feats = getFeatures(game_map, prev_heading)
                episode_rows.append(" ".join(map(str, feats)) + f" {player_facing.get_encoding()}")

            player_from = direction((-player_facing.value[0], -player_facing.value[1]))

            game_map, gotApple, gameOver = updateMap(game_map, player_facing)
            if gameOver:
                saveEpisode(crashed=True)   # >>> NEW
                state = gameState.MENU
                resetGame()
                continue
            elif gotApple:
                player_size += 1
                score += 1


        drawMap(game_map)

        fps = TEXT.render(f"{clock.get_fps():.2f} fps", True, "black")
        screen.blit(fps, (screen.get_width() / 2 - fps.get_width() / 2, screen.get_height() - fps.get_height() - 2))

        scoreText = TEXT.render(f"Score: {score}", True, "black")
        screen.blit(scoreText, (screen.get_width() - scoreText.get_width() - 27, screen.get_height() - scoreText.get_height() - 2))


    elif state == gameState.BOT:
        dt = clock.tick(60)

        since_last_update_ms += dt
        if since_last_update_ms >= UPDATE_MS:

            since_last_update_ms = 0

            # >>> CHANGED: predict from features + current heading (was: raw flattened map)
            pred = mlp.predict([getFeatures(game_map, player_facing)])[0]
            moveDir = direction.get_direction(pred)
            if moveDir != player_from:
                player_facing = moveDir
            # else: bot tried to reverse, keep going the same way

            player_from = direction((-player_facing.value[0], -player_facing.value[1]))

            game_map, gotApple, gameOver = updateMap(game_map, player_facing)
            if gameOver:
                print(f"Bot final score: {score}")   # >>> NEW
                state = gameState.MENU
                resetGame()
                continue
            elif gotApple:
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
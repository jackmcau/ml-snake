# Runs the MLP bot headless (no window) many times and reports average score.
# Usage: python benchmark.py [games]    (run in the folder with playstyle.txt)
import sys, random
import numpy as np
from enum import Enum
from sklearn.neural_network import MLPClassifier

HEIGHT = WIDTH = 15
GAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 100
MAX_STEPS_NO_APPLE = 300

class direction(Enum):
    North = (-1, 0)
    East = (0, 1)
    South = (1, 0)
    West = (0, -1)

DIRS = [direction.North, direction.East, direction.South, direction.West]
player_size = 3

def spawnApple(m):
    empty = [(r, c) for r in range(HEIGHT) for c in range(WIDTH) if m[r][c] == 0]
    if empty:
        r, c = random.choice(empty)
        m[r][c] = -1
    return m

def updateMap(m, towards):
    hr, hc = next((r, c) for r, row in enumerate(m) for c, v in enumerate(row) if v == player_size)
    nr, nc = hr + towards.value[0], hc + towards.value[1]
    if not (0 <= nr < HEIGHT and 0 <= nc < WIDTH):
        return m, False, True
    if m[nr][nc] == -1:
        m[nr][nc] = player_size + 1
        return spawnApple(m), True, False
    if m[nr][nc] > 1:
        return m, False, True
    out = [[(i - 1 if i > 0 else i) for i in row] for row in m]
    out[nr][nc] = player_size
    return out, False, False

def getFeatures(m, heading):
    hr, hc = next(((r, c) for r, row in enumerate(m) for c, v in enumerate(row) if v == player_size), (0, 0))
    ar, ac = next(((r, c) for r, row in enumerate(m) for c, v in enumerate(row) if v == -1), (hr, hc))
    danger = []
    for d in DIRS:
        r, c = hr + d.value[0], hc + d.value[1]
        out = not (0 <= r < HEIGHT and 0 <= c < WIDTH)
        danger.append(int(out or m[r][c] > 1))
    apple = [int(np.sign(ar - hr)), int(np.sign(ac - hc))]
    return danger + apple + [int(d == heading) for d in DIRS]

def playGame(model):
    global player_size
    m = [[0] * WIDTH for _ in range(HEIGHT)]
    for i in range(3):
        m[HEIGHT // 2][i + 2] = i + 1
    player_size = 3
    m = spawnApple(m)
    heading = direction.East
    score = since_apple = 0
    while True:
        move = DIRS[model.predict([getFeatures(m, heading)])[0] - 1]
        if move.value != (-heading.value[0], -heading.value[1]):   # ignore reverse moves
            heading = move
        m, got, dead = updateMap(m, heading)
        if dead:
            return score, True
        if got:
            player_size += 1
            score += 1
            since_apple = 0
        else:
            since_apple += 1
            if since_apple > MAX_STEPS_NO_APPLE:   # stuck in a loop
                return score, False

data = np.loadtxt("playstyle.txt", ndmin=2)
X, y = data[:, :-1], data[:, -1].astype(int)
model = MLPClassifier(hidden_layer_sizes=(16, 16), max_iter=1000).fit(X, y)
print(f"trained on {len(X)} rows, accuracy {model.score(X, y):.3f}")

scores, crashes = [], 0
for g in range(GAMES):
    s, crashed = playGame(model)
    scores.append(s)
    crashes += crashed
print(f"{GAMES} games | avg {np.mean(scores):.2f} | median {np.median(scores):.0f} | "
      f"min {min(scores)} | max {max(scores)} | std {np.std(scores):.2f} | crashed {crashes}/{GAMES}")

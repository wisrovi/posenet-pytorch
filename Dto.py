class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class KeyPoint_Poses:
    def __init__(self, part, x, y, score):
        self.part = part
        pos = Position(x, y)
        self.position = pos
        self.score = score
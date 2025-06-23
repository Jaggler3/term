class Vec:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def add(self, x: int, y: int):
        self.x += x
        self.y += y

    def sub(self, x: int, y: int):
        self.x -= x
        self.y -= y

    def __sub__(self, other: "Vec") -> "Vec":
        return Vec(self.x - other.x, self.y - other.y)

    def __add__(self, other: "Vec") -> "Vec":
        return Vec(self.x + other.x, self.y + other.y)


def cloneVec(vec: Vec) -> Vec:
    return Vec(vec.x, vec.y)


def addVec(v1: Vec, v2: Vec) -> Vec:
    return Vec(v1.x + v2.x, v1.y + v2.y)


def equalsVec(v1: Vec, v2: Vec) -> bool:
    return v1.x == v2.x and v1.y == v2.y

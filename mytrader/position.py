class Position:
    def __init__(self):
        self.size = 0.0
    def __bool__(self):
        return self.size != 0

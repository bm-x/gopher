class TimeNode:
    def __init__(self, time, captureInterval, foundDelay):
        self.time = time
        self.captureInterval = captureInterval
        self.foundDealy = foundDelay


class Slice:
    def __init__(self, fileName, name):
        self.fileName = fileName
        self.name = name
        self.width = None
        self.height = None
        self.img = None
        self.centerX = None
        self.centerY = None
        self.covertName = None

from picamzero import Camera

class CameraSensor:
    def __init__(self):
        self.camera = Camera()

    def capture(self, filename):
        self.camera.capture(filename)

    def close(self):
        self.camera.close()

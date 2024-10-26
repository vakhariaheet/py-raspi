from picamzero import Camera

class CameraSensor:
    def __init__(self):
        self.camera = Camera()

    def capture(self, filename):
        # self.camera.start_preview();
        self.camera.take_photo(filename);
        # self.camera.stop_preview();
    

    def close(self):
        self.camera.close()

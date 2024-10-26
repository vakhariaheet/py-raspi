from picamzero import Camera
import pygame;

class CameraSensor:
    def __init__(self):
        self.camera = Camera()

    def capture(self, filename):
        # self.camera.start_preview();
        self.camera.take_photo(filename);
        sound = pygame.mixer.Sound("../assets/sfx/camera.mp3");
        sound.play();
        # self.camera.stop_preview();
    

    def close(self):
        self.camera.close()

from rpi_ws281x import *

class TideLightLedStrip(PixelStrip):
    
    def _Green(self):
        return Color(0, 255,0)
    
    
    def _Red(self):
        return Color(255, 0, 0)
    
    
    def _Off(self):
        return Color(0, 0, 0)

    def _Blue(self):
        return Color(0, 0, 255)

    def _Purple(self):
        return Color(128,0,128)
    
    
    def update_tide_leds(self, led_number, direction):
        if direction:
            self.setPixelColor(0, self._Off())
            self.setPixelColor(self.numPixels() - 1, self._Green())
            for i in range(1, led_number + 1):
                self.setPixelColor(i, self._Blue())
            for i in range(led_number + 1, self.numPixels() - 1):
                self.setPixelColor(i, self._Purple())
        else:
            self.setPixelColor(0, self._Red())
            self.setPixelColor(self.numPixels() - 1, self._Off())
            for i in range(1, self.numPixels() - led_number):
                self.setPixelColor(i, self._Blue())
            for i in range(self.numPixels() - led_number, self.numPixels() - 1):
                self.setPixelColor(i, self._Purple())
        self.show()

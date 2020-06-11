from Config import Config
import ast

class ThreadManagerConfigBinding(Config):
    def __init__(self, thread_manager):
        super().__init__()
        self.thread_manager = thread_manager

    def setLatLon(self, lat, lon):
        new_lat, new_lon = super().setLatLon(lat, lon)
        self.thread_manager.change_lat_lon(new_lat, new_lon)

    def setBrightness(self, brightness):
        new_brightness = super().setBrightness(brightness)
        self.thread_manager.change_brightness(new_brightness)

    def setLdrActive(self, active):
        new_active = super().setLdrActive(active)
        self.thread_manager.change_ldr_active(new_active)

    def setHighTideDirectionColor(self, color):
        new_color = super().setHighTideDirectionColor(color)
        self.thread_manager.change_high_tide_direction_color(new_color)

    def setLowTideDirectionColor(self, color):
        new_color = super().setLowTideDirectionColor(color)
        self.thread_manager.change_high_tide_direction_color(new_color)

    def setTideLevelIndicatorColor(self, color):
        new_color = super().setTideLevelIndicatorColor(color)
        self.thread_manager.change_tide_level_indicator_color(new_color)

    def setNoTideLevelIndicatorColor(self, color):
        new_color = super().setNoTideLevelIndicatorColor(color)
        self.thread_manager.change_no_tide_level_indicator_color(new_color)

    def setTideLevelIndicatorMovingColor(self, colors):
        new_colors = super().setTideLevelIndicatorMovingColor(colors)
        self.thread_manager.change_tide_level_indicator_moving_color(new_colors)

    def setNoTideLevelIndicatorMovingColor(self, colors):
        new_colors = super().setNoTideLevelIndicatorMovingColor(colors)
        self.thread_manager.change_no_tide_level_indicator_moving_color(new_colors)

    def setMovingPattern(self, movingPattern):
        new_moving_pattern = super().setMovingPattern(movingPattern)
        self.thread_manager.change_moving_pattern(new_moving_pattern)

    def setMovingSpeed(self, movingSpeed):
        new_moving_speed = super().setMovingSpeed(movingSpeed)
        self.thread_manager.change_moving_speed(new_moving_speed)
    
    def setMovingPattern(self, movingPattern):
        new_moving_pattern = super().setMovingPattern(movingPattern)
        self.thread_manager.change_moving_pattern(new_moving_pattern)
    
    def setOfflineMode(self, mode):
        new_mode = super().setOfflineMode(mode)
        self.thread_manager.change_offline_mode(ast.literal_eval(mode))
    
    def updateOfflineData(self):
        self.thread_manager.update_offline_data()
    
    def reset(self):
        super().reset()
        self.thread_manager.reset()
        
        


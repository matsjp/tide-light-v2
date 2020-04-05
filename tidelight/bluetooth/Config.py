import configparser
import ast
import re
from kartverket_tide_api import TideApi
from kartverket_tide_api.parsers import LocationDataParser
from datetime import datetime
from datetime import timedelta

configPath = 'config.ini'

ldrStates = {
    0x1: 'True',
    0x2: 'False'
    }

colorFormats = {
    0x1: 'rgb',
    0x2: 'bgr'
    }

movingPatterns = {
    0x1: 'wave'
    }

offlineModeStates = {
    0x1: 'True',
    0x2: 'False'
    }

class Config():
    def __init__(self):
        pass
        
    
    def getLatLon(self):
        config = self._getConfig()
        lat = config.get('apivalues', 'lat')
        lon = config.get('apivalues', 'lon')
        return lat, lon
        
        
    def setLatLon(self, lat, lon):
        if type(lat) is not int and type(lat) is not float and type(lon) is not int and type(lon) is not float:
            raise ValueError('lat and lon must be int or float')
        if not self.validateLatLon(lat, lon):
            raise ValueError()
        config = self._getConfig()
        config.set('apivalues', 'lat', str(lat))
        config.set('apivalues', 'lon', str(lon))
        self.writeConfig(config)
        return lat, lon
    
    
    def getBrightness(self):
        config = self._getConfig()
        return config.get('ledstrip', 'LED_BRIGHTNESS')
    
    def setBrightness(self, brightness):
        if type(brightness) is not int:
            raise ValueError('brightness must be an int')
        if brightness < 0 or brightness > 255:
            raise ValueError('brightness must be between 0 and 255')
        config = self._getConfig()
        config.set('ledstrip', 'LED_BRIGHTNESS', str(brightness))
        self.writeConfig(config)        
        return brightness
    
    def getLdrActive(self):
        config = self._getConfig()
        return config.get('ldr', 'ldr_active')
    
    def setLdrActive(self, active):
        if active != 'True' and active != 'False':
            raise ValueError('active must be "True" or "False"')
        config = self._getConfig()
        config.set('ldr', 'ldr_active', active)
        self.writeConfig(config)
        return active
    
    def getColorFormat(self):
        config = self._getConfig()
        return config.get('color', 'color_format')
    
    def setColorFormat(self, colorFormat):
        if colorFormat != 'rgb' and colorFormat != 'bgr':
            raise ValueError('colorFormat must be rgb or bgr')
        config = self._getConfig()
        config.set('color', 'color_format', colorFormat)
        self.writeConfig(config)
        return colorFormat
    
    def getHighTideDirectionColor(self):
        config = self._getConfig()
        return config.get('color', 'high_tide_direction_color')
    
    def setHighTideDirectionColor(self, color):
        if not self.validateColor(color):
            raise ValueError('Invalid color format')
        config = self._getConfig()
        config.set('color', 'high_tide_direction_color', color)
        self.writeConfig(config)
        return color
    
    def getLowTideDirectionColor(self):
        config = self._getConfig()
        return config.get('color', 'low_tide_direction_color')
    
    def setLowTideDirectionColor(self, color):
        if not self.validateColor(color):
            raise ValueError('Invalid color format')
        config = self._getConfig()
        config.set('color', 'low_tide_direction_color', color)
        self.writeConfig(config)
        return color
    
    def getTideLevelIndicatorColor(self):
        config = self._getConfig()
        return config.get('color', 'tide_level_indicator_color')
    
    def setTideLevelIndicatorColor(self, color):
        if not self.validateColor(color):
            raise ValueError('Invalid color format')
        config = self._getConfig()
        config.set('color', 'tide_level_indicator_color', color)
        self.writeConfig(config)
        return color
    
    def getNoTideLevelIndicatorColor(self):
        config = self._getConfig()
        return config.get('color', 'no_tide_level_indicator_color')
    
    def setNoTideLevelIndicatorColor(self, color):
        if not self.validateColor(color):
            raise ValueError('Invalid color format')
        config = self._getConfig()
        config.set('color', 'no_tide_level_indicator_color', color)
        self.writeConfig(config)
        return color
    
    def getTideLevelIndicatorMovingColor(self):
        config = self._getConfig()
        return config.get('color', 'tide_level_indicator_moving_color')
    
    def setTideLevelIndicatorMovingColor(self, colors):
        if not self.validateColors(colors):
            raise ValueError('Invalid color format')
        config = self._getConfig()
        config.set('color', 'tide_level_indicator_moving_color', colors)
        self.writeConfig(config)
        return colors
    
    def getNoTideLevelIndicatorMovingColor(self):
        config = self._getConfig()
        return config.get('color', 'no_tide_level_indicator_moving_color')
    
    def setNoTideLevelIndicatorMovingColor(self, colors):
        if not self.validateColors(colors):
            raise ValueError('Invalid color format')
        config = self._getConfig()
        config.set('color', 'no_tide_level_indicator_moving_color', colors)
        self.writeConfig(config)
        return colors
    
    def getMovingPattern(self):
        config = self._getConfig()
        return config.get('color', 'moving_pattern')
    
    def setMovingPattern(self, movingPattern):
        if movingPattern != 'wave':
            raise ValueError('movingPattern must be wave')
        config = self._getConfig()
        config.set('color', 'moving_pattern', movingPattern)
        self.writeConfig(config)
        return movingPattern
    
    
    def getMovingSpeed(self):
        config = self._getConfig()
        return config.get('color', 'moving_speed')
    
    def setMovingSpeed(self, movingSpeed):
        if type(movingSpeed) is not int and type(movingSpeed) is not float:
            raise ValueError('movingSpeed must be int or float')
        if movingSpeed <= 0:
            raise ValueError('movingSpeed must be above 0')
        config = self._getConfig()
        config.set('color', 'moving_speed', str(movingSpeed))
        self.writeConfig(config)
        return movingSpeed
    
    def getOfflineMode(self):
        config = self._getConfig()
        return config.get('offline', 'offline_mode')
    
    def setOfflineMode(self, mode):
        if mode != 'True' and mode != 'False':
            raise ValueError('mode must be "True" or "False"')
        config = self._getConfig()
        config.set('offline', 'offline_mode', mode)
        self.writeConfig(config)
        return mode
    
    def validateColor(self, color):
        regex = '^\[([0-9]|[1-8][0-9]|9[0-9]|1[0-9]{'\
'2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-9]'\
'{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-9'\
']{2}|2[0-4][0-9]|25[0-5])\]$'
        return re.match(regex, color)
        
    
    def validateColors(self, colors):
        regex = '^\[(\[([0-9]|[1-8][0-9]|9[0-9]|1[0-9]'\
'{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-9'\
']{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-'\
'9]{2}|2[0-4][0-9]|25[0-5])\],)*\[([0-9]|[1-8][0-9]|9[0-'\
'9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0'\
'-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9['\
'0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\]\]$|^\[\]$'
        return re.match(regex, colors)
    
    def validateLatLon(self, lat, lon):
        try:
            api = TideApi()
            timeFrom = (datetime.now() + timedelta(days=-1)).strftime("%Y-%m-%dT%H:%M")
            timeTo = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M")
            response = api.get_location_data(lon, lat, timeFrom, timeTo, 'TAB')
            parser = LocationDataParser(response)
            parser.parse_response()
            return True
        except Exception as e:
            print('Validate error')
            print(e)
            return False
        
    
    def _getConfig(self):
        config = configparser.ConfigParser()
        config.read(configPath)
        return config
    
    def writeConfig(self, config):
        with open(configPath, 'w') as configfile:
            config.write(configfile)
        
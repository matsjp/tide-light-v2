import ast
import re
import logging

from kartverket_tide_api import TideApi
from kartverket_tide_api.parsers import LocationDataParser

from util import *

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
    0x1: 'wave',
    0x2: 'regular'
}


class Config():
    def __init__(self):
        if not self.configExists():
            self.defaultConfig()
        if not self.validateConfig():
            self.defaultConfig()

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
        return str(lat), str(lon)

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
        return ast.literal_eval(active)

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
        if movingPattern not in list(movingPatterns.values()):
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



    def validateColor(self, color):
        regex = '^\[([0-9]|[1-8][0-9]|9[0-9]|1[0-9]{' \
                '2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-9]' \
                '{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-9' \
                ']{2}|2[0-4][0-9]|25[0-5])\]$'
        return re.match(regex, color)

    def validateColors(self, colors):
        regex = '^\[(\[([0-9]|[1-8][0-9]|9[0-9]|1[0-9]' \
                '{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-9' \
                ']{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-' \
                '9]{2}|2[0-4][0-9]|25[0-5])\],)*\[([0-9]|[1-8][0-9]|9[0-' \
                '9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0' \
                '-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[' \
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
            logging.error('Validate error')
            logging.exception(e)
            return False

    def _getConfig(self):
        config = configparser.ConfigParser()
        config.read(configPath)
        return config

    def writeConfig(self, config):
        with open(configPath, 'w') as configfile:
            config.write(configfile)
    
    def configExists(self):
        return os.path.exists(configPath)

    def defaultConfig(self):
        apivalues = {
            'lat': '59.908',
            'lon': '10.734'
        }
        ledstrip = {
            'led_count': '60',
            'led_pin': '18',
            'led_freq_hz': '800000',
            'led_dma': '10',
            'led_brightness': '100',
            'led_invert': 'False',
            'led_channel': '0'
        }
        ldr = {
            'ldr_pin': '11',
            'ldr_active': 'True'
        }
        color = {
            'color_format': 'rgb',
            'high_tide_direction_color': '[24,255,4]',
            'low_tide_direction_color': '[255,0,0]',
            'tide_level_indicator_color': '[0,0,255]',
            'no_tide_level_indicator_color': '[128,0,128]',
            'tide_level_indicator_moving_color': '[[255,105,115],[255,159,176],[100,100,255]]',
            'no_tide_level_indicator_moving_color': '[[91,73,255],[73,164,255],[73,255,255]]',
            'moving_pattern': 'wave',
            'moving_speed': '0.5',
        }
        config = configparser.ConfigParser()
        config['apivalues'] = apivalues
        config['ledstrip'] = ledstrip
        config['ldr'] = ldr
        config['color'] = color

        config.write(open(configPath, 'w+'))
    
    
    
    def reset(self):
        self.defaultConfig()
        if os.path.exists('offline.xml'):
            os.remove('offline.xml')
    
    def getLEDConstants(self):
        config = self._getConfig()
        LED_COUNT = ast.literal_eval(config.get('ledstrip', 'LED_COUNT'))
        LED_PIN = ast.literal_eval(config.get('ledstrip', 'LED_PIN'))
        LED_FREQ_HZ = ast.literal_eval(config.get('ledstrip', 'LED_FREQ_HZ'))
        LED_DMA = ast.literal_eval(config.get('ledstrip', 'LED_DMA'))
        LED_BRIGHTNESS = ast.literal_eval(config.get('ledstrip', 'LED_BRIGHTNESS'))
        LED_INVERT = ast.literal_eval(config.get('ledstrip', 'LED_INVERT'))
        LED_CHANNEL = ast.literal_eval(config.get('ledstrip', 'LED_CHANNEL'))
        return LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_BRIGHTNESS, LED_INVERT, LED_CHANNEL
    
    def getLDRPin(self):
        config = self._getConfig()
        return ast.literal_eval(config.get('ldr', 'ldr_pin'))
        
    
    def validateConfig(self):
        #TODO: test this
        #TODO: handle all possible exceptions
        regex_color_list = '^\[(\[([0-9]|[1-8][0-9]|9[0-9]|1[0-9]' \
                   '{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-9' \
                   ']{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-' \
                   '9]{2}|2[0-4][0-9]|25[0-5])\],)*\[([0-9]|[1-8][0-9]|9[0-' \
                   '9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0' \
                   '-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[' \
                       '0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\]\]$|^\[\]$'
        
        # Regex that is used to validate a single color
        # Format is [123,255,12]
        # Is a single rgb color
        regex_single_color = '^\[([0-9]|[1-8][0-9]|9[0-9]|1[0-9]{' \
                             '2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-9]' \
                             '{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-9' \
                             ']{2}|2[0-4][0-9]|25[0-5])\]$'

        config = configparser.ConfigParser()
        config.read(configPath)
        lon = config.get('apivalues', 'lon')
        lat = config.get('apivalues', 'lat')

        LED_COUNT = ast.literal_eval(config.get('ledstrip', 'LED_COUNT'))
        LED_PIN = ast.literal_eval(config.get('ledstrip', 'LED_PIN'))
        LED_FREQ_HZ = ast.literal_eval(config.get('ledstrip', 'LED_FREQ_HZ'))
        LED_DMA = ast.literal_eval(config.get('ledstrip', 'LED_DMA'))
        LED_BRIGHTNESS = ast.literal_eval(config.get('ledstrip', 'LED_BRIGHTNESS'))
        LED_INVERT = ast.literal_eval(config.get('ledstrip', 'LED_INVERT'))
        LED_CHANNEL = ast.literal_eval(config.get('ledstrip', 'LED_CHANNEL'))

        ldr_pin = ast.literal_eval(config.get('ldr', 'ldr_pin'))
        ldr_active = ast.literal_eval(config.get('ldr', 'ldr_active'))


        # TODO: make excaptions for all these possible errors
        color_format = config.get('color', 'color_format')
        if color_format not in ['rgb', 'bgr']:
            logging.error('Color_format must be "rgb" or "bgr"')
            exit()
        high_tide_direction_color_string = config.get('color', 'high_tide_direction_color')
        if not re.match(regex_single_color, high_tide_direction_color_string):
            logging.error('high_tide_direction_color must have the following format: [23,43,34] where' \
                  'the digit is between 0 and 255')
            return False
        htdc_list = json.loads(high_tide_direction_color_string)

        low_tide_direction_color_string = config.get('color', 'low_tide_direction_color')
        if not re.match(regex_single_color, low_tide_direction_color_string):
            logging.error('low_tide_direction_color must have the following format: [23,43,34] where' \
                  'the digit is between 0 and 255')
            return False
        ltdc_list = json.loads(low_tide_direction_color_string)

        tide_level_indicator_color_string = config.get('color', 'tide_level_indicator_color')
        if not re.match(regex_single_color, tide_level_indicator_color_string):
            logging.error('tide_level_indicator_color must have the following format: [23,43,34] where' \
                  'the digit is between 0 and 255')
            return False
        tlic_list = json.loads(tide_level_indicator_color_string)

        no_tide_level_indicator_color_string = config.get('color', 'no_tide_level_indicator_color')
        if not re.match(regex_single_color, no_tide_level_indicator_color_string):
            logging.error('no_tide_level_indicator_color must have the following format: [23,43,34] where' \
                  'the digit is between 0 and 255')
            return False
        ntlic_list = json.loads(no_tide_level_indicator_color_string)

        tide_level_indicator_moving_color_string = config.get('color', 'tide_level_indicator_moving_color')
        if not re.match(regex_color_list, tide_level_indicator_moving_color_string):
            logging.error('tide_level_indicator_moving_color must have the following format: [[23,43,34],[13,255,1]] etc where' \
                  'the digit is between 0 and 255')
            return False
        tlimc_list = json.loads(tide_level_indicator_moving_color_string)

        no_tide_level_indicator_moving_color_string = config.get('color', 'no_tide_level_indicator_moving_color')
        if not re.match(regex_color_list, no_tide_level_indicator_moving_color_string):
            logging.error('no_tide_level_indicator_moving_color must have the following format: [[23,43,34],[13,255,1]] etc where' \
                  'the digit is between 0 and 255')
            return False
        ntlimc_list = json.loads(no_tide_level_indicator_moving_color_string)

        if len(ntlimc_list) != len(tlimc_list):
            logging.error('The number of rgbs in each moving tide indicator must be equal')
            return False

        if color_format == 'rgb':
            high_tide_direction_color = Color(htdc_list[0], htdc_list[1], htdc_list[2])
            low_tide_direction_color = Color(ltdc_list[0], ltdc_list[1], ltdc_list[2])
            tide_level_indicator_color = Color(tlic_list[0], tlic_list[1], tlic_list[2])
            no_tide_level_indicator_color = Color(ntlic_list[0], ntlic_list[1], ntlic_list[2])

            tide_level_indicator_moving_colors = []
            for color in tlimc_list:
                tide_level_indicator_moving_colors.append(Color(color[0], color[1], color[2]))
            no_tide_level_indicator_moving_colors = []
            for color in ntlimc_list:
                no_tide_level_indicator_moving_colors.append(Color(color[0], color[1], color[2]))
        else:
            high_tide_direction_color = Color(htdc_list[2], htdc_list[1], htdc_list[0])
            low_tide_direction_color = Color(ltdc_list[2], ltdc_list[1], ltdc_list[0])
            tide_level_indicator_color = Color(tlic_list[2], tlic_list[1], tlic_list[0])
            no_tide_level_indicator_color = Color(ntlic_list[2], ntlic_list[1], ntlic_list[0])

            tide_level_indicator_moving_colors = []
            for color in tlimc_list:
                tide_level_indicator_moving_colors.append(Color(color[2], color[1], color[0]))
            no_tide_level_indicator_moving_colors = []
            for color in ntlimc_list:
                no_tide_level_indicator_moving_colors.append(Color(color[2], color[1], color[0]))

        moving_speed = ast.literal_eval(config.get('color', 'moving_speed'))
        moving_pattern = config.get('color', 'moving_pattern')
        if moving_pattern not in ['no', 'wave', 'regular']:
            logging.error('moving_pattern must be no, wave or regular')
            return False

        if (moving_pattern in ['wave', 'regular'] and
                (len(tide_level_indicator_moving_colors) == 0
                 or len(no_tide_level_indicator_moving_colors) == 0)):
            logging.error('For moving patterns you need colors. They cannot be []')
            return False
        return True

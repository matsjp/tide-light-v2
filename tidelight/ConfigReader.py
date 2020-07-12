import configparser
import ast
import json
import re
from rpi_ws281x import *
"""TODO:
Confirm that file is not in use anywhere and delete"""
from util import configExists, defaultConfig

if not configExists():
    defaultConfig()
# Regex that is used to validate the list of colors
# Format is [[45,23,56],[1,12,255]] etc
# List of lists containing rgb color
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
config.read('config.ini')
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

offline_mode = ast.literal_eval(config.get('offline', 'offline_mode'))

# TODO: make excaptions for all these possible errors
color_format = config.get('color', 'color_format')
if color_format not in ['rgb', 'bgr']:
    print('Color_format must be "rgb" or "bgr"')
    exit()
high_tide_direction_color_string = config.get('color', 'high_tide_direction_color')
if not re.match(regex_single_color, high_tide_direction_color_string):
    print('high_tide_direction_color must have the following format: [23,43,34] where' \
          'the digit is between 0 and 255')
    exit()
htdc_list = json.loads(high_tide_direction_color_string)

low_tide_direction_color_string = config.get('color', 'low_tide_direction_color')
if not re.match(regex_single_color, low_tide_direction_color_string):
    print('low_tide_direction_color must have the following format: [23,43,34] where' \
          'the digit is between 0 and 255')
    exit()
ltdc_list = json.loads(low_tide_direction_color_string)

tide_level_indicator_color_string = config.get('color', 'tide_level_indicator_color')
if not re.match(regex_single_color, tide_level_indicator_color_string):
    print('tide_level_indicator_color must have the following format: [23,43,34] where' \
          'the digit is between 0 and 255')
    exit()
tlic_list = json.loads(tide_level_indicator_color_string)

no_tide_level_indicator_color_string = config.get('color', 'no_tide_level_indicator_color')
if not re.match(regex_single_color, no_tide_level_indicator_color_string):
    print('no_tide_level_indicator_color must have the following format: [23,43,34] where' \
          'the digit is between 0 and 255')
    exit()
ntlic_list = json.loads(no_tide_level_indicator_color_string)

tide_level_indicator_moving_color_string = config.get('color', 'tide_level_indicator_moving_color')
if not re.match(regex_color_list, tide_level_indicator_moving_color_string):
    print('tide_level_indicator_moving_color must have the following format: [[23,43,34],[13,255,1]] etc where' \
          'the digit is between 0 and 255')
    exit()
tlimc_list = json.loads(tide_level_indicator_moving_color_string)

no_tide_level_indicator_moving_color_string = config.get('color', 'no_tide_level_indicator_moving_color')
if not re.match(regex_color_list, no_tide_level_indicator_moving_color_string):
    print('no_tide_level_indicator_moving_color must have the following format: [[23,43,34],[13,255,1]] etc where' \
          'the digit is between 0 and 255')
    exit()
ntlimc_list = json.loads(no_tide_level_indicator_moving_color_string)

if len(ntlimc_list) != len(tlimc_list):
    print('The number of rgbs in each moving tide indicator must be equal')
    exit()

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
    print('moving_pattern must be no, wave or regular')
    exit()

if (moving_pattern in ['wave', 'regular'] and
        (len(tide_level_indicator_moving_colors) == 0
         or len(no_tide_level_indicator_moving_colors) == 0)):
    print('For moving patterns you need colors. They cannot be []')
    exit()
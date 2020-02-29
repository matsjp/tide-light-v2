# flo-og-fj-re-lys-v2

# Config file

```
[apivalues]
lat=59.908559
lon=10.73451
```

```lat```: the latitude where you want tide data from.

```lon```: the longitude where you want tide data from.

The combination of lat and lon must be a geographic area where the Kartverket tide api can get data from.

```
[ledstrip]
LED_COUNT=60
LED_PIN=18
LED_FREQ_HZ=800000
LED_DMA=10
LED_BRIGHTNESS=50
LED_INVERT=False
LED_CHANNEL=0
```

```LED_COUNT```: the amount of addressable LEDs on the strip

```LED_PIN```: the GPIO pin connected to the LED strip

```LED_FREQ_HZ```: don't touch, leave at ```800000```

```LED_DMA```: don't touch, leave at ```10```

```LED_BRIGHTNESS```: the brightness of the LEDs. Must be a number between ```0``` and ```255```

```LED_INVERT```: don't touch, leave at ```False```

```LED_CHANNEL```: don't touch, leave at ```0```

```
[ldr]
ldr_pin=11
ldr_active=False
```

```ldr_pin```: the GPIO pin connected to the ldr
```ldr_active```: if the light auto dim should be active or not. ```True``` to make it active, ```False``` to make it inactive

```
[color]
color_format=rgb
high_tide_direction_color=[0,255,0]
low_tide_direction_color=[255,0,0]
tide_level_indicator_color=[0,0,255]
no_tide_level_indicator_color=[128,0,128]
tide_level_indicator_moving_color=[[255,73,115],[255,159,176],[100,100,255]]
no_tide_level_indicator_moving_color=[[91,73,255],[73,164,255],[73,255,255]]
moving_pattern=wave
moving_speed=0.5
```

```color_format```: the color format used by the LED strip. Can be rgb or bgr

```high_tide_direction_color```: the color of the top LED when water is moving towards high tide. Color is RGB or BGR depending on ```color_format``` and must follow this format ```[N,N,N]``` where ```N``` is a number between ```0``` and ```255```

```low_tide_direction_color```: the color of the bottom LED when the water is moving towards low tide. Color is RGB or BGR depending on ```color_format``` and must follow this format ```[N,N,N]``` where ```N``` is a number between ```0``` and ```255```

```tide_level_indicator_color```: the color of the LEDs showing where the tide currently is. These are the bottom LEDs. Color is RGB or BGR depending on ```color_format``` and must follow this format ```[N,N,N]``` where ```N``` is a number between ```0``` and ```255```

```no_tide_level_indicator_color```: the color of the LEDs showing where the tide currently isn't. These are the top LEDs. Color is RGB or BGR depending on ```color_format``` and must follow this format ```[N,N,N]``` where ```N``` is a number between ```0``` and ```255```

```tide_level_indicator_moving_color```: the color of the LEDS moving accross the LEDs indicating where the tide currently is.

```no_tide_level_indicator_moving_color```: the color of the LEDS moving accross the LEDs indicating where the tide currently isn't.

```tide_level_indicator_moving_color``` and ```no_tide_level_indicator_moving_color``` colors are RGB or BGR depending on ```color_format```. Both need to follow the following format ```[[N,N,N],[N,N,N],[N,N,N]]``` where N is a number between ```0``` and ```255```. ```[N,N,N]``` is the RGB value of a single LED. The number of LEDs in ```tide_level_indicator_moving_color``` and ```no_tide_level_moving_color``` must be equal

```moving_pattern```: the pattern of the moving colors. ```wave```: makes the LEDs move across like a wave

```moving_speed```: the moving speed of the LEDs. The number is amount of seconds between each LED movement

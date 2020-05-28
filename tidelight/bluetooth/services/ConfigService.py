from pybleno import *
from bluetooth.characteristics.configcharacteristics.BrightnessCharacteristic import BrightnessCharacteristic
from bluetooth.characteristics.configcharacteristics.LdrActiveCharacteristic import LdrActiveCharacteristic
from bluetooth.characteristics.configcharacteristics.ColorFormatCharacteristic import ColorFormatCharacteristic
from bluetooth.characteristics.configcharacteristics.HighTideDirectionColorCharacteristic import HighTideDirectionColorCharacteristic
from bluetooth.characteristics.configcharacteristics.LowTideDirectionColorCharacteristic import LowTideDirectionColorCharacteristic
from bluetooth.characteristics.configcharacteristics.TideLevelIndicatorColorCharacteristic import TideLevelIndicatorColorCharacteristic
from bluetooth.characteristics.configcharacteristics.NoTideLevelIndicatorColorCharacteristic import NoTideLevelIndicatorColorCharacteristic
from bluetooth.characteristics.configcharacteristics.TideLevelIndicatorMovingColorCharacteristic import TideLevelIndicatorMovingColorCharacteristic
from bluetooth.characteristics.configcharacteristics.NoTideLevelIndicatorMovingColorCharacteristic import NoTideLevelIndicatorMovingColorCharacteristic
from bluetooth.characteristics.configcharacteristics.MovingPatternCharacteristic import MovingPatternCharacteristic
from bluetooth.characteristics.configcharacteristics.MovingSpeedCharacteristic import MovingSpeedCharacteristic
from bluetooth.characteristics.configcharacteristics.LatLonCharacteristic import LatLonCharacteristic
from bluetooth.characteristics.configcharacteristics.ResetCharacteristic import ResetCharacteristic

class ConfigService(BlenoPrimaryService):
    uuid = 'ec00'
    def __init__(self, config):
        BlenoPrimaryService.__init__(self, {
          'uuid': 'ec00',
          'characteristics': [
            BrightnessCharacteristic(config),
            LdrActiveCharacteristic(config),
            ColorFormatCharacteristic(config),
            HighTideDirectionColorCharacteristic(config),
            LowTideDirectionColorCharacteristic(config),
            TideLevelIndicatorColorCharacteristic(config),
            NoTideLevelIndicatorColorCharacteristic(config),
            TideLevelIndicatorMovingColorCharacteristic(config),
            NoTideLevelIndicatorMovingColorCharacteristic(config),
            MovingPatternCharacteristic(config),
            MovingSpeedCharacteristic(config),
            LatLonCharacteristic(config),
            ResetCharacteristic(config)
          ]})
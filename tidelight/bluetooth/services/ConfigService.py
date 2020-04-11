from pybleno import *
from tidelight.bluetooth.characteristics.configcharacteristics.BrightnessCharacteristic import BrightnessCharacteristic
from tidelight.bluetooth.characteristics.configcharacteristics.LdrActiveCharacteristic import LdrActiveCharacteristic
from tidelight.bluetooth.characteristics.configcharacteristics.ColorFormatCharacteristic import ColorFormatCharacteristic
from tidelight.bluetooth.characteristics.configcharacteristics.HighTideDirectionColorCharacteristic import HighTideDirectionColorCharacteristic
from tidelight.bluetooth.characteristics.configcharacteristics.LowTideDirectionColorCharacteristic import LowTideDirectionColorCharacteristic
from tidelight.bluetooth.characteristics.configcharacteristics.TideLevelIndicatorColorCharacteristic import TideLevelIndicatorColorCharacteristic
from tidelight.bluetooth.characteristics.configcharacteristics.NoTideLevelIndicatorColorCharacteristic import NoTideLevelIndicatorColorCharacteristic
from tidelight.bluetooth.characteristics.configcharacteristics.TideLevelIndicatorMovingColorCharacteristic import TideLevelIndicatorMovingColorCharacteristic
from tidelight.bluetooth.characteristics.configcharacteristics.NoTideLevelIndicatorMovingColorCharacteristic import NoTideLevelIndicatorMovingColorCharacteristic
from tidelight.bluetooth.characteristics.configcharacteristics.MovingPatternCharacteristic import MovingPatternCharacteristic
from tidelight.bluetooth.characteristics.configcharacteristics.MovingSpeedCharacteristic import MovingSpeedCharacteristic
from tidelight.bluetooth.characteristics.configcharacteristics.LatLonCharacteristic import LatLonCharacteristic

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
            LatLonCharacteristic(config)
          ]})
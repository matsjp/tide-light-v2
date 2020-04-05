from pybleno import *
from .BrightnessCharacteristic import BrightnessCharacteristic
from .LdrActiveCharacteristic import LdrActiveCharacteristic
from .ColorFormatCharacteristic import ColorFormatCharacteristic
from .HighTideDirectionColorCharacteristic import HighTideDirectionColorCharacteristic
from .LowTideDirectionColorCharacteristic import LowTideDirectionColorCharacteristic
from .TideLevelIndicatorColorCharacteristic import TideLevelIndicatorColorCharacteristic
from .NoTideLevelIndicatorColorCharacteristic import NoTideLevelIndicatorColorCharacteristic
from .TideLevelIndicatorMovingColorCharacteristic import TideLevelIndicatorMovingColorCharacteristic
from .NoTideLevelIndicatorMovingColorCharacteristic import NoTideLevelIndicatorMovingColorCharacteristic
from .MovingPatternCharacteristic import MovingPatternCharacteristic
from .MovingSpeedCharacteristic import MovingSpeedCharacteristic
from .LatLonCharacteristic import LatLonCharacteristic

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
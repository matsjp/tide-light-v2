from pybleno import *
from ..characteristics.BrightnessCharacteristic import BrightnessCharacteristic
from ..characteristics.LdrActiveCharacteristic import LdrActiveCharacteristic
from ..characteristics.ColorFormatCharacteristic import ColorFormatCharacteristic
from ..characteristics.HighTideDirectionColorCharacteristic import HighTideDirectionColorCharacteristic
from ..characteristics.LowTideDirectionColorCharacteristic import LowTideDirectionColorCharacteristic
from ..characteristics.TideLevelIndicatorColorCharacteristic import TideLevelIndicatorColorCharacteristic
from ..characteristics.NoTideLevelIndicatorColorCharacteristic import NoTideLevelIndicatorColorCharacteristic
from ..characteristics.TideLevelIndicatorMovingColorCharacteristic import TideLevelIndicatorMovingColorCharacteristic
from ..characteristics.NoTideLevelIndicatorMovingColorCharacteristic import NoTideLevelIndicatorMovingColorCharacteristic
from ..characteristics.MovingPatternCharacteristic import MovingPatternCharacteristic
from ..characteristics.MovingSpeedCharacteristic import MovingSpeedCharacteristic
from ..characteristics.LatLonCharacteristic import LatLonCharacteristic

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
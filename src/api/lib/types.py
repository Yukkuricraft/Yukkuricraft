from enum import Enum

class ConfigType(Enum):
    PLUGIN = 'plugin'
    MOD = 'mod'

    # Because luckperms is weird and puts half of its generated files in /data/mods instead of /data/configs :-/
    MOD_FILES = 'modfiles'

    @staticmethod
    def from_str(label) -> 'ConfigType':
        if label == 'plugin':
            return ConfigType.PLUGIN
        elif label == 'mod':
            return ConfigType.MOD
        elif label == 'modfiles':
            return ConfigType.MOD_FILES
        else:
            raise NotImplementedError
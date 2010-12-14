import os

from JSI.ProviderToolbox.conf import default_settings

ENV_VAR = "PROVTOOL_SETTINGS"

class Settings():

    def __init__(self):
        self.conf = None

    def __getattr__(self, name):
        if self.conf is None:
            # Delayed initialization
            self.__import_settings()
        return getattr(self.conf, name)

    def __setattr__(self, name, value):
        if name == 'conf':
            # Treat conf differently to avoid infinite loop
            self.__dict__['conf'] = value
        else:
            if self.conf is None:
                self.__import_settings()
            setattr(self.conf, name, value)

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __import_settings(self):
        i = ImportConfig()
        self.conf = i.getConfig()

    def updateMediaRoot(self, newRoot):
        if self.conf is None:
            self.__import_settings()
        _oldRoot = self.__getitem__("MEDIA_ROOT")
        for setting in dir(self.conf):
            if setting == setting.upper():
                _value = str(self.__getitem__(setting))
                if _value.startswith(_oldRoot):
                    _value = _value.replace(_oldRoot, newRoot, 1)
                    setattr(self, setting, _value)

    def list(self):
        if self.conf is None:
            self.__import_settings()
        out = ""
        for setting in dir(self.conf):
            if setting == setting.upper():
                out += setting + " = " + str(self.__getitem__(setting)) + "\n"
        return out

class ImportConfig():

    def __init__(self):
        self.config = None
        try:
            myConfig = os.environ[ENV_VAR]
        except KeyError:
            myConfig = None
        # Variable set but empty
        if myConfig == "":
            myConfig = None
        if myConfig != None:
            myConfigFile = myConfig + ".py"
            myConfigPath = os.path.join(os.path.dirname(__file__), myConfigFile)
            assert os.path.isfile(myConfigPath), "Specified config file " + myConfigPath + " does not exist!" 
            module = "JSI.ProviderToolbox.conf." + myConfig
            self.config = self.myImport(module)
        else:
            self.config = default_settings

    def getConfig(self):
        self.updateConfig(self.config)
        # Store where the settings were loaded from
        setattr(self, "SETTINGS", self.config)
        setattr(self, "SETTINGS_NAME", self.config.__name__)
        return self

    def updateConfig(self, conf):
        for setting in dir(conf):
            # Only upper case attributes are considered as settings
            if setting == setting.upper():
                setattr(self, setting, getattr(conf, setting))

    def myImport(self, name):
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod

settings = Settings()


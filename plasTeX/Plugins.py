
import importlib
import os
import sys
import traceback

# the following is required while there are still installations
# of "old" Pythons
if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

from plasTeX.Logging import getLogger

pluginLog = getLogger('plugin.loading')

def listInstalledPlastexPlugins():
    knownPlugins = []
    for anEntryPoint in entry_points(group='plastex.plugin'):
        knownPlugins.append(anEntryPoint.value)
    return knownPlugins

def runPlastexPluginConfig(config, methodName,
    texStream=None, texDocument=None
):
    for aPlugin in entry_points(group='plastex.plugin'):
        configFilePath = None
        for aFilePath in aPlugin.dist.files:
            aFilePath = '.'.join(aFilePath.parts)
            #
            # We explicitly prefer a new style `'ConfigPlasTeXPlugin.py`
            # to the old style `Renderers/<Name>/Config.py`
            #
            # IF there are both, then the new style `addConfig(config)`
            # should explicitly call the old style `addConfig(config)`
            #
            # This allows all PlasTeX plugins to (re)configure their
            # environment before any parsing takes place.
            #
            if 'ConfigPlasTeXPlugin.py' in aFilePath:
                configFilePath = aFilePath.replace('.py', '')
                break
            if 'Config.py' in aFilePath:
                configFilePath = aFilePath.replace('.py', '')
        if not configFilePath:
            continue
        try:
            conf = importlib.import_module(configFilePath)
        except Exception:
            print(f"Failed to load {configFilePath}:")
            print(traceback.format_exc(limit=-1))
            print("  ignoring plugin")
            continue

        if hasattr(conf, methodName) and \
           callable(getattr(conf, methodName)):
            if methodName == 'updateCommandLineOptions' or \
               methodName == 'initPlugin' :
              pluginLog.info(f"Running {methodName} from: {configFilePath}")
            elif 'PLASTEX_LOG_PLUGIN_LOADING' in os.environ:
              print(f"Running {methodName} from: {configFilePath}")
            try:
                theMethod = getattr(conf, methodName)
                if methodName == 'initPlugin' :
                    theMethod(config, texStream, texDocument)
                else:
                    theMethod(config)

            except Exception:
                print(f"Failed to run {methodName} from {configFilePath}:")
                print(traceback.format_exc(limit=-1))
                print("  ignoring plugin")

def addPlugins(data) :
    knownPlugins = listInstalledPlastexPlugins()
    if not data['plugins']:
        data['plugins'] = [knownPlugins]
    else:
        # NOTE: not sure why the extra `[0]` is needed...
        # but it seems that the argparse data places lists inside a list.
        data['plugins'][0].extend(knownPlugins)
    knownPlugins = listInstalledPlastexPlugins()
    pluginLog.info(f"Added PlasTeX plugins: {knownPlugins} ")

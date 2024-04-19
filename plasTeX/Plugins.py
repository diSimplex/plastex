
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

# We use a simple module level singleton to discover and sort all plugins
# found in the `plastex.plugin` group of entry points

# Each entry point in the `plastex.plugin` group can have an optional
# float appended after a ':'. The default float is '50'. The
# discovered plugins are sorted in ascending order by this optional float
# value. (lowest floats will be loaded first; equal floats will then be
# loaded in lexigraphical order).

unsortedPlugins = []
entryPoints = {}
for anEntryPoint in entry_points(group='plastex.plugin'):
    anEPvalue = anEntryPoint.value
    anEPlist = []
    if ':' in anEPvalue:
        fields = anEPvalue.split(':')
        anEPlist = [float(fields[1]), fields[0]]
    else:
        anEPlist = [50.0, anEPvalue]
    unsortedPlugins.append(anEPlist)
    entryPoints[anEPlist[1]] = anEntryPoint

discoveredPlugins = []
for aPlugin in sorted(unsortedPlugins):
    discoveredPlugins.append(aPlugin[1])


def runPlastexPluginConfig(config, methodName,
                           fileName=None, texStream=None, texDocument=None
                           ):
    for aPlugin in discoveredPlugins:
        configFilePath = None
        for aFilePath in entryPoints[aPlugin].dist.files:
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
            if methodName == 'initPlugin' or methodName == 'updateConfig':
                pluginLog.info(f"Running {methodName} from: {configFilePath}")
            elif 'PLASTEX_LOG_PLUGIN_LOADING' in os.environ:
                print(f"Running {methodName} from: {configFilePath}")
            try:
                theMethod = getattr(conf, methodName)
                if methodName == 'initPlugin':
                    theMethod(config, fileName, texStream, texDocument)
                elif methodName == 'updateConfig' :
                    theMethod(config, fileName)
                else:
                    theMethod(config)

            except Exception:
                print(f"Failed to run {methodName} from {configFilePath}:")
                print(traceback.format_exc(limit=-1))
                print("  ignoring plugin")


def addPlugins(config):
    pluginList = []
    for aPlugin in discoveredPlugins:
        pluginList.append(aPlugin)
    # wrapping the pluginList in another list is required by the
    # updateFromDict method
    config.updateFromDict({'plugins' : [pluginList] })
    pluginLog.info(f"Added PlasTeX plugins: {config['general']['plugins']} ")


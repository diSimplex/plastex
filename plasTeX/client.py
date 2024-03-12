#!/usr/bin/env python3

import os, sys
import importlib

# the following is required while there are still installations
# of "old" Pythons
if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

import traceback, pdb
import plasTeX
from plasTeX import __version__
from argparse import ArgumentParser
from plasTeX.Logging import getLogger, updateLogLevels
from plasTeX.Compile import run
from plasTeX.Config import defaultConfig

log = getLogger()
pluginLog = getLogger('plugin.loading')

def convertLoggingListToDict(loggingList):
  loggingDict = {}
  for i in range(len(loggingList)):
    loggingDict[loggingList[i][0]] = loggingList[i][1]
  return loggingDict

def list_installed_plastex_plugins():
    knownPlugins = []
    for anEntryPoint in entry_points(group='plastex.plugin'):
        knownPlugins.append(anEntryPoint.value)
    return knownPlugins

def run_plastex_plugin_config(config, methodName, logUsable=False):
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
            if logUsable:
              pluginLog.info(f"Running {methodName} from: {configFilePath}")
            else:
              print(f"Running {methodName} from: {configFilePath}")
            try:
                theMethod = getattr(conf, methodName)
                theMethod(config)
            except Exception:
                print(f"Failed to run {methodName} from {configFilePath}:")
                print(traceback.format_exc(limit=-1))
                print("  ignoring plugin")

def collect_renderer_config(config):
    plastex_dir = os.path.dirname(os.path.realpath(plasTeX.__file__))
    renderers_dir = os.path.join(plastex_dir, 'Renderers')
    renderers = next(os.walk(renderers_dir))[1]
    for renderer in renderers:
        try:
            conf = importlib.import_module('plasTeX.Renderers.'+renderer+'.Config')
        except ImportError as msg:
            continue

        conf.addConfig(config)

def main(argv):
    """ Main program routine """
    print('plasTeX version %s' % __version__)

    config = defaultConfig()
    collect_renderer_config(config)
    run_plastex_plugin_config(config, 'addConfig')

    parser = ArgumentParser("plasTeX")

    group = parser.add_argument_group("External Configuration Files")
    group.add_argument("--config", "-c", dest="config", help="Config files to load. Non-existent files are silently ignored", action="append")

    config.registerArgparse(parser)

    parser.add_argument("file", help="File to process")

    data = parser.parse_args(argv)
    data = vars(data)
    if data["config"] is not None:
        config.read(data["config"])

    # We reproduce this call here to allow logging to take place as soon
    # as possible (even before the (La)TeX files are parsed)
    updateLogLevels(convertLoggingListToDict(data['logging']))

    if data['add-plugins'] :
        knownPlugins = list_installed_plastex_plugins()
        if not data['plugins']:
            data['plugins'] = [knownPlugins]
        else:
            # NOTE: not sure why the extra `[0]` is needed...
            # but it seems that the argparse data places lists inside a list.
            data['plugins'][0].extend(knownPlugins)

    run_plastex_plugin_config(data, 'updateCommandLineOptions', True)

    config.updateFromDict(data)

    if data['add-plugins'] :
        knownPlugins = list_installed_plastex_plugins()
        pluginLog.info(f"Added PlasTeX plugins: {knownPlugins} ")

    run_plastex_plugin_config(config, 'initPlugin', True)

    filename = data["file"]

    run(filename, config)

def info(type, value, tb):
   if hasattr(sys, 'ps1') or not sys.stderr.isatty():
      # we are in interactive mode or we don't have a tty-like
      # device, so we call the default hook
      sys.__excepthook__(type, value, tb)
   else:
      # we are NOT in interactive mode, print the exception...
      traceback.print_exception(type, value, tb)
      print()
      # ...then start the debugger in post-mortem mode.
      pdb.pm()

#sys.excepthook = info

#sys.setrecursionlimit(10000)

def plastex():
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        pass

import os
import sys

initfilepath = os.path.abspath(__file__)
pluginDir = os.path.dirname(initfilepath)
SourceDir = os.path.join(pluginDir, "src")
unrealLibDir = os.path.join(pluginDir, "vendor", "unrealSDK")

def AddDirToPath(dir):
    if dir not in sys.path:
        sys.path.append(dir)
        print(f"added{dir} to path")

AddDirToPath(pluginDir)
AddDirToPath(SourceDir)
AddDirToPath(unrealLibDir)
    
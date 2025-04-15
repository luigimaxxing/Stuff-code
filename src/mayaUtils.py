import maya.cmds as mc
import maya.OpenMayaUI as omui # this imports maya's open maya ui module, it can help finding the maya main window
import shiboken2 # this helps with converting the maya main window to the pyside type
 
from PySide2.QtWidgets import QMainWindow, QWidget
from PySide2.QtCore import Qt # this has some values we can use to configure our widget, like their windowType, or orientation
 
def GetMayaMainWindow()->QMainWindow:
    mayaMainWindow = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(mayaMainWindow), QMainWindow)
 
def DeleteWindowWithName(name):
    for window in GetMayaMainWindow().findChildren(QWidget, name):
        window.deleteLater()
 
class QMayaWindow(QWidget):
    def __init__(self):
        DeleteWindowWithName(self.GetWindowHash())
        super().__init__(parent = GetMayaMainWindow())
        self.setWindowFlags(Qt.WindowType.Window)
        self.setObjectName(self.GetWindowHash())
       
 
    def GetWindowHash(self):
        return "sdsdfhsdfisdfnsdsdwerisdhfakl213hradfhafafjai"
 
 
def IsMesh(obj):
    shapes = mc.listRelatives(obj, s=True)
    if not shapes:
        return False
 
    for s in shapes:
        if mc.objectType(s) == "mesh":
            return True
 
    return False
 
def IsSkin(obj):
    return mc.objectType(obj) == "skinCluster"
 
def IsJoint(obj):
    return mc.objectType(obj) == "joint"
 
def GetUpperStream(obj):
    return mc.listConnections(obj, s=True, d=False, sh=True)
 
def GetLowerStream(obj):
    return mc.listConnections(obj, s=False, d=True, sh=True)
 
def GetAllConnectIn(obj, NextFunc, searchDepth = 10, Filter = None):
    AllFound = set()
    nexts = NextFunc(obj)
    while nexts and searchDepth > 0:
        for next in nexts:
            AllFound.add(next)
 
        nexts = NextFunc(nexts)
        if nexts:
            nexts = [x for x in nexts if x not in AllFound]
 
        searchDepth -= 1
 
    if not Filter:
        return list(AllFound)
 
    filterd = []
    for found in AllFound:
        if Filter(found):
            filterd.append(found)
 
    return filterd
 
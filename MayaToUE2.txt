import os
from mayaUtils import *
from PySide2.QtCore import Signal
from PySide2.QtGui import QIntValidator, QRegExpValidator
from PySide2.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget
import maya.cmds as mc
from mayaUtils import IsJoint, IsMesh, QMayaWindow
import mayatools
import remote_execution


def TryAction(action):
    def wrapper(*args, **kwargs):
        try: 
            action(*args, **kwargs)
        except Exception as e:
            QMessageBox().critical(None, "Error", f"{e}")

    return wrapper

# Data oriented class
class AnimClip:
    def __init__(self):
        self.subfix = ""
        self.frameMin = mc.playbackOptions(q=True, min=True) 
        self.frameMax = mc.playbackOptions(q=True, max=True)
        self.shouldExport = True

class MayaToUE:
    def __init__(self):
        self.rootJnt = ""
        self.meshes = []
        self.animationClips: list[AnimClip] = []
        self.fileName = ""
        self.saveDir = ""
        self.scale = 1.0  

    def SetScale(self, scaleStr):
        try:
            scale = float(scaleStr)
            if scale <= 0:
                raise ValueError("Scale must be positive.")
            self.scale = scale
        except ValueError:
            raise Exception("Invalid scale value. Please enter a valid number.")

    def GetAllJoints(self):
        jnts = [self.rootJnt]
        children = mc.listRelatives(self.rootJnt, c=True, ad=True, type="joint")
        if children:
            jnts.extend(children)
        return jnts

    def SaveFiles(self):
        allJnts = self.GetAllJoints()
        allMeshes = self.meshes
        allObjectToExport = allJnts + allMeshes
        mc.select(allObjectToExport, r=True)

        skeletalMeshExportPath = self.GetSkeletalMeshSavePath()

        mc.FBXResetExport()
        mc.FBXExportSmoothingGroups('-v', True)
        mc.FBXExportInputConnections('-v', False)
        mc.FBXExportScaleFactor('-v', self.scale)  # Apply scale

        mc.FBXExport('-f', skeletalMeshExportPath, '-s', True, '-ea', False)

        os.makedirs(self.GetAnimDirPath(), exist_ok=True)
        mc.FBXExportBakeComplexAnimation('-v', True)

        for animClip in self.animationClips:
            if not animClip.shouldExport:
                continue
            animExportPath = self.GetSavePathForAnimClip(animClip)
            startFrame = animClip.frameMin
            endFrame = animClip.frameMax
            mc.FBXExportBakeComplexStart('-v', startFrame)
            mc.FBXExportBakeComplexEnd('-v', endFrame)
            mc.FBXExportBakeComplexStep('-v', 1)
            mc.playbackOptions(e=True, min=startFrame, max=endFrame)
            mc.FBXExport('-f', animExportPath, '-s', True, '-ea', True)

        self.SendToUnreal()


class MayaToUEWidget(QMayaWindow):
    def GetWindowHash(self):
        return "MayaToUEJL4172025745"

    def __init__(self):
        super().__init__()
        self.mayaToUE = MayaToUE()
        self.setWindowTitle("Maya to UE")

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.rootJntText = QLineEdit()
        self.rootJntText.setEnabled(False)
        self.masterLayout.addWidget(self.rootJntText)

        setSelectionAsRootJntBtn = QPushButton("Set Root Joint")
        setSelectionAsRootJntBtn.clicked.connect(self.SetSelectionAsRootJointBtnClicked)
        self.masterLayout.addWidget(setSelectionAsRootJntBtn)

        addRootJntBtn = QPushButton("Add Root Joint")
        addRootJntBtn.clicked.connect(self.AddRootJntButtonClicked)
        self.masterLayout.addWidget(addRootJntBtn)

        self.meshList = QListWidget()
        self.masterLayout.addWidget(self.meshList)
        self.meshList.setFixedHeight(80)

        addMeshBtn = QPushButton("Add Meshes")
        addMeshBtn.clicked.connect(self.AddMeshBtnClicked)
        self.masterLayout.addWidget(addMeshBtn)

        addNewAnimClipEntryBtn = QPushButton("Add Animation Clip")
        addNewAnimClipEntryBtn.clicked.connect(self.AddNewAnimClipEntryBtnClicked)
        self.masterLayout.addWidget(addNewAnimClipEntryBtn)

        self.animEntryLayout = QVBoxLayout()
        self.masterLayout.addLayout(self.animEntryLayout)

        self.saveFileLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.saveFileLayout)

        fileNameLabel = QLabel("File Name: ")
        self.saveFileLayout.addWidget(fileNameLabel)

        self.fileNameLineEdit = QLineEdit()
        self.fileNameLineEdit.setFixedWidth(80)
        self.fileNameLineEdit.setValidator(QRegExpValidator("\w+"))
        self.fileNameLineEdit.textChanged.connect(self.FileNameLineEditChanged)
        self.saveFileLayout.addWidget(self.fileNameLineEdit)

        self.directoryLabel = QLabel("Save Directory: ")
        self.saveFileLayout.addWidget(self.directoryLabel)
        self.saveDirectoryLineEdit = QLineEdit()
        self.saveDirectoryLineEdit.setEnabled(False)
        self.saveFileLayout.addWidget(self.saveDirectoryLineEdit)
        self.pickDirBtn = QPushButton("...")
        self.pickDirBtn.clicked.connect(self.PickDirBtnClicked)
        self.saveFileLayout.addWidget(self.pickDirBtn)

        scaleLayout = QHBoxLayout()
        scaleLabel = QLabel("Export Scale:")
        self.scaleEdit = QLineEdit()
        self.scaleEdit.setValidator(QIntValidator(1, 10000))
        self.scaleEdit.setFixedWidth(60)
        self.scaleEdit.setText("1")
        self.scaleEdit.textChanged.connect(self.ScaleEditChanged)
        scaleLayout.addWidget(scaleLabel)
        scaleLayout.addWidget(self.scaleEdit)
        self.masterLayout.addLayout(scaleLayout)

        self.savePreviewLabel = QLabel("")
        self.masterLayout.addWidget(self.savePreviewLabel)

        saveFileBtn = QPushButton("Save Files")
        saveFileBtn.clicked.connect(self.SaveFilesBtnClicked)
        self.masterLayout.addWidget(saveFileBtn)

    def SaveFilesBtnClicked(self):
        self.mayaToUE.SaveFiles()

    def UpdateSavePreviewLabel(self):
        preivewText = self.mayaToUE.GetSkeletalMeshSavePath()
        if not self.mayaToUE.animationClips:
            self.savePreviewLabel.setText(preivewText)
            return
        for animClip in self.mayaToUE.animationClips:
            animSavePath = self.mayaToUE.GetSavePathForAnimClip(animClip)
            preivewText += "\n" + animSavePath
        self.savePreviewLabel.setText(preivewText)

    @TryAction
    def PickDirBtnClicked(self):
        path = QFileDialog().getExistingDirectory()
        self.saveDirectoryLineEdit.setText(path)
        self.mayaToUE.saveDir = path
        self.UpdateSavePreviewLabel()

    @TryAction
    def FileNameLineEditChanged(self, newText):
        self.mayaToUE.fileName = newText
        self.UpdateSavePreviewLabel()

    @TryAction
    def ScaleEditChanged(self, text):
        self.mayaToUE.SetScale(text)

    @TryAction
    def AddNewAnimClipEntryBtnClicked(self):
        newEntry = self.mayaToUE.AddNewAnimEntry()
        newEntryWidget = AnimClipEntryWidget(newEntry)
        newEntryWidget.entryRemoved.connect(self.AnimClipEntryRemoved)
        newEntryWidget.entrySubfixChanged.connect(lambda x: self

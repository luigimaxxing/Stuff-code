import importlib
import mayaUtils
importlib.reload(mayaUtils)
from mayaUtils import *
from PySide2.QtWidgets import QPushButton, QVBoxLayout
import maya.cmds as mc



class ProxyRigger:
    def __init__(self):
        self.skin = ""
        self.model = ""
        self.joints = ""

    def CreateProxyRigFromSelectedMesh(self):
        mesh = mc.ls(sl=True)[0]
        if not IsMesh(mesh):
            raise TypeError(f"{mesh} is not a mesh, select a mesh")
        
        self.model = mesh
        modelShape = mc.listRelatives(self.model, s=True)[0]
        print(f"found mesh {mesh} and shape {modelShape}")

        skin = GetAllConnectIn(modelShape, GetUpperStream, 10, IsSkin)
        if not skin:
            raise Exception(f"{mesh} no skin")
        self.skin = skin[0]

        jnts = GetAllConnectIn(modelShape, GetUpperStream, IsJoint)
        if not jnts:
            raise Exception(f"{mesh} no joint bound")
        self.jnts = jnts

        print(f"start build with mesh:{self.model}, skin: {self.skin} and joints: {self.jnts}")

        jntVertMap = self.GenerateJntVertDict()
        segments = []
        ctrls = []
        for jnt, verts in jntVertMap.items():
            print(f"joint{jnt} controls {verts} primarily")
            newSeg = self.CreateProxyModelForJntsAndVerts(jnt, verts)
            if newSeg is None:
                continue

            newSkinCluster = mc.skinCluster(self.jnts, newSeg)[0]
            mc.copySkinWeights(ss=self.skin, ds=newSkinCluster, nm=True, sa="closestPoint", ia="closestJoint")
            segments.append(newSeg)

            ctrlLocator = "ac_" + jnt + "_proxy"
            mc.spaceLocator(n=ctrlLocator)
            ctrlLocatorGrp = ctrlLocator + "_grp"
            mc.group(ctrlLocator, n=ctrlLocatorGrp)
            mc.matchTransform(ctrlLocatorGrp, jnt)

            visibilityAttr = "vis"
            mc.addAttr(ctrlLocator, ln=visibilityAttr, min=0, max=1, dv=1, k=True)
            mc.connectAttr(ctrlLocator + "." + visibilityAttr, newSeg + ".v")
            ctrls.append(ctrlLocatorGrp)

        proxyTopGrp = self.model + "_proxy_grp"
        mc.group(segments, n=proxyTopGrp)

        ctrlTopGrp = "ac_" + self.model + "_proxy_grp"
        mc.group(ctrls, n=ctrlTopGrp)

        globalProxyCtrl = "ac_" +self.model + "_proxy_global"
        mc.circle(n=globalProxyCtrl, r=30)
        mc.parent(proxyTopGrp, globalProxyCtrl)
        mc.parent(ctrlTopGrp, globalProxyCtrl)
        mc.setAttr(proxyTopGrp + ".inheritsTransform", 0)

        visibilityAttr = "vis"
        mc.addAttr(globalProxyCtrl, ln= visibilityAttr, min=0, max=1, dv=1, k=True)
        mc.connectAttr(globalProxyCtrl + "."+ visibilityAttr,proxyTopGrp + ".v")
        

    def CreateProxyModelForJntsAndVerts(self, jnt, verts):
        if not verts:
            return None
        
        faces = mc.polyListComponentConversion(verts, fromVertex=True, toFace=True)
        faces = mc.ls(faces, fl=True)

        labels = set()
        for face in faces:
            labels.add(face.replace(self.model,""))

        dup = mc.duplicate(self.model)[0]

        allDupFaces = mc.ls(f"{dup}.f[*]", fl=True)
        facesToDelete = []
        for dupFace in allDupFaces:
            label = dupFace.replace(dup, "")
            if label not in labels:
                facesToDelete.append(dupFace)

        mc.delete(facesToDelete)

        dupName = self.model + "_" + jnt + "_proxy"
        mc.rename(dup, dupName)
        return dupName

    def GenerateJntVertDict(self):
        dict = {}
        for jnt in self.jnts:
            dict[jnt] = []

        verts = mc.ls(f"{self.model}.vtx[*]", fl=True)
        for vert in verts:
            owningJnt = self.GetJntWithMaxInfluence(vert, self.skin)
            dict[owningJnt].append(vert)

        return dict

        def GetJntWithMaxInfluence(self, vert, skin):
            weights = mc.skinPresent(skin, vert, q=True, v=True)
            jnts = mc.skinPercent(skin, vert, q=True, t=None)

            maxWeightIndex = 0
            maxWeight = weights[0]

            for i in range(1, len(weights)):
                if weights[i] > maxWeight:
                    maxWeight = weights[i]
                    maxWeightIndex = i

            return jnts[maxWeightIndex]
        

class ProxyRiggerWidget(QMayaWindow):
    def __init__(self):
        super().__init__()
        self.proxyRigger = ProxyRigger
        self.setWindowTitle("Proxy Rigger")
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)
        generateProxyRigBtn = QPushButton("generate proxy rig")
        self.masterLayout.addWidget(generateProxyRigBtn)
        generateProxyRigBtn.clicked.connect(self.GenerateProxyRigButtonClicked)

    def GenerateProxyRigButtonClicked(self):
        self.proxyRigger.CreateProxyRigFromSelectedMesh()
        

    def GetWindowHash(self):
        return "meowmeowmeoew32v058hdf8349g57f9qhbdf2bcn905g8f22dp90jkjfs5390tjgksdldgj5je0"
    
ProxyRiggerWidget = ProxyRiggerWidget()
ProxyRiggerWidget.show()
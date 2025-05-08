import os
import unreal

def CreateBaseImportTask(importPath):
    importTask = unreal.AssetImportTask()
    importTask.filename = importPath

    fileName = os.path.basename(importPath).split(".")[0]
    importTask.destination_path = '/Game/' + fileName
    importTask.automated = True
    importTask.save = True
    importTask.replace_existing = True

    return importTask

def importSkeletalMesh(meshPath):
    importTask = CreateBaseImportTask(meshPath)

    importOption = unreal.FbxImportUI()
    importOption.import_mesh = True
    importOption.import_as_skeletal = True

    importOption.skeletal_mesh_import_data.set_editor_property('import_morph_targets', True)

    importOption.skeletal_mesh_import_data.set_editor_property('use_t0_as_ref_pose', True)

    importTask.options = importOption

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([importTask])  

    #for imported in importTask.get_objects():
       #pathName = imported.get_path_name()
       #importedData = unreal.EditorAssetLibrary.find_asset_data(pathName)
       #assertClass = importedData.get_class()
       #if assertClass == unreal.SkeletalMesh:
          #return imported
       
    return importTask.get_objects([-1])

def ImportAnimation(mesh: unreal.SkeletalMesh, animPath):
    importTask = CreateBaseImportTask(animPath)
    meshDir = os.path.dirname(mesh.get_path_name())
    importTask.destination_path = meshDir + "/animations"

    importOptions = unreal.FbxImportUI()
    importOptions.import_mesh = False
    importOptions.import_as_skeletal = True
    importOptions.import_animations = True
    importOptions.skeleton = mesh.skeleton

    importOptions.set_editor_property('automated_import_should_detect_type', False)
    importOptions.set_editor_property('original_import_type', unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    importOptions.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)

    importTask.options = importOptions

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([importTask])

def importMeshAndAnimation(meshPath, animDir):
   mesh =  importSkeletalMesh(meshPath)
   for filename in os.listdir(animDir):
    if ".fbx" in filename:
        animPath = os.path.join(animDir, filename)
        ImportAnimation(mesh, animPath)


importMeshAndAnimation("d:/profile redirect/tmwilso1/Desktop/Maya/mayaToUe/alex.fbx", "d:/profile redirect/tmwilso1/Desktop/Maya/mayaToUe/animations")
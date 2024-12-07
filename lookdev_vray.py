#lookdev_vray.py

import json
import maya.cmds as cmds

"""
Purpose:
To recieve the set designs from the Blender artists in a quick and easy manner.

How:
The user will open the FBX exported from Blender into their Maya scene
The user will import the JSON file that exported with the Blender lookdev
This JSON file contains data on which material is assigned to each mesh
The FBX comes with default materials (phongs) attached for shading. But we hate that lol
Based on the JSON data, the textures will be reassigned to VRAY materials (for Pedro)

The JSON structure is like so:
{
    "MeshName": {
        "MaterialName": {
            "ChannelName": "TexturePath",
            "ChannelName": "TexturePath",
            "ChannelName": "TexturePath",
            "ChannelName": "TexturePath",
        }
    }
}

For reference, the channel names coming from Blender are:
Base Color
Metallic
Roughness
IOR
Transmission
Transmission Roughness
Specular
Specular Tint
Anisotropic 
Anisotropic Rotation
Subsurface
Subsurface Radius
Subsurface Color
Clearcoat
Clearcoat Roughness
Sheen
Sheen Tint
Emission
Alpha
Normal

"""


BSDF_TO_VRAY = {
    "Base Color": "diffuse",
    "Metallic": "metalness", 
    "Roughness": "reflection_glossiness",
    "IOR": "refraction_ior",
    "Transmission": "refraction_weight",
    "Transmission Roughness": "refraction_glossiness",
    "Specular": "reflection_weight",
    "Specular Tint": "reflection_color",
    "Anisotropic": "anisotropy",
    "Anisotropic Rotation": "anisotropy_rotation",
    "Subsurface": "sss_weight",
    "Subsurface Radius": "sss_radius",
    "Subsurface Color": "sss_color",
    "Normal": "bump_map"
}


class LookdevVray:
    def __init__(self, json_file):
        self.json_file = json_file

    def import_json(self):
        with open(self.json_file, 'r') as file:
            self.json_data = json.load(file)

        return self.json_data

    def parse_json(self):
        for mesh_name, material_data in self.json_data.items():
            for material_name, channel_data in material_data.items():
                for channel_name, texture_path in channel_data.items():
                    print(f"Mesh: {mesh_name}, Material: {material_name}, Channel: {channel_name}, Texture: {texture_path}")
                    self.assign_textures(mesh_name, material_name, channel_name, texture_path)

    def assign_textures(self, mesh_name, material_name, channel_name, texture_path):
        # Skip if the channel isn't mapped to a VRay attribute
        if channel_name not in BSDF_TO_VRAY:
            return

        # Create or get the VRay material
        vray_material = f"VRayMtl_{material_name}"
        if not cmds.objExists(vray_material):
            vray_material = cmds.shadingNode('VRayMtl', asShader=True, name=vray_material)
            # Create shading group
            sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=f"{vray_material}SG")
            cmds.connectAttr(f'{vray_material}.outColor', f'{sg}.surfaceShader')
            # Assign material to mesh
            cmds.sets(mesh_name, edit=True, forceElement=sg)

        # Create file texture node
        file_node = cmds.shadingNode('file', asTexture=True, name=f"{material_name}_{BSDF_TO_VRAY[channel_name]}_tex")
        cmds.setAttr(f"{file_node}.fileTextureName", texture_path, type="string")
        
        # Get the corresponding VRay attribute
        vray_attr = BSDF_TO_VRAY[channel_name]
        
        # Connect based on whether the attribute needs single channel or RGB
        single_channel_attrs = ['metalness', 'reflection_glossiness', 'refraction_weight', 
                              'refraction_glossiness', 'reflection_weight', 'anisotropy', 
                              'anisotropy_rotation', 'sss_weight']
        
        if vray_attr in single_channel_attrs:
            cmds.connectAttr(f'{file_node}.outColorR', f'{vray_material}.{vray_attr}')
        else:
            cmds.connectAttr(f'{file_node}.outColor', f'{vray_material}.{vray_attr}')

# i forgot to finish the prompt before hitting enter
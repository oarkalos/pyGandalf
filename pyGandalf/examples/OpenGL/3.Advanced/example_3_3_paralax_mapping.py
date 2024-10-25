from pyGandalf.core.application import Application
from pyGandalf.core.opengl_window import OpenGLWindow

from pyGandalf.systems.link_system import LinkSystem
from pyGandalf.systems.transform_system import TransformSystem
from pyGandalf.systems.camera_system import CameraSystem
from pyGandalf.systems.camera_controller_system import CameraControllerSystem
from pyGandalf.systems.opengl_rendering_system import OpenGLStaticMeshRenderingSystem
from pyGandalf.systems.light_system import LightSystem

from pyGandalf.renderer.opengl_renderer import OpenGLRenderer

from pyGandalf.scene.scene import Scene
from pyGandalf.scene.scene_manager import SceneManager
from pyGandalf.scene.components import *

from pyGandalf.utilities.opengl_material_lib import OpenGLMaterialLib, MaterialData
from pyGandalf.utilities.opengl_texture_lib import OpenGLTextureLib, TextureData, TextureDescriptor
from pyGandalf.utilities.opengl_shader_lib import OpenGLShaderLib

from pyGandalf.utilities.definitions import SHADERS_PATH, TEXTURES_PATH
from pyGandalf.utilities.logger import logger

import glm
import numpy as np

"""
Showcase of a brick wall using different methods to parallax mapping compared to simple normal mapping.
"""

def calculate_vertex_data():
    # positions
    pos1 = glm.vec3(-1.0,  1.0, 0.0)
    pos2 = glm.vec3(-1.0, -1.0, 0.0)
    pos3 = glm.vec3( 1.0, -1.0, 0.0)
    pos4 = glm.vec3( 1.0,  1.0, 0.0)

    # texture coordinates
    uv1 = glm.vec2(0.0, 1.0)
    uv2 = glm.vec2(0.0, 0.0)
    uv3 = glm.vec2(1.0, 0.0)
    uv4 = glm.vec2(1.0, 1.0)

    # normal vector
    nm = glm.vec3(0.0, 0.0, 1.0)

    # calculate tangent/bitangent vectors of both triangles
    tangent1, bitangent1 = glm.vec3(), glm.vec3()
    tangent2, bitangent2 = glm.vec3(), glm.vec3()

    # triangle 1
    edge1 = pos2 - pos1
    edge2 = pos3 - pos1
    deltaUV1 = uv2 - uv1
    deltaUV2 = uv3 - uv1

    f = 1.0 / (deltaUV1.x * deltaUV2.y - deltaUV2.x * deltaUV1.y)

    tangent1.x = f * (deltaUV2.y * edge1.x - deltaUV1.y * edge2.x)
    tangent1.y = f * (deltaUV2.y * edge1.y - deltaUV1.y * edge2.y)
    tangent1.z = f * (deltaUV2.y * edge1.z - deltaUV1.y * edge2.z)

    bitangent1.x = f * (-deltaUV2.x * edge1.x + deltaUV1.x * edge2.x)
    bitangent1.y = f * (-deltaUV2.x * edge1.y + deltaUV1.x * edge2.y)
    bitangent1.z = f * (-deltaUV2.x * edge1.z + deltaUV1.x * edge2.z)

    # triangle 2
    edge1 = pos3 - pos1
    edge2 = pos4 - pos1
    deltaUV1 = uv3 - uv1
    deltaUV2 = uv4 - uv1

    f = 1.0 / (deltaUV1.x * deltaUV2.y - deltaUV2.x * deltaUV1.y)

    tangent2.x = f * (deltaUV2.y * edge1.x - deltaUV1.y * edge2.x)
    tangent2.y = f * (deltaUV2.y * edge1.y - deltaUV1.y * edge2.y)
    tangent2.z = f * (deltaUV2.y * edge1.z - deltaUV1.y * edge2.z)

    bitangent2.x = f * (-deltaUV2.x * edge1.x + deltaUV1.x * edge2.x)
    bitangent2.y = f * (-deltaUV2.x * edge1.y + deltaUV1.x * edge2.y)
    bitangent2.z = f * (-deltaUV2.x * edge1.z + deltaUV1.x * edge2.z)

    vertices = np.array([
        [pos1.x, pos1.y, pos1.z], [pos2.x, pos2.y, pos2.z], [pos3.x, pos3.y, pos3.z],
        [pos1.x, pos1.y, pos1.z], [pos3.x, pos3.y, pos3.z], [pos4.x, pos4.y, pos4.z]
    ], dtype=np.float32)

    normals = np.array([
        [nm.x, nm.y, nm.z], [nm.x, nm.y, nm.z], [nm.x, nm.y, nm.z],
        [nm.x, nm.y, nm.z], [nm.x, nm.y, nm.z], [nm.x, nm.y, nm.z]
    ], dtype=np.float32)

    texture_coords = np.array([
        [uv1.x, uv1.y], [uv2.x, uv2.y], [uv3.x, uv3.y],
        [uv1.x, uv1.y], [uv3.x, uv3.y], [uv4.x, uv4.y]
    ], dtype=np.float32)

    tangent = np.array([
        [tangent1.x, tangent1.y, tangent1.z], [tangent1.x, tangent1.y, tangent1.z], [tangent1.x, tangent1.y, tangent1.z],
        [tangent2.x, tangent2.y, tangent2.z], [tangent2.x, tangent2.y, tangent2.z], [tangent2.x, tangent2.y, tangent2.z]
    ], dtype=np.float32)

    bitangent = np.array([
        [bitangent1.x, bitangent1.y, bitangent1.z], [bitangent1.x, bitangent1.y, bitangent1.z], [bitangent1.x, bitangent1.y, bitangent1.z],
        [bitangent2.x, bitangent2.y, bitangent2.z], [bitangent2.x, bitangent2.y, bitangent2.z], [bitangent2.x, bitangent2.y, bitangent2.z]
    ], dtype=np.float32)

    return vertices, normals, texture_coords, tangent, bitangent

def main():
    # Set the logger DEBUG to report all the logs
    logger.setLevel(logger.DEBUG)

    # Create a new application
    Application().create(OpenGLWindow('Parallax Mapping', 1280, 720, True), OpenGLRenderer)

    # Create a new scene
    scene = Scene('Parallax Mapping')

    # Create Enroll entities to registry
    root = scene.enroll_entity()
    camera = scene.enroll_entity()
    wall_normal = scene.enroll_entity()
    wall_parallax = scene.enroll_entity()
    wall_steep_parallax = scene.enroll_entity()
    wall_parallax_occlusion = scene.enroll_entity()
    light = scene.enroll_entity()

    OpenGLTextureLib().build('wall_albedo', TextureData(TEXTURES_PATH / 'bricks2.jpg'), TextureDescriptor(flip=False))
    OpenGLTextureLib().build('wall_normal', TextureData(TEXTURES_PATH / 'bricks2_normal.jpg'), TextureDescriptor(flip=False))
    OpenGLTextureLib().build('wall_disp', TextureData(TEXTURES_PATH / 'bricks2_disp.jpg'), TextureDescriptor(flip=False))

    # Build shaders
    OpenGLShaderLib().build('default_mesh_normal', SHADERS_PATH  / 'opengl' /  'lit_blinn_phong_normal.vs', SHADERS_PATH  / 'opengl' /  'lit_blinn_phong_normal.fs')
    OpenGLShaderLib().build('default_mesh_parallax', SHADERS_PATH  / 'opengl' /  'lit_blinn_phong_parallax.vs', SHADERS_PATH  / 'opengl' /  'lit_blinn_phong_parallax.fs')
    OpenGLShaderLib().build('default_mesh_steep_parallax', SHADERS_PATH  / 'opengl' /  'lit_blinn_phong_parallax.vs', SHADERS_PATH  / 'opengl' /  'lit_blinn_phong_steep_parallax.fs')
    OpenGLShaderLib().build('default_mesh_parallax_occlusion', SHADERS_PATH  / 'opengl' /  'lit_blinn_phong_parallax.vs', SHADERS_PATH  / 'opengl' /  'lit_blinn_phong_parallax_occlusion.fs')
    
    # Build Materials
    OpenGLMaterialLib().build('M_Wall_Normal', MaterialData('default_mesh_normal', ['wall_albedo', 'wall_normal'], glossiness=1.0))
    OpenGLMaterialLib().build('M_Wall_Parallax', MaterialData('default_mesh_parallax', ['wall_albedo', 'wall_normal', 'wall_disp'], glossiness=1.0))
    OpenGLMaterialLib().build('M_Wall_Steep_Parallax', MaterialData('default_mesh_steep_parallax', ['wall_albedo', 'wall_normal', 'wall_disp'], glossiness=1.0))
    OpenGLMaterialLib().build('M_Wall_Parallax_Occlusion', MaterialData('default_mesh_parallax_occlusion', ['wall_albedo', 'wall_normal', 'wall_disp'], glossiness=1.0))

    # Vertex data for the plane
    vertices, normals, texture_coords, tangent, bitangent = calculate_vertex_data()

    # Register components to root
    scene.add_component(root, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(root, InfoComponent('root'))
    scene.add_component(root, LinkComponent(None))

    # Register components to wall with normal mapping
    scene.add_component(wall_normal, InfoComponent("wall_normal"))
    scene.add_component(wall_normal, TransformComponent(glm.vec3(-2.5, 1.25, 0), glm.vec3(0, 0, 180), glm.vec3(1, 1, 1)))
    scene.add_component(wall_normal, LinkComponent(root))
    scene.add_component(wall_normal, StaticMeshComponent('wall_mesh', [vertices, normals, texture_coords, tangent, bitangent]))
    scene.add_component(wall_normal, MaterialComponent('M_Wall_Normal'))

    # Register components to wall with parallax mapping
    scene.add_component(wall_parallax, InfoComponent("wall_parallax"))
    scene.add_component(wall_parallax, TransformComponent(glm.vec3(0, 1.25, 0), glm.vec3(0, 0, 180), glm.vec3(1, 1, 1)))
    scene.add_component(wall_parallax, LinkComponent(root))
    scene.add_component(wall_parallax, StaticMeshComponent('wall_mesh', [vertices, normals, texture_coords, tangent, bitangent]))
    scene.add_component(wall_parallax, MaterialComponent('M_Wall_Parallax'))

    # Register components to wall with steep parallax mapping
    scene.add_component(wall_steep_parallax, InfoComponent("wall_steep_parallax"))
    scene.add_component(wall_steep_parallax, TransformComponent(glm.vec3(-2.5, -1.25, 0), glm.vec3(0, 0, 180), glm.vec3(1, 1, 1)))
    scene.add_component(wall_steep_parallax, LinkComponent(root))
    scene.add_component(wall_steep_parallax, StaticMeshComponent('wall_mesh', [vertices, normals, texture_coords, tangent, bitangent]))
    scene.add_component(wall_steep_parallax, MaterialComponent('M_Wall_Steep_Parallax'))

    # Register components to wall with parallax occlusion mapping
    scene.add_component(wall_parallax_occlusion, InfoComponent("wall_parallax_occlusion"))
    scene.add_component(wall_parallax_occlusion, TransformComponent(glm.vec3(0, -1.25, 0), glm.vec3(0, 0, 180), glm.vec3(1, 1, 1)))
    scene.add_component(wall_parallax_occlusion, LinkComponent(root))
    scene.add_component(wall_parallax_occlusion, StaticMeshComponent('wall_mesh', [vertices, normals, texture_coords, tangent, bitangent]))
    scene.add_component(wall_parallax_occlusion, MaterialComponent('M_Wall_Parallax_Occlusion'))

    # Register components to light
    scene.add_component(light, InfoComponent("light"))
    scene.add_component(light, TransformComponent(glm.vec3(-1.45, 0.8, 4), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(light, LinkComponent(root))
    scene.add_component(light, LightComponent(glm.vec3(1.0, 1.0, 1.0), 1.0))

    # Register components to camera
    scene.add_component(camera, InfoComponent("camera"))
    scene.add_component(camera, TransformComponent(glm.vec3(-1, 0, 6), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(camera, LinkComponent(root))
    scene.add_component(camera, CameraComponent(45, 1.778, 0.1, 1000, 1.2, CameraComponent.Type.PERSPECTIVE))
    scene.add_component(camera, CameraControllerComponent())

    # Register the systems
    scene.register_system(TransformSystem([TransformComponent]))
    scene.register_system(LinkSystem([LinkComponent, TransformComponent]))
    scene.register_system(CameraSystem([CameraComponent, TransformComponent]))
    scene.register_system(LightSystem([LightComponent, TransformComponent]))
    scene.register_system(OpenGLStaticMeshRenderingSystem([StaticMeshComponent, MaterialComponent, TransformComponent]))
    scene.register_system(CameraControllerSystem([CameraControllerComponent, CameraComponent, TransformComponent]))

    # Add scene to manager
    SceneManager().add_scene(scene)

    # Start application
    Application().start()

if __name__ == "__main__":
    main()
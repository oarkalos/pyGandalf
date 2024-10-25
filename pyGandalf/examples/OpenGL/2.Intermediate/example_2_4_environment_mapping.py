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

from pyGandalf.utilities.opengl_material_lib import OpenGLMaterialLib, MaterialData, MaterialDescriptor
from pyGandalf.utilities.opengl_texture_lib import OpenGLTextureLib, TextureData, TextureDescriptor, TextureDimension
from pyGandalf.utilities.opengl_shader_lib import OpenGLShaderLib
from pyGandalf.utilities.mesh_lib import MeshLib

from pyGandalf.utilities.definitions import SHADERS_PATH, TEXTURES_PATH, MODELS_PATH
from pyGandalf.utilities.logger import logger

import numpy as np
import OpenGL.GL as gl

"""
Showcase of reflection and refraction materials when using a skybox.
"""

def main():
    # Set the logger DEBUG to report all the logs
    logger.setLevel(logger.DEBUG)

    # Create a new application
    Application().create(OpenGLWindow('Environment Mapping - Reflection and Refraction', 1280, 720, True), OpenGLRenderer)

    # Create a new scene
    scene = Scene('Environment Mapping - Reflection and Refraction')

    # Create Enroll entities to registry
    root = scene.enroll_entity()
    camera = scene.enroll_entity()
    reflection_bunny = scene.enroll_entity()
    refraction_bunny = scene.enroll_entity()
    light = scene.enroll_entity()
    skybox = scene.enroll_entity()

    # Array that holds all the skybox textures
    skybox_textures = [
        TEXTURES_PATH / 'skybox' / 'sea' / 'right.jpg',
        TEXTURES_PATH / 'skybox' / 'sea' / 'left.jpg',
        TEXTURES_PATH / 'skybox' / 'sea' / 'top.jpg',
        TEXTURES_PATH / 'skybox' / 'sea' / 'bottom.jpg',
        TEXTURES_PATH / 'skybox' / 'sea' / 'front.jpg',
        TEXTURES_PATH / 'skybox' / 'sea' / 'back.jpg'
    ]

    # Vertices for the cube
    vertices = np.array([
        [-1.0, -1.0, -1.0], [-1.0, -1.0,  1.0], [-1.0,  1.0,  1.0], [ 1.0,  1.0, -1.0],
        [-1.0, -1.0, -1.0], [-1.0,  1.0, -1.0], [1.0, -1.0,  1.0], [-1.0, -1.0, -1.0],
        [1.0, -1.0, -1.0], [ 1.0,  1.0, -1.0], [1.0, -1.0, -1.0], [-1.0, -1.0, -1.0],

        [-1.0, -1.0, -1.0], [-1.0,  1.0,  1.0], [-1.0,  1.0, -1.0], [ 1.0, -1.0,  1.0],
        [-1.0, -1.0,  1.0], [-1.0, -1.0, -1.0], [-1.0,  1.0,  1.0], [-1.0, -1.0,  1.0],
        [1.0, -1.0,  1.0], [1.0,  1.0,  1.0], [1.0, -1.0, -1.0], [1.0,  1.0, -1.0],

        [1.0, -1.0, -1.0], [1.0,  1.0,  1.0], [1.0, -1.0,  1.0], [1.0,  1.0,  1.0],
        [1.0,  1.0, -1.0], [-1.0,  1.0, -1.0], [1.0,  1.0,  1.0], [-1.0,  1.0, -1.0],
        [-1.0,  1.0,  1.0], [1.0,  1.0,  1.0], [-1.0,  1.0,  1.0], [1.0, -1.0,  1.0]
    ], dtype=np.float32)

    # Build textures
    OpenGLTextureLib().build('white_texture', TextureData(image_bytes=0xffffffff.to_bytes(4, byteorder='big'), width=1, height=1))
    OpenGLTextureLib().build('cube_map', TextureData(path=skybox_textures), TextureDescriptor(flip=True, dimention=TextureDimension.CUBE, internal_format=gl.GL_RGB8, format=gl.GL_RGB))

    # Build shaders
    OpenGLShaderLib().build('default_mesh', SHADERS_PATH / 'opengl' / 'lit_blinn_phong.vs', SHADERS_PATH / 'opengl' / 'lit_blinn_phong.fs')
    OpenGLShaderLib().build('skybox', SHADERS_PATH / 'opengl' / 'skybox.vs', SHADERS_PATH / 'opengl' / 'skybox.fs')
    OpenGLShaderLib().build('cubemap_reflection', SHADERS_PATH / 'opengl' / 'cubemap_reflection.vs', SHADERS_PATH / 'opengl' / 'cubemap_reflection.fs')
    OpenGLShaderLib().build('cubemap_refraction', SHADERS_PATH / 'opengl' / 'cubemap_refraction.vs', SHADERS_PATH / 'opengl' / 'cubemap_refraction.fs')
    
    # Build Materials
    OpenGLMaterialLib().build('M_Skybox', MaterialData('skybox', ['cube_map']), MaterialDescriptor(cull_face=gl.GL_FRONT, depth_mask=gl.GL_FALSE))
    OpenGLMaterialLib().build('M_EnvironmentReflection', MaterialData('cubemap_reflection', ['cube_map']))
    OpenGLMaterialLib().build('M_EnvironmentRefraction', MaterialData('cubemap_refraction', ['cube_map']))

    # Load models
    MeshLib().build('bunny_mesh', MODELS_PATH/'bunny.obj')

    # Register components to root
    scene.add_component(root, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(root, InfoComponent('root'))
    scene.add_component(root, LinkComponent(None))

    # Register components to skybox
    scene.add_component(skybox, InfoComponent("skybox"))
    scene.add_component(skybox, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(skybox, LinkComponent(None))
    scene.add_component(skybox, StaticMeshComponent('skybox', [vertices]))
    scene.add_component(skybox, MaterialComponent('M_Skybox'))

    # Register components to reflection bunny - acts like its a bunny made from a mirror
    scene.add_component(reflection_bunny, InfoComponent("reflection_bunny"))
    scene.add_component(reflection_bunny, TransformComponent(glm.vec3(1.5, 0, 0), glm.vec3(0, 10, 0), glm.vec3(1, 1, 1)))
    scene.add_component(reflection_bunny, LinkComponent(root))
    scene.add_component(reflection_bunny, StaticMeshComponent('bunny_mesh'))
    scene.add_component(reflection_bunny, MaterialComponent('M_EnvironmentReflection'))

    # Register components to refraction bunny - acts like its a bunny made from glass
    scene.add_component(refraction_bunny, InfoComponent("refraction_bunny"))
    scene.add_component(refraction_bunny, TransformComponent(glm.vec3(-1.5, 0, 0), glm.vec3(0, 10, 0), glm.vec3(1, 1, 1)))
    scene.add_component(refraction_bunny, LinkComponent(root))
    scene.add_component(refraction_bunny, StaticMeshComponent('bunny_mesh'))
    scene.add_component(refraction_bunny, MaterialComponent('M_EnvironmentRefraction'))

    # Register components to light
    scene.add_component(light, InfoComponent("light"))
    scene.add_component(light, TransformComponent(glm.vec3(0, 5, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(light, LinkComponent(root))
    scene.add_component(light, LightComponent(glm.vec3(1.0, 1.0, 1.0), 0.75))

    # Register components to camera
    scene.add_component(camera, InfoComponent("camera"))
    scene.add_component(camera, TransformComponent(glm.vec3(-0.25, 1, 4), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
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
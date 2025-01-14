from pyGandalf.core.application import Application
from pyGandalf.core.opengl_window import OpenGLWindow
from pyGandalf.systems.transform_system import TransformSystem
from pyGandalf.systems.camera_system import CameraSystem
from pyGandalf.systems.camera_controller_system import CameraControllerSystem
from pyGandalf.systems.opengl_rendering_system import OpenGLStaticMeshRenderingSystem

from pyGandalf.renderer.opengl_renderer import OpenGLRenderer

from pyGandalf.scene.scene import Scene
from pyGandalf.scene.components import *
from pyGandalf.scene.scene_manager import SceneManager

from pyGandalf.utilities.opengl_material_lib import OpenGLMaterialLib, MaterialData
from pyGandalf.utilities.opengl_shader_lib import OpenGLShaderLib

from pyGandalf.utilities.logger import logger
from pyGandalf.utilities.definitions import SHADERS_PATH

import numpy as np
import glm

"""
Showcase of basic triangle drawing using the pyGandalf API.
"""

def main():
    # Set the logger DEBUG to report all the logs
    logger.setLevel(logger.DEBUG)

    # Create a new application
    Application().create(OpenGLWindow('Triangle', 1280, 720, True), OpenGLRenderer)

    # Create a new scene
    scene = Scene('Triangle')

    # Enroll a triangle entity to registry
    root = scene.enroll_entity()
    triangle = scene.enroll_entity()
    camera = scene.enroll_entity()

    # Build shaders 
    OpenGLShaderLib().build('mesh_shader', vs_path=SHADERS_PATH / 'opengl' / 'mesh_shader.glsl', fs_path=SHADERS_PATH / 'opengl' / 'pixel_shader.glsl', isMehShader=True)
    
    # Build Materials
    OpenGLMaterialLib().build('M_Unlit', MaterialData('mesh_shader', []))

    # Vertices of the triangle
    vertices = np.array([
        [-0.5, -0.5, 0.0], # 0 - Bottom left
        [ 0.5, -0.5, 0.0], # 1 - Bottom right
        [ 0.0,  0.5, 0.0], # 2 - Top middle
    ], dtype=np.float32)

    # Register components to root
    scene.add_component(root, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(root, InfoComponent("root"))
    scene.add_component(root, LinkComponent(None))

    # Register components to triangle
    scene.add_component(triangle, InfoComponent("triangle"))
    scene.add_component(triangle, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(triangle, LinkComponent(root))
    scene.add_component(triangle, StaticMeshComponent('triangle', [vertices]))
    scene.add_component(triangle, MaterialComponent('M_Unlit'))

    # Register components to camera
    scene.add_component(camera, InfoComponent("camera"))
    scene.add_component(camera, TransformComponent(glm.vec3(0, 0, 5), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(camera, LinkComponent(root))
    scene.add_component(camera, CameraComponent(45, 1.778, 0.1, 1000, 1.2, CameraComponent.Type.PERSPECTIVE))
    scene.add_component(camera, CameraControllerComponent())

    # Register systems to the scene
    scene.register_system(TransformSystem([TransformComponent]))
    scene.register_system(CameraSystem([CameraComponent, TransformComponent]))
    scene.register_system(OpenGLStaticMeshRenderingSystem([StaticMeshComponent, MaterialComponent, TransformComponent]))
    scene.register_system(CameraControllerSystem([CameraControllerComponent, CameraComponent, TransformComponent]))

    # Add scene to the manager
    SceneManager().add_scene(scene)

    # Start application
    Application().start()

if __name__ == "__main__":
    main()
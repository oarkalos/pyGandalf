from pyGandalf.core.application import Application
from pyGandalf.core.opengl_window import OpenGLWindow
from pyGandalf.systems.transform_system import TransformSystem
from pyGandalf.systems.camera_system import CameraSystem
from pyGandalf.systems.opengl_rendering_system import OpenGLStaticMeshRenderingSystem

from pyGandalf.renderer.opengl_renderer import OpenGLRenderer

from pyGandalf.scene.scene import Scene
from pyGandalf.scene.components import *
from pyGandalf.scene.scene_manager import SceneManager

from pyGandalf.utilities.opengl_material_lib import OpenGLMaterialLib, MaterialData
from pyGandalf.utilities.opengl_shader_lib import OpenGLShaderLib

from pyGandalf.utilities.logger import logger
from pyGandalf.utilities.definitions import SHADERS_PATH, TEXTURES_PATH

import numpy as np
import glm

"""
Showcase of basic quad drawing using the pyGandalf API using a perspective camera.
"""

def main():
    # Set the logger DEBUG to report all the logs
    logger.setLevel(logger.DEBUG)

    # Create a new application
    Application().create(OpenGLWindow('Camera', 1280, 720, True), OpenGLRenderer)

    # Create a new scene
    scene = Scene('Camera')

    # Enroll entities to registry
    quad = scene.enroll_entity()
    camera = scene.enroll_entity()

    # Build shaders 
    OpenGLShaderLib().build('unlit', SHADERS_PATH / 'opengl' / 'unlit_simple.vs', SHADERS_PATH / 'opengl' / 'unlit_simple.fs')
    
    # Build Materials
    OpenGLMaterialLib().build('M_Unlit', MaterialData('unlit', [], glm.vec4(0.8, 0.5, 0.3, 1.0)))

    # Vertices of the quad
    vertices = np.array([
        [-0.5, -0.5, 0.0], # 0 - Bottom left
        [ 0.5, -0.5, 0.0], # 1 - Bottom right
        [ 0.5,  0.5, 0.0], # 2 - Top right
        [ 0.5,  0.5, 0.0], # 2 - Top right
        [-0.5,  0.5, 0.0], # 3 - Top left
        [-0.5, -0.5, 0.0]  # 0 - Bottom left
    ], dtype=np.float32)

    # Register components to quad
    scene.add_component(quad, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(quad, InfoComponent("quad"))
    scene.add_component(quad, StaticMeshComponent('quad', [vertices]))
    scene.add_component(quad, MaterialComponent('M_Unlit'))
    
    # Register components to camera
    scene.add_component(camera, InfoComponent("camera"))
    scene.add_component(camera, TransformComponent(glm.vec3(0, 0, 5), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(camera, CameraComponent(45, 1.778, 0.1, 1000, 1.2, CameraComponent.Type.PERSPECTIVE))

    # Register systems to the scene
    scene.register_system(TransformSystem([TransformComponent]))
    scene.register_system(CameraSystem([CameraComponent, TransformComponent]))
    scene.register_system(OpenGLStaticMeshRenderingSystem([StaticMeshComponent, MaterialComponent, TransformComponent]))

    # Add scene to the manager
    SceneManager().add_scene(scene)

    # Start application
    Application().start()

if __name__ == "__main__":
    main()
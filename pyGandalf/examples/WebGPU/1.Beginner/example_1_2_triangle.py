from pyGandalf.core.application import Application
from pyGandalf.core.webgpu_window import WebGPUWindow
from pyGandalf.systems.transform_system import TransformSystem
from pyGandalf.systems.webgpu_rendering_system import WebGPUStaticMeshRenderingSystem

from pyGandalf.renderer.webgpu_renderer import WebGPURenderer

from pyGandalf.scene.scene import Scene
from pyGandalf.scene.components import *
from pyGandalf.scene.scene_manager import SceneManager

from pyGandalf.utilities.webgpu_material_lib import WebGPUMaterialLib, MaterialData
from pyGandalf.utilities.webgpu_shader_lib import WebGPUShaderLib

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
    Application().create(WebGPUWindow('Triangle', 1280, 720, True), WebGPURenderer)

    # Create a new scene
    scene = Scene('Triangle')

    # Enroll a triangle entity to registry
    triangle = scene.enroll_entity()

    # Build shaders 
    WebGPUShaderLib().build('unlit', SHADERS_PATH / 'webgpu' / 'unlit.wgsl')
    
    # Build Materials
    WebGPUMaterialLib().build('M_Unlit', MaterialData('unlit', []))

    # Vertices of the triangle
    vertices = np.array([
        [ 0.0,  0.5, 0.0], # 2 - Top middle
        [ 0.5, -0.5, 0.0], # 1 - Bottom right
        [-0.5, -0.5, 0.0], # 0 - Bottom left
    ], dtype=np.float32)

    # Register components to triangle
    scene.add_component(triangle, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(triangle, InfoComponent("triangle"))
    scene.add_component(triangle, StaticMeshComponent('triangle', [vertices]))
    scene.add_component(triangle, MaterialComponent('M_Unlit'))

    # Register systems to the scene
    scene.register_system(TransformSystem([TransformComponent]))
    scene.register_system(WebGPUStaticMeshRenderingSystem([StaticMeshComponent, MaterialComponent, TransformComponent]))

    # Add scene to the manager
    SceneManager().add_scene(scene)

    # Start application
    Application().start()

if __name__ == "__main__":
    main()
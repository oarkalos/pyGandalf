from pyGandalf.core.application import Application
from pyGandalf.core.opengl_window import OpenGLWindow

from pyGandalf.core.events import EventType
from pyGandalf.core.event_manager import EventManager

from pyGandalf.systems.link_system import LinkSystem
from pyGandalf.systems.light_system import LightSystem
from pyGandalf.systems.transform_system import TransformSystem
from pyGandalf.systems.camera_system import CameraSystem
from pyGandalf.systems.camera_controller_system import CameraControllerSystem
from pyGandalf.systems.opengl_rendering_system import OpenGLStaticMeshRenderingSystem
from pyGandalf.systems.terrain_generation_system import TerrainGenerationSystem

from pyGandalf.renderer.opengl_renderer import OpenGLRenderer

from pyGandalf.scene.scene import Scene
from pyGandalf.scene.scene_manager import SceneManager
from pyGandalf.scene.components import *

from pyGandalf.utilities.opengl_material_lib import OpenGLMaterialLib, MaterialData, MaterialDescriptor
from pyGandalf.utilities.opengl_texture_lib import OpenGLTextureLib, TextureData
from pyGandalf.utilities.opengl_shader_lib import OpenGLShaderLib

from pyGandalf.utilities.definitions import SHADERS_PATH
from pyGandalf.utilities.logger import logger

import glfw
import numpy as np
import OpenGL.GL as gl
import pyGandalf.utilities.noise_lib as Noise

def main():
    noiseSettings = Noise.NoiseSettings('Mountains', 30, 2, 2, 0.5, 2, False, 2, False, Noise.typeOfNoise.Perlin)
    #noiseSettings2 = Noise.NoiseSettings('Mountains2', 3, 7, 2, 0.5, 2, False, 2, False, Noise.typeOfNoise.Perlin)
    # Set the logger DEBUG to report all the logs
    logger.setLevel(logger.DEBUG)

    patch_resolution = 8
    vertices_per_patch = 4
    terrainComponent = TerrainComponent(200, 62, 64, True, Noise.typeOfFallOff.Circle, 2.2, 0.4, 0.2, patch_resolution, vertices_per_patch, False)

    # Create a new application
    Application().create(OpenGLWindow('Tessellation Shaders', 1280, 720, True), OpenGLRenderer, attach_imgui=True, attach_editor=True)
    #OpenGLRenderer().set_shadows_enabled(True)

    # Create a new scene
    scene = Scene('Tessellation Shaders')

    # Create Enroll entities to registry
    root = scene.enroll_entity()
    camera = scene.enroll_entity()
    terrain = scene.enroll_entity()
    light = scene.enroll_entity()

    # Build textures
    OpenGLTextureLib().build('height_map', TextureData('height_map.png'))
    OpenGLTextureLib().build('normal_map', TextureData('height_map_normals.png'))

    # Build shaders
    OpenGLShaderLib().build('default_tessellation', SHADERS_PATH / 'opengl' / 'tessellation.vs', SHADERS_PATH / 'opengl' / 'tessellation.fs', None, SHADERS_PATH / 'opengl' / 'tessellation.tcs', SHADERS_PATH / 'opengl' / 'tessellation.tes')
    
    # Build Materials
    OpenGLMaterialLib().build('M_Terrain', MaterialData('default_tessellation', ['height_map', 'normal_map']), MaterialDescriptor(primitive=gl.GL_PATCHES, cull_face=gl.GL_FRONT, patch_resolution=terrainComponent.patch_resolution, vertices_per_patch=terrainComponent.vertices_per_patch))

    vertices = [[0.0, 0.0, 0.0]]
    tex_coords = [[0.0, 0.0]]

    vertices = np.asarray(vertices, np.float32)
    tex_coords = np.asarray(tex_coords, np.float32)

    # Register components to root
    scene.add_component(root, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(root, InfoComponent('root'))
    scene.add_component(root, LinkComponent(None))

    terrainComponent.noiseLayers.append(noiseSettings)
    #terrainComponent.noiseLayers.append(noiseSettings2)

    # Register components to terrain
    scene.add_component(terrain, InfoComponent("terrain"))
    scene.add_component(terrain, TransformComponent(glm.vec3(0, 0, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(terrain, LinkComponent(root))
    scene.add_component(terrain, StaticMeshComponent('terrain_mesh', attributes=[vertices, tex_coords]))
    scene.add_component(terrain, MaterialComponent('M_Terrain'))
    scene.add_component(terrain, terrainComponent)

    # Register components to camera
    scene.add_component(camera, InfoComponent("camera"))
    scene.add_component(camera, TransformComponent(glm.vec3(0, 50, 0), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(camera, LinkComponent(root))
    scene.add_component(camera, CameraComponent(45, 1.778, 0.1, 2000, 1.2, CameraComponent.Type.PERSPECTIVE))
    scene.add_component(camera, CameraControllerComponent(15, 2))

    # Register components to light
    scene.add_component(light, InfoComponent("light"))
    scene.add_component(light, TransformComponent(glm.vec3(0, 50, 2), glm.vec3(0, 0, 0), glm.vec3(1, 1, 1)))
    scene.add_component(light, LinkComponent(root))
    scene.add_component(light, LightComponent(glm.vec3(1.0, 1.0, 1.0), 10000.0))

    # Create Register systems
    scene.register_system(TransformSystem([TransformComponent]))
    scene.register_system(LinkSystem([LinkComponent, TransformComponent]))
    scene.register_system(CameraSystem([CameraComponent, TransformComponent]))
    scene.register_system(LightSystem([LightComponent, TransformComponent]))
    scene.register_system(OpenGLStaticMeshRenderingSystem([StaticMeshComponent, MaterialComponent, TransformComponent]))
    scene.register_system(CameraControllerSystem([CameraControllerComponent, CameraComponent, TransformComponent]))
    scene.register_system(TerrainGenerationSystem([TerrainComponent, StaticMeshComponent]))

    # Add scene to manager
    SceneManager().add_scene(scene)

    # Attach events
    def on_key_callback(key, modifiers):
        if key == glfw.KEY_F:
            OpenGLRenderer().set_fill_mode(gl.GL_FILL)
        if key == glfw.KEY_L:
            OpenGLRenderer().set_fill_mode(gl.GL_LINE)

    EventManager().attach_callback(EventType.KEY_PRESS, on_key_callback, True)

    # Start application
    Application().start()

if __name__ == "__main__":
    main()
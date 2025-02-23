from pyGandalf.systems.system import System
from pyGandalf.scene.entity import Entity
from pyGandalf.scene.components import TerrainComponent
from pyGandalf.scene.components import StaticMeshComponent
from pyGandalf.scene.components import TransformComponent
from pyGandalf.scene.components import ComputeComponent
from pyGandalf.scene.components import Component
import numpy as np
import glm
import OpenGL.GL as gl
from PIL import Image, ImageDraw
from pyGandalf.utilities.opengl_texture_lib import OpenGLTextureLib, TextureData

class TerrainGenerationSystem(System):
    """
    The system responsible for the terrain generation.
    """

    def on_create_entity(self, entity: Entity, components: Component | tuple[Component]):
        pass

    def on_update_entity(self, ts: float, entity: Entity, components: Component | tuple[Component]):
        # NOTE: These should match the components that the system operates on, which are defined in the system instantiation.
        #       See line 145: 'scene.register_system(TerrainGenerationSystem([TerrainComponent, StaticMeshComponent]))'
        terrain: TerrainComponent = components[0]
        mesh: StaticMeshComponent = components[1]
        transform: TransformComponent = components[2]
        compute: ComputeComponent = components[3]

        if terrain.mapSize != compute.workGroupsX:
            compute.workGroupsX = terrain.mapSize
            compute.workGroupsY = terrain.mapSize
            uniformDataIndex = list(compute.uniformsDictionary.keys()).index('mapSize')
            compute.uniformsData[uniformDataIndex] = terrain.mapSize

        vertices = []
        tex_coords = []

        if terrain.cameraMoved:
            if not terrain.erode:
                transform.translation.x = terrain.cameraCoords.x
                transform.translation.z = terrain.cameraCoords.y
            terrain.cameraMoved = False

        if terrain.generate:
            width, height = (terrain.scale, terrain.scale)

            for i in range(terrain.patch_resolution):
                for j in range(terrain.patch_resolution):
                    vertex = []
                    vertex.append((-width / 2.0 + width * i / float(terrain.patch_resolution)))  # v.x
                    vertex.append(0.0)  # v.y
                    vertex.append(-height / 2.0 + height * j / float(terrain.patch_resolution))  # v.z
                    vertices.append(vertex)

                    tex_coord = []
                    tex_coord.append(i / float(terrain.patch_resolution))  # u
                    tex_coord.append(j / float(terrain.patch_resolution))  # v
                    tex_coords.append(tex_coord)

                    vertex = []
                    vertex.append((-width / 2.0 + width * (i + 1) / float(terrain.patch_resolution)) )  # v.x
                    vertex.append(0.0)  # v.y
                    vertex.append((-height / 2.0 + height * j / float(terrain.patch_resolution))  )  # v.z
                    vertices.append(vertex)

                    tex_coord = []
                    tex_coord.append((i + 1) / float(terrain.patch_resolution))  # u
                    tex_coord.append(j / float(terrain.patch_resolution))  # v
                    tex_coords.append(tex_coord)

                    vertex = []
                    vertex.append((-width / 2.0 + width * i / float(terrain.patch_resolution))  )  # v.x
                    vertex.append(0.0)  # v.y
                    vertex.append((-height / 2.0 + height * (j + 1) / float(terrain.patch_resolution))  )  # v.z
                    vertices.append(vertex)

                    tex_coord = []
                    tex_coord.append(i / float(terrain.patch_resolution))  # u
                    tex_coord.append((j + 1) / float(terrain.patch_resolution))  # v
                    tex_coords.append(tex_coord)

                    vertex = []
                    vertex.append((-width / 2.0 + width * (i + 1) / float(terrain.patch_resolution))  )  # v.x
                    vertex.append(0.0)  # v.y
                    vertex.append((-height / 2.0 + height * (j + 1) / float(terrain.patch_resolution))  )  # v.z
                    vertices.append(vertex)

                    tex_coord = []
                    tex_coord.append((i + 1) / float(terrain.patch_resolution))  # u
                    tex_coord.append((j + 1) / float(terrain.patch_resolution))  # v
                    tex_coords.append(tex_coord)

            terrain.vertices = np.asarray(vertices, np.float32)
            tex_coords = np.asarray(tex_coords, np.float32)

            mesh.attributes = [terrain.vertices, tex_coords]  
            mesh.changed = True 
            terrain.generate = False
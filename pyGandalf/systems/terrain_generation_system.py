from pyGandalf.systems.system import System
from pyGandalf.scene.entity import Entity
from pyGandalf.scene.components import TerrainComponent
from pyGandalf.scene.components import StaticMeshComponent
from pyGandalf.scene.components import TransformComponent
from pyGandalf.scene.components import ComputeComponent
from pyGandalf.scene.components import Component
import numpy as np
import glm
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

        """if terrain.mapSize != compute.workGroupsX:
            compute.workGroupsX = terrain.mapSize
            compute.workGroupsY = terrain.mapSize
            OpenGLTextureLib().update('heightmap', TextureData(width=terrain.mapSize, height=terrain.mapSize))"""

        vertices = []
        tex_coords = []

        if terrain.cameraMoved:
            transform.translation.x = terrain.cameraCoords.x
            transform.translation.z = terrain.cameraCoords.y
            terrain.cameraMoved = False

        if terrain.generate:
            #self.CreateHeightMap(terrain)
            #self.export_texture(terrain.heights, "height_map.png", (terrain.mapSize, terrain.mapSize), terrain)
            #self.Generate(terrain)
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

    def export_texture(self, heightmap, filename, map_size=(256, 256), terrain=None):
        image = Image.new('RGB', map_size, 0)
        normalImage = Image.new('RGB', map_size, 0)
        draw = ImageDraw.ImageDraw(image)
        drawNormals = ImageDraw.ImageDraw(normalImage)
        for z in range(map_size[0]):
            for x in range(map_size[1]):
                draw.point((z, x), (int(heightmap[z][x] * 255), int(heightmap[z][x] * 255), int(heightmap[z][x] * 255)))
                o = heightmap[z][x]
                b = o 
                if z < terrain.mapSize - 1:
                    b = heightmap[z + 1][x]
                t = o 
                if z > 0:
                    t = heightmap[z - 1][x]
                l = o 
                if x > 0:
                    l = heightmap[z][x - 1]
                r = o
                if x < terrain.mapSize - 1:
                    r = heightmap[z][x + 1]
                vecX = glm.vec3(2 , (r - l) * terrain.elevationScale, 0)
                vecY = glm.vec3(0, (t - b) * terrain.elevationScale, -2)
                normal = glm.normalize(glm.cross(glm.normalize(vecX), glm.normalize(vecY)))
                drawNormals.point((z, x), (int(normal.x * 255), int(normal.y * 255), int(normal.z * 255)))
        image.save(filename)
        normalImage.save("height_map_normals.png")
        print(filename, "saved")
        return image.width, image.height
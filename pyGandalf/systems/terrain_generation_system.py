from pyGandalf.systems.system import System
from pyGandalf.scene.entity import Entity
from pyGandalf.scene.components import TerrainComponent
from pyGandalf.scene.components import StaticMeshComponent
from pyGandalf.scene.components import TransformComponent
from pyGandalf.scene.components import Component
import pyGandalf.utilities.noise_lib as Noise
import numpy as np
import glm
from PIL import Image, ImageDraw
from pyGandalf.utilities.opengl_texture_lib import OpenGLTextureLib, TextureData

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolate on the scale given by a to b, using t as the point on that scale.
    Examples
    --------
        50 == lerp(0, 100, 0.5)
        4.2 == lerp(1, 5, 0.8)
    """
    return (1 - t) * a + t * b

# From: https://gist.github.com/laundmo/b224b1f4c8ef6ca5fe47e132c8deab56
def inv_lerp(a: float, b: float, v: float) -> float:
    """Inverse Linar Interpolation, get the fraction between a and b on which v resides.
    Examples
    --------
        0.5 == inv_lerp(0, 100, 50)
        0.8 == inv_lerp(1, 5, 4.2)
    """
    return (v - a) / (b - a)

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

            # Build textures
            OpenGLTextureLib().update('height_map', TextureData('height_map.png'))
            OpenGLTextureLib().update('normal_map', TextureData('height_map_normals.png'))

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

    def ApplyFallOff(self, x, z, height, terrain: TerrainComponent):
        distFromCenter = 0
        h = 0
        if(terrain.fallOffType == Noise.typeOfFallOff.Circle):
            distFromCenter = np.power(x - 0.5, 2) + np.power(z - 0.5, 2)
            distFromCenter *= 2
        else:
            distFromCenter = max(np.abs(x*2 - 1.0), np.abs(z*2 - 1.0))
        h = np.power(distFromCenter, terrain.a) / (np.power(distFromCenter, terrain.a) + np.power(terrain.b - terrain.b * distFromCenter, terrain.a))
        if(height > terrain.fallOffHeight):
            return lerp(height, terrain.fallOffHeight, h)
        else:
            clampedHeight = height
            return lerp(height, clampedHeight, h)

    def Generate(self, terrain: TerrainComponent):
        v = 0
        t = 0
        i = 0

        for z in range(0, terrain.mapSize, 1):
            zCoord = (z / (terrain.mapSize - 1.0)) * 2
            for x in range(0, terrain.mapSize, 1):
                xCoord = (x / (terrain.mapSize - 1.0)) * 2
                terrain.vertices[i] =[(xCoord - 1) * terrain.scale, terrain.heights[z][x] * terrain.elevationScale, (zCoord - 1) * terrain.scale]

                i = i + 1

                if ((z < terrain.mapSize - 1) and (x < terrain.mapSize - 1)):
                    terrain.indices[t] = v
                    terrain.indices[t + 1] = v + terrain.mapSize
                    terrain.indices[t + 2] = v + 1
                    terrain.indices[t + 3] = v + 1
                    terrain.indices[t + 4] = v + terrain.mapSize
                    terrain.indices[t + 5] = v + terrain.mapSize + 1
                    v = v + 1
                    t += 6
                if (x == terrain.mapSize - 1):
                    v = v + 1

    def CreateHeightMap(self, terrain: TerrainComponent):
        terrain.heightMap = [[[0.0 for x in range(0, terrain.mapSize, 1)] for z in range(0, terrain.mapSize, 1)] for i in range(0, len(terrain.noiseLayers), 1)]
        terrain.heights = [[0.0 for x in range(0, terrain.mapSize, 1)] for z in range(0, terrain.mapSize, 1)]
        terrain.vertices = [[0.0, 0.0, 0.0] for x in range(0, terrain.mapSize * terrain.mapSize, 1)]
        terrain.indices = [0 for x in range(0, (terrain.mapSize - 1) * (terrain.mapSize - 1) * 6, 1)]
        for i in range(0, len(terrain.noiseLayers), 1):
            terrain.minTerrainHeight.append(100)
            terrain.maxTerrainHeight.append(0)
        terrain.minHeight = 100
        terrain.maxHeight = 0

        for i in range(0, len(terrain.noiseLayers), 1):
            for z in range(0, terrain.mapSize, 1):
                for x in range(0, terrain.mapSize, 1):
                    terrain.heightMap[i][z][x] = Noise.Noise(x, z, terrain.noiseLayers[i], terrain.mapSize)
                    terrain.minTerrainHeight[i] = min(terrain.minTerrainHeight[i], terrain.heightMap[i][z][x])
                    terrain.maxTerrainHeight[i] = max(terrain.maxTerrainHeight[i], terrain.heightMap[i][z][x])

        for z in range(0, terrain.mapSize, 1):
            zCoord = z / (terrain.mapSize - 1.0)
            for x in range(0, terrain.mapSize, 1):   
                xCoord = x / (terrain.mapSize - 1.0)
                height = 0
                mask = 1
                for l in range(0, len(terrain.noiseLayers), 1):
                    if terrain.noiseLayers[l].layerActive:
                        terrain.heightMap[l][z][x] = inv_lerp(terrain.minTerrainHeight[l], terrain.maxTerrainHeight[l], terrain.heightMap[l][z][x])
                        if l != 0:
                            if (terrain.noiseLayers[l].useFirstLayerAsMask):
                                mask = terrain.heightMap[0][z][x]
                            else:
                                mask = 1
                        height += terrain.heightMap[l][z][x] * mask

                if terrain.fallOffEnabled:
                    height = self.ApplyFallOff(xCoord, zCoord, height, terrain)
                terrain.minHeight = min(terrain.minHeight, height)
                terrain.maxHeight = max(terrain.maxHeight, height)
                terrain.heights[z][x] = height
            
        for z in range(0, terrain.mapSize, 1):
            for x in range(0, terrain.mapSize, 1):
                terrain.heights[z][x] = inv_lerp(terrain.minHeight, terrain.maxHeight, terrain.heights[z][x])
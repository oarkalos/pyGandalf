from pyGandalf.systems.system import System
from pyGandalf.scene.entity import Entity
from pyGandalf.scene.components import TerrainComponent
from pyGandalf.scene.components import StaticMeshComponent
from pyGandalf.scene.components import TransformComponent
from pyGandalf.utilities.opengl_shader_lib import OpenGLShaderLib
from pyGandalf.scene.components import Component
from pyGandalf.utilities.opengl_material_lib import MaterialInstance
import numpy as np
import OpenGL.GL as gl

class TerrainGenerationSystem(System):
    """
    The system responsible for the terrain generation.
    """

    def on_create_entity(self, entity: Entity, components: Component | tuple[Component]):
        terrain: TerrainComponent = components[0]
        computeCode = OpenGLShaderLib().load_from_file(terrain.shader)

        compute_shader = OpenGLShaderLib().compile_shader(computeCode, gl.GL_COMPUTE_SHADER)
        shader_program = gl.glCreateProgram()
        gl.glAttachShader(shader_program, compute_shader)
        gl.glLinkProgram(shader_program)

        if not gl.glGetProgramiv(shader_program, gl.GL_LINK_STATUS):
            raise RuntimeError(gl.glGetProgramInfoLog(shader_program).decode('utf-8'))

        gl.glDeleteShader(compute_shader)

        terrain.ID = shader_program

    def on_update_entity(self, ts: float, entity: Entity, components: Component | tuple[Component]):
        # NOTE: These should match the components that the system operates on, which are defined in the system instantiation.
        #       See line 145: 'scene.register_system(TerrainGenerationSystem([TerrainComponent, StaticMeshComponent]))'
        terrain: TerrainComponent = components[0]
        mesh: StaticMeshComponent = components[1]
        transform: TransformComponent = components[2]

        if terrain.mapSize != terrain.workGroupsX:
            terrain.workGroupsX = terrain.mapSize
            terrain.workGroupsY = terrain.mapSize

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

        if terrain.run:
            gl.glUseProgram(terrain.ID)

            gl.glBindImageTexture(0, terrain.textures[0], 0, gl.GL_FALSE, 0, gl.GL_READ_WRITE, gl.GL_RGBA32F)
            gl.glBindImageTexture(1, terrain.textures[1], 0, gl.GL_FALSE, 0, gl.GL_READ_WRITE, gl.GL_RGBA32F)
            gl.glBindImageTexture(2, terrain.textures[2], 0, gl.GL_FALSE, 0, gl.GL_READ_WRITE, gl.GL_RGBA32F)

            location = gl.glGetUniformLocation(terrain.ID,'scale')
            MaterialInstance.update_uniform(MaterialInstance, location, 'scale', int(terrain.scale), 'int')

            location = gl.glGetUniformLocation(terrain.ID,'frequency')
            MaterialInstance.update_uniform(MaterialInstance, location, 'frequency', terrain.frequency, 'float')

            location = gl.glGetUniformLocation(terrain.ID,'lacunarity')
            MaterialInstance.update_uniform(MaterialInstance, location, 'lacunarity', terrain.lacunarity, 'float')

            location = gl.glGetUniformLocation(terrain.ID,'persistence')
            MaterialInstance.update_uniform(MaterialInstance, location, 'persistence', terrain.persistence, 'float')

            location = gl.glGetUniformLocation(terrain.ID,'octaves')
            MaterialInstance.update_uniform(MaterialInstance, location, 'octaves', terrain.octaves, 'int')

            location = gl.glGetUniformLocation(terrain.ID,'turbulance')
            MaterialInstance.update_uniform(MaterialInstance, location, 'turbulance', terrain.turbulance, 'int')

            location = gl.glGetUniformLocation(terrain.ID,'Ridges')
            MaterialInstance.update_uniform(MaterialInstance, location, 'Ridges', terrain.Ridges, 'int')

            location = gl.glGetUniformLocation(terrain.ID,'ridgesStrength')
            MaterialInstance.update_uniform(MaterialInstance, location, 'ridgesStrength', terrain.ridgesStrength, 'int')

            location = gl.glGetUniformLocation(terrain.ID,'seed')
            MaterialInstance.update_uniform(MaterialInstance, location, 'seed', terrain.seed, 'int')

            location = gl.glGetUniformLocation(terrain.ID,'fallOffEnabled')
            MaterialInstance.update_uniform(MaterialInstance, location, 'fallOffEnabled', terrain.fallOffEnabled, 'int')

            location = gl.glGetUniformLocation(terrain.ID,'fallOffType')
            MaterialInstance.update_uniform(MaterialInstance, location, 'fallOffType', terrain.fallOffType, 'int')

            location = gl.glGetUniformLocation(terrain.ID,'fallOffHeight')
            MaterialInstance.update_uniform(MaterialInstance, location, 'fallOffHeight', terrain.fallOffHeight, 'float')

            location = gl.glGetUniformLocation(terrain.ID,'a')
            MaterialInstance.update_uniform(MaterialInstance, location, 'a', terrain.a, 'float')

            location = gl.glGetUniformLocation(terrain.ID,'b')
            MaterialInstance.update_uniform(MaterialInstance, location, 'b', terrain.b, 'float')

            location = gl.glGetUniformLocation(terrain.ID,'underWaterRavines')
            MaterialInstance.update_uniform(MaterialInstance, location, 'underWaterRavines', terrain.underWaterRavines, 'int')

            location = gl.glGetUniformLocation(terrain.ID, 'cameraCoords')
            MaterialInstance.update_uniform(MaterialInstance, location, 'cameraCoords', terrain.cameraCoords, 'vec2')

            location = gl.glGetUniformLocation(terrain.ID, 'mapSize')
            MaterialInstance.update_uniform(MaterialInstance, location, 'mapSize', terrain.mapSize, 'int')

            location = gl.glGetUniformLocation(terrain.ID, 'clampHeight')
            MaterialInstance.update_uniform(MaterialInstance, location, 'clampHeight', terrain.clampHeight, 'int')

            location = gl.glGetUniformLocation(terrain.ID, 'minHeight')
            MaterialInstance.update_uniform(MaterialInstance, location, 'minHeight', terrain.minHeight, 'float')

            location = gl.glGetUniformLocation(terrain.ID, 'maxHeight')
            MaterialInstance.update_uniform(MaterialInstance, location, 'maxHeight', terrain.maxHeight, 'float')

            location = gl.glGetUniformLocation(terrain.ID, 'offsetX')
            MaterialInstance.update_uniform(MaterialInstance, location, 'offsetX', terrain.offsetX, 'float')

            location = gl.glGetUniformLocation(terrain.ID, 'offsetY')
            MaterialInstance.update_uniform(MaterialInstance, location, 'offsetY', terrain.offsetY, 'float')

            location = gl.glGetUniformLocation(terrain.ID, 'loaded')
            MaterialInstance.update_uniform(MaterialInstance, location, 'loaded', terrain.loaded, 'int')

            gl.glDispatchCompute(terrain.workGroupsX, terrain.workGroupsY, terrain.workGroupsZ)
            gl.glMemoryBarrier(gl.GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)
            gl.glUseProgram(0)
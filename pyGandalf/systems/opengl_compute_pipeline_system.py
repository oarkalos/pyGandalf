import OpenGL.GL as gl
from pyGandalf.systems.system import System
from pyGandalf.scene.entity import Entity
from pyGandalf.scene.components import Component
from pyGandalf.scene.components import ComputeComponent, GUIData
from pyGandalf.utilities.opengl_shader_lib import OpenGLShaderLib
from pyGandalf.utilities.opengl_texture_lib import OpenGLTextureLib
from pyGandalf.utilities.opengl_material_lib import MaterialInstance
from pyGandalf.utilities.definitions import SHADERS_PATH
import glm
from PIL import Image, ImageDraw

class OpenGLComputePipelineSystem(System):

    def on_create_entity(self, entity: Entity, components: Component | tuple[Component]):
        compute: ComputeComponent = components
        computeCode = OpenGLShaderLib().load_from_file(compute.shader)

        compute_shader = OpenGLShaderLib().compile_shader(computeCode, gl.GL_COMPUTE_SHADER)
        shader_program = gl.glCreateProgram()
        gl.glAttachShader(shader_program, compute_shader)
        gl.glLinkProgram(shader_program)

        if not gl.glGetProgramiv(shader_program, gl.GL_LINK_STATUS):
            raise RuntimeError(gl.glGetProgramInfoLog(shader_program).decode('utf-8'))

        gl.glDeleteShader(compute_shader)

        compute.ID = shader_program

        compute_params = OpenGLShaderLib().parse(computeCode)
        compute.uniformsDictionary = compute_params

        if compute.uniformsData == []:
            for uniformName, uniformType in compute.uniformsDictionary.items():
                match uniformType:
                    case 'float':
                        compute.uniformsData.append(0.0)
                    case 'int':
                        compute.uniformsData.append(0)
                    case 'image2D':
                        compute.uniformsData.append(0)
                    case 'sampler2D':
                        compute.uniformsData.append(0)
                    case 'samplerCube':
                        compute.uniformsData.append(0)
                    case 'vec2':
                        compute.uniformsData.append(glm.vec2(0.0, 0.0))
                    case 'vec3':
                        compute.uniformsData.append(glm.vec3(0.0, 0.0, 0.0))
                    case 'vec4':
                        compute.uniformsData.append(glm.vec4(0.0, 0.0, 0.0, 0.0))
                    case 'ivec2':
                        compute.uniformsData.append(glm.ivec2(0, 0))
                    case 'ivec3':
                        compute.uniformsData.append(glm.ivec3(0, 0, 0))
                    case 'ivec4':
                        compute.uniformsData.append(glm.ivec4(0, 0, 0, 0))
                    case 'uvec2':
                        compute.uniformsData.append(glm.uvec2(0, 0))
                    case 'uvec3':
                        compute.uniformsData.append(glm.uvec3(0, 0, 0))
                    case 'uvec4':
                        compute.uniformsData.append(glm.uvec4(0, 0, 0, 0))
                    case 'dvec2':
                        compute.uniformsData.append(glm.dvec2(0.0, 0.0))
                    case 'dvec3':
                        compute.uniformsData.append(glm.dvec3(0.0, 0.0, 0.0))
                    case 'dvec4':
                        compute.uniformsData.append(glm.dvec4(0.0, 0.0, 0.0, 0.0))
                    case 'mat2':
                        compute.uniformsData.append(glm.mat2(0.0, 0.0, 0.0, 0.0))
                    case 'mat3':
                        compute.uniformsData.append(glm.mat3(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
                    case 'mat4':
                        compute.uniformsData.append(glm.mat4(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        
        for uniformName, uniformType in compute.uniformsDictionary.items():
            if uniformName not in compute.guiData:
                match uniformType:
                    case 'float':
                        compute.guiData[uniformName] = GUIData(0.01, 0.0, 100.0)
                    case _:
                        compute.guiData[uniformName] = GUIData(1, 0, 1000)
        

    def on_update_entity(self, ts: float, entity: Entity, components: Component | tuple[Component]):
        compute: ComputeComponent = components

        if compute.run:
            gl.glUseProgram(compute.ID)

            gl.glBindImageTexture(0, compute.textures[0], 0, gl.GL_FALSE, 0, gl.GL_READ_WRITE, gl.GL_RGBA32F)
            gl.glBindImageTexture(1, compute.textures[1], 0, gl.GL_FALSE, 0, gl.GL_READ_WRITE, gl.GL_RGBA32F)
            for uniformName, uniformType in compute.uniformsDictionary.items():
                location = gl.glGetUniformLocation(compute.ID, uniformName)
                uniformDataIndex = list(compute.uniformsDictionary.keys()).index(uniformName)
                MaterialInstance.update_uniform(MaterialInstance, location, uniformName, compute.uniformsData[uniformDataIndex], uniformType)

            gl.glDispatchCompute(compute.workGroupsX, compute.workGroupsY, compute.workGroupsZ)
            gl.glMemoryBarrier(gl.GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)
            gl.glUseProgram(0)

        if compute.save:
            self.export_texture("heightmap.png")
            compute.save = False

    def export_texture(self, filename):
        gl.glBindTexture(gl.GL_TEXTURE_2D, OpenGLTextureLib().get_id("heightmap"))
        heightmap = gl.glGetTexImage(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, gl.GL_FLOAT)

        image = Image.new('RGB', (heightmap.shape[0], heightmap.shape[1]), 0)
        draw = ImageDraw.ImageDraw(image)
        for z in range(heightmap.shape[0]):
            for x in range(heightmap.shape[1]):
                draw.point((z, x), (int(heightmap[z][x][0] * 255), int(heightmap[z][x][0] * 255), int(heightmap[z][x][0] * 255)))
        image.save(filename)
        print(filename, "saved")
        return image.width, image.height


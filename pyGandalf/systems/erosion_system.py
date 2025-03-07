import OpenGL.GL as gl
from pyGandalf.systems.system import System
from pyGandalf.scene.entity import Entity
from pyGandalf.scene.components import Component, ErosionComponent
from pyGandalf.utilities.opengl_shader_lib import OpenGLShaderLib
from pyGandalf.utilities.opengl_texture_lib import OpenGLTextureLib
from pyGandalf.utilities.opengl_material_lib import MaterialInstance
from pyGandalf.utilities.definitions import SHADERS_PATH
from PIL import Image, ImageDraw
from os import path

class ErosionSystem(System):

    def compile_compute(self, computeCode):
        compute_shader = OpenGLShaderLib().compile_shader(computeCode, gl.GL_COMPUTE_SHADER)
        shader_program = gl.glCreateProgram()
        gl.glAttachShader(shader_program, compute_shader)
        gl.glLinkProgram(shader_program)

        if not gl.glGetProgramiv(shader_program, gl.GL_LINK_STATUS):
            raise RuntimeError(gl.glGetProgramInfoLog(shader_program).decode('utf-8'))

        gl.glDeleteShader(compute_shader)
        return shader_program

    def on_create_entity(self, entity: Entity, components: Component | tuple[Component]):
        settings: ErosionComponent = components
        erosionCode = OpenGLShaderLib().load_from_file(SHADERS_PATH / 'opengl' / 'erosion.compute')

        settings.erosionId = self.compile_compute(erosionCode)

    def on_update_entity(self, ts: float, entity: Entity, components: Component | tuple[Component]):
        erosion: ErosionComponent = components

        if erosion.enabled:
            gl.glBindImageTexture(0, erosion.heightmapId, 0, gl.GL_FALSE, 0, gl.GL_READ_WRITE, gl.GL_RGBA32F)
            gl.glBindImageTexture(1, erosion.dropsPosSpeedId, 0, gl.GL_FALSE, 0, gl.GL_READ_WRITE, gl.GL_RGBA32F)
            gl.glBindImageTexture(2, erosion.dropsVolSedId, 0, gl.GL_FALSE, 0, gl.GL_READ_WRITE, gl.GL_RGBA32F)

            gl.glUseProgram(erosion.erosionId)
            location = gl.glGetUniformLocation(erosion.erosionId, 'started')
            gl.glUniform1i(location, erosion.started)

            gl.glDispatchCompute(erosion.width, erosion.height, 1)
            gl.glMemoryBarrier(gl.GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)
            gl.glUseProgram(0)

            erosion.counter += 1
            erosion.started = 1
            if erosion.counter == 500:
                erosion.enabled = False

        if erosion.save:
            counter = 0
            filename = "heightmap" + str(counter) + ".png"
            while(path.isfile(path.abspath(filename))):
                counter += 1
                filename = "heightmap" + str(counter) + ".png"
            self.export_texture(filename)
            erosion.save = False

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
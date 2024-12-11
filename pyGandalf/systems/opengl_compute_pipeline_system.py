import OpenGL.GL as gl
from pyGandalf.systems.system import System
from pyGandalf.scene.entity import Entity
from pyGandalf.scene.components import Component
from pyGandalf.scene.components import ComputeComponent
from pyGandalf.utilities.opengl_shader_lib import OpenGLShaderLib
from pyGandalf.utilities.opengl_material_lib import MaterialInstance
from pyGandalf.utilities.definitions import SHADERS_PATH
from pathlib import Path
import os

class OpenGLComputePipelineSystem(System):

    def on_create_entity(self, entity: Entity, components: Component | tuple[Component]):
        compute: ComputeComponent = components
        computeCode = OpenGLShaderLib().load_from_file(compute.shader)
        #compute_rel_path = Path(os.path.relpath(compute.shader, SHADERS_PATH))

        compute_shader = OpenGLShaderLib().compile_shader(computeCode, gl.GL_COMPUTE_SHADER)
        shader_program = gl.glCreateProgram()
        gl.glAttachShader(shader_program, compute_shader)
        gl.glLinkProgram(shader_program)

        if not gl.glGetProgramiv(shader_program, gl.GL_LINK_STATUS):
            raise RuntimeError(gl.glGetProgramInfoLog(shader_program).decode('utf-8'))

        gl.glDeleteShader(compute_shader)
        print("Created")

        gl.glBindImageTexture(2, compute.textures[0], 0, gl.GL_FALSE, 0, gl.GL_READ_WRITE, gl.GL_R32F)
        compute.ID = shader_program

    def on_update_entity(self, ts: float, entity: Entity, components: Component | tuple[Component]):
        compute: ComputeComponent = components

        gl.glUseProgram(compute.ID)

        for uniformName, uniformType in compute.uniformsDictionary.items():
            location = gl.glGetUniformLocation(compute.ID, uniformName)
            uniformDataIndex = list(compute.uniformsDictionary.keys()).index(uniformName)
            MaterialInstance.update_uniform(location, uniformName, compute.uniformsData[uniformDataIndex], uniformType)

        gl.glDispatchCompute(compute.workGroupsX, compute.workGroupsY, compute.workGroupsZ)
        gl.glMemoryBarrier(gl.GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)
        gl.glUseProgram(0)


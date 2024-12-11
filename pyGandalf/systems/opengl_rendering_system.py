from pyGandalf.core.application import Application
from pyGandalf.scene.components import Component, TransformComponent, MaterialComponent
from pyGandalf.systems.system import System, SystemState
from pyGandalf.systems.light_system import LightSystem
from pyGandalf.renderer.opengl_renderer import OpenGLRenderer

from pyGandalf.utilities.opengl_texture_lib import OpenGLTextureLib, TextureData, TextureDescriptor
from pyGandalf.utilities.opengl_material_lib import OpenGLMaterialLib
from pyGandalf.utilities.mesh_lib import MeshLib

from pyGandalf.scene.scene_manager import SceneManager
from pyGandalf.scene.entity import Entity

from pyGandalf.utilities.logger import logger

import glm
import glfw
import numpy as np
import OpenGL.GL as gl

class OpenGLStaticMeshRenderingSystem(System):
    """
    The system responsible for rendering static meshes.
    """

    def on_create_system(self):
        self.pre_pass_material = None
        self.SHADOW_WIDTH = 1024
        self.SHADOW_HEIGHT = 1024

        self.framebuffer_id = gl.glGenFramebuffers(1)

        depth_texture_descriptor = TextureDescriptor()
        depth_texture_descriptor.internal_format=gl.GL_DEPTH_COMPONENT
        depth_texture_descriptor.format=gl.GL_DEPTH_COMPONENT
        depth_texture_descriptor.type=gl.GL_FLOAT
        depth_texture_descriptor.wrap_s=gl.GL_CLAMP_TO_BORDER
        depth_texture_descriptor.wrap_t=gl.GL_CLAMP_TO_BORDER
        depth_texture_descriptor.min_filter=gl.GL_NEAREST
        depth_texture_descriptor.max_filter=gl.GL_NEAREST

        # Create depth texture
        OpenGLTextureLib().build('depth_texture', TextureData(image_bytes=None, width=self.SHADOW_WIDTH, height=self.SHADOW_WIDTH), descriptor=depth_texture_descriptor)
        depth_texture_id = OpenGLTextureLib().get_id('depth_texture')

        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_texture_id)

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.framebuffer_id)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_TEXTURE_2D, depth_texture_id, 0)
        gl.glDrawBuffer(gl.GL_NONE)
        gl.glReadBuffer(gl.GL_NONE)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def on_create_entity(self, entity: Entity, components: Component | tuple[Component]):
        mesh, material, transform = components

        mesh.render_pipeline = None
        mesh.index_buffer = None
        mesh.buffers.clear()

        material.instance = OpenGLMaterialLib().get(material.name)

        if material.instance == None:
            logger.error(f"No such material exists: '{material.name}'")
            return

        if mesh.load_from_file == True:
            mesh_instance = MeshLib().get(mesh.name)
            mesh.attributes = [mesh_instance.vertices, mesh_instance.normals, mesh_instance.texcoords]
            mesh.indices = mesh_instance.indices

        if len(mesh.attributes) == 0:
            return
        
        mesh.batch = OpenGLRenderer().add_batch(mesh, material)

    def on_update_system(self, ts: float):
        for components in self.get_filtered_components():
            mesh, entity_material, transform = components
            if mesh.changed:
                self.on_create_entity(mesh, components)
                mesh.changed = False

        if OpenGLRenderer().get_shadows_enabled():
            # Create the depth only pre-pass material is not already created
            if self.pre_pass_material == None:
                self.pre_pass_material = MaterialComponent('M_DepthPrePass')
                self.pre_pass_material.instance = OpenGLMaterialLib().get('M_DepthPrePass')

            OpenGLRenderer().resize(self.SHADOW_WIDTH, self.SHADOW_HEIGHT)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.framebuffer_id)
            gl.glClear(gl.GL_DEPTH_BUFFER_BIT)

            # Depth only pre-pass
            for components in self.get_filtered_components():
                mesh, entity_material, transform = components

                if entity_material.instance.descriptor.cast_shadows == False:
                    continue

                if len(mesh.attributes) == 0:
                    continue

                # Bind vao
                OpenGLRenderer().set_pipeline(mesh)
                # Bind vbo(s) and ebo
                OpenGLRenderer().set_buffers(mesh)
                # Bind shader program and set material properties
                OpenGLRenderer().set_bind_groups(self.pre_pass_material)

                self.update_prepass_uniforms(transform.world_matrix, self.pre_pass_material)

                if (mesh.indices is None):
                    OpenGLRenderer().draw(mesh, self.pre_pass_material)
                else:
                    OpenGLRenderer().draw_indexed(mesh, self.pre_pass_material)

            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

            if OpenGLRenderer().use_framebuffer:
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, OpenGLRenderer().framebuffer_id)
                OpenGLRenderer().resize(int(OpenGLRenderer().framebuffer_width), int(OpenGLRenderer().framebuffer_height))
            else:
                OpenGLRenderer().resize(Application().get_window().width, Application().get_window().height)

            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # Color pass
        for components in self.get_filtered_components():
            mesh, material, transform = components

            if len(mesh.attributes) == 0:
                continue

            if material.instance == None:
                continue

            # Bind vao
            OpenGLRenderer().set_pipeline(mesh)
            # Bind vbo(s) and ebo
            OpenGLRenderer().set_buffers(mesh)
            # Bind shader program and set material properties
            OpenGLRenderer().set_bind_groups(material)

            self.update_uniforms(transform.world_matrix, material)

            if (mesh.indices is None):
                OpenGLRenderer().draw(mesh, material)
            else:
                OpenGLRenderer().draw_indexed(mesh, material)

    def update_prepass_uniforms(self, model, material: MaterialComponent):
        light_system: LightSystem = SceneManager().get_active_scene().get_system(LightSystem)
        
        if light_system is not None:
            if light_system.get_state() != SystemState.PAUSE:
                for components in light_system.get_filtered_components():
                    light, transform = components

                    if material.instance.has_uniform('u_LightSpaceMatrix'):
                        light_projection = SceneManager().get_main_camera().projection
                        light_view = glm.lookAt(transform.get_world_position(), glm.vec3(0.0), glm.vec3(0.0, 1.0, 0.0))
                        material.instance.set_uniform('u_LightSpaceMatrix', light_projection * light_view)

                    break

        if material.instance.has_uniform('u_Model'):
            material.instance.set_uniform('u_Model', model)

    def update_uniforms(self, model, material: MaterialComponent):
        light_system: LightSystem = SceneManager().get_active_scene().get_system(LightSystem)

        light_positions: list[glm.vec3] = []
        light_colors: list[glm.vec3] = []
        light_intensities: list[np.float32] = []
        
        if light_system is not None:
            if light_system.get_state() != SystemState.PAUSE:
                for components in light_system.get_filtered_components():
                    light, transform = components
                    light_colors.append(light.color)
                    light_positions.append(transform.get_world_position())
                    light_intensities.append(light.intensity)

                    # NOTE: Only works with one light, adding more will keep the last.
                    if material.instance.has_uniform('u_LightSpaceMatrix'):
                        light_projection = SceneManager().get_main_camera().projection
                        light_view = glm.lookAt(transform.get_world_position(), glm.vec3(0.0), glm.vec3(0.0, 1.0, 0.0))
                        material.instance.set_uniform('u_LightSpaceMatrix', light_projection * light_view)

        count = len(light_positions)

        assert count <= 16, f"Maximum supported lights for WebGPU backend are 16, but {count} are defined"

        if count != 0:
            if material.instance.has_uniform('u_LightPositions'):
                material.instance.set_uniform('u_LightPositions', glm.array(light_positions))
            if material.instance.has_uniform('u_LightColors'):
                material.instance.set_uniform('u_LightColors', glm.array(light_colors))
            if material.instance.has_uniform('u_LightIntensities'):
                material.instance.set_uniform('u_LightIntensities', np.asarray(light_intensities, dtype=np.float32))
            if material.instance.has_uniform('u_LightCount'):
                material.instance.set_uniform('u_LightCount', count)
            if material.instance.has_uniform('u_Glossiness'):
                material.instance.set_uniform('u_Glossiness', material.instance.data.glossiness)
        elif light_system is not None:
            if material.instance.has_uniform('u_LightCount'):
                material.instance.set_uniform('u_LightCount', 0)

        camera = SceneManager().get_main_camera()
        if camera != None:
            if material.instance.has_uniform('u_ModelViewProjection'):
                material.instance.set_uniform('u_ModelViewProjection', camera.projection * camera.view * model)
            if material.instance.has_uniform('u_Model'):
                material.instance.set_uniform('u_Model', model)
            if material.instance.has_uniform('u_View'):
                material.instance.set_uniform('u_View', camera.view)
            if material.instance.has_uniform('u_Projection'):
                material.instance.set_uniform('u_Projection', camera.projection)
            if material.instance.has_uniform('u_ViewProjection'):
                material.instance.set_uniform('u_ViewProjection', camera.projection * glm.mat4(glm.mat3(camera.view)))
        else:
            if material.instance.has_uniform('u_ModelViewProjection'):
                material.instance.set_uniform('u_ModelViewProjection', glm.mat4(1.0))
            if material.instance.has_uniform('u_Model'):
                material.instance.set_uniform('u_Model', glm.mat4(1.0))
            if material.instance.has_uniform('u_View'):
                material.instance.set_uniform('u_View', glm.mat4(1.0))
            if material.instance.has_uniform('u_Projection'):
                material.instance.set_uniform('u_Projection', glm.mat4(1.0))
            if material.instance.has_uniform('u_ViewProjection'):
                material.instance.set_uniform('u_ViewProjection', glm.mat4(1.0))

        if material.instance.has_uniform('u_ViewPosition'):
            camera_entity = SceneManager().get_main_camera_entity()
            if camera_entity != None:
                camera_transform = SceneManager().get_active_scene().get_component(camera_entity, TransformComponent)
                if camera_transform != None and not camera_transform.static:
                    material.instance.set_uniform('u_ViewPosition', camera_transform.get_world_position())

        if material.instance.has_uniform('u_Color'):
            material.instance.set_uniform('u_Color', material.instance.data.color.rgb)

        if material.instance.has_uniform('scale'):
            material.instance.set_uniform('scale', int(material.instance.data.scale))

        if material.instance.has_uniform('elevationScale'):
            material.instance.set_uniform('elevationScale', int(material.instance.data.elevationScale))

        if material.instance.has_uniform('mapSize'):
            material.instance.set_uniform('mapSize', int(material.instance.data.mapSize - 1))

        if material.instance.has_uniform('tiling'):
            material.instance.set_uniform('tiling', material.instance.data.tiling)

        if material.instance.has_uniform('cameraCoords'):
            material.instance.set_uniform('cameraCoords', material.instance.data.cameraCoords)

        if material.instance.has_uniform('a'):
            material.instance.set_uniform('a', material.instance.data.a)
        if material.instance.has_uniform('b'):
            material.instance.set_uniform('b', material.instance.data.b)
        if material.instance.has_uniform('fallOffHeight'):
            material.instance.set_uniform('fallOffHeight', material.instance.data.fallOffHeight)
        if material.instance.has_uniform('fallOffEnabled'):
            material.instance.set_uniform('fallOffEnabled', int(material.instance.data.fallOffEnabled))
        if material.instance.has_uniform('useTextures'):
            material.instance.set_uniform('useTextures', int(material.instance.data.useTextures))
        if material.instance.has_uniform('fallOffType'):
            material.instance.set_uniform('fallOffType', material.instance.data.fallOffType)
        if material.instance.has_uniform('underWaterRavines'):
            material.instance.set_uniform('underWaterRavines', int(material.instance.data.underWaterRavines))
        if material.instance.has_uniform('seed'):
            material.instance.set_uniform('seed', material.instance.data.seed)
        if material.instance.has_uniform('octaves'):
            material.instance.set_uniform('octaves', int(material.instance.data.octaves))
        if material.instance.has_uniform('frequency'):
            material.instance.set_uniform('frequency', material.instance.data.frequency)
        if material.instance.has_uniform('persistence'):
            material.instance.set_uniform('persistence', material.instance.data.persistence)
        if material.instance.has_uniform('lacunarity'):
            material.instance.set_uniform('lacunarity', material.instance.data.lacunarity)
        if material.instance.has_uniform('turbulance'):
            material.instance.set_uniform('turbulance', int(material.instance.data.Turbulance))
        if material.instance.has_uniform('Ridges'):
            material.instance.set_uniform('Ridges', int(material.instance.data.Ridges))
        if material.instance.has_uniform('ridgesStrength'):
            material.instance.set_uniform('ridgesStrength', material.instance.data.RidgesStrength)
        if material.instance.has_uniform('metallic'):
            material.instance.set_uniform('metallic', material.instance.data.metallic)

        if material.instance.has_uniform('roughness'):
            material.instance.set_uniform('roughness', material.instance.data.roughness)

        if material.instance.has_uniform('ao'):
            material.instance.set_uniform('ao', material.instance.data.ao)

        if material.instance.has_uniform('_Height_of_blend'):
            material.instance.set_uniform('_Height_of_blend', material.instance.data.heightOfBlend)

        if material.instance.has_uniform('_Depth'):
            material.instance.set_uniform('_Depth', material.instance.data.depthOfBlend)

        if material.instance.has_uniform('maxHeight'):
            material.instance.set_uniform('maxHeight', material.instance.data.maxHeight)
            
        if material.instance.has_uniform('heightOfSnow'):
            material.instance.set_uniform('heightOfSnow', material.instance.data.heightOfSnow)
                    
        if material.instance.has_uniform('heightOfGrass'):
            material.instance.set_uniform('heightOfGrass', material.instance.data.heightOfGrass)
            
        if material.instance.has_uniform('rockColor'):
            material.instance.set_uniform('rockColor', material.instance.data.rockColor.rgba)
            
        if material.instance.has_uniform('rockBlendAmount'):
            material.instance.set_uniform('rockBlendAmount', material.instance.data.rockBlendAmount)
            
        if material.instance.has_uniform('slopeTreshold'):
            material.instance.set_uniform('slopeTreshold', material.instance.data.slopeTreshold)
            
        if material.instance.has_uniform('snowColor'):
            material.instance.set_uniform('snowColor', material.instance.data.snowColor.rgba)
            
        if material.instance.has_uniform('grassColor'):
            material.instance.set_uniform('grassColor', material.instance.data.grassColor.rgba)
            
        if material.instance.has_uniform('sandColor'):
            material.instance.set_uniform('sandColor', material.instance.data.sandColor.rgba)

        if material.instance.has_uniform('u_Time'):
            material.instance.set_uniform('u_Time', float(glfw.get_time()))
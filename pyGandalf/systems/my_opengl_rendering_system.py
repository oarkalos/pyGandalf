from pyGandalf.core.application import Application
from pyGandalf.scene.components import Component, TransformComponent, MaterialComponent, CameraControllerComponent, CameraComponent, InfoComponent
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

class MyOpenGLRenderingSystem(System):
     
    def createFrameBuffer(self):
        frameBuffer = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, frameBuffer)
        gl.glDrawBuffer(gl.GL_COLOR_ATTACHMENT0)
        return frameBuffer

    def createDepthTextureAttachment(self, width: int, height: int):
        depthTexture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depthTexture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_DEPTH_COMPONENT32, width, height, 0, gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, depthTexture, 0)
        return depthTexture

    def createDepthBufferAttachment(self, width: int, height: int):
        depthBuffer = gl.glGenRenderbuffers(1)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, depthBuffer)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT, width, height)
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_RENDERBUFFER, depthBuffer)
        return depthBuffer
    
    def inevrtCamera(self, pitch):
        main_camera = SceneManager().get_main_camera_entity()
        camera = SceneManager().get_active_scene().get_component(main_camera, CameraComponent)
        transform = SceneManager().get_active_scene().get_component(main_camera, TransformComponent)

        transform.rotation = glm.vec3(-pitch, transform.rotation.y, 0)

        T = glm.translate(glm.mat4(1.0), glm.vec3(transform.translation.x, transform.translation.y, transform.translation.z))
        R = glm.quat(glm.vec3(glm.radians(transform.rotation.x), glm.radians(transform.rotation.y), glm.radians(transform.rotation.z)))
        S = glm.scale(glm.mat4(1.0), glm.vec3(transform.scale.x, transform.scale.y, transform.scale.z))
            
        transform.quaternion = R
        transform.local_matrix = T * glm.mat4(R) * S
        transform.world_matrix = transform.local_matrix

        if not transform.static:
            camera.view = glm.inverse(transform.world_matrix)
        
            match camera.type:
                case CameraComponent.Type.PERSPECTIVE:
                    camera.projection = glm.perspective(glm.radians(camera.fov), camera.aspect_ratio, camera.near, camera.far)
                case CameraComponent.Type.ORTHOGRAPHIC:
                    camera.projection = glm.ortho(-camera.aspect_ratio * camera.zoom_level, camera.aspect_ratio * camera.zoom_level, -camera.zoom_level, camera.zoom_level, camera.near, camera.far)

    def on_create_system(self):
        self.pre_pass_material = None
        self.SHADOW_WIDTH = 1024
        self.SHADOW_HEIGHT = 1024
        self.REFLECTION_WIDTH = 320
        self.REFLECTION_HEIGHT = 180
        self.REFRACTION_WIDTH = 1280
        self.REFRACTION_HEIGHT = 720
        self.waterPlane = 2.05
        self.offset = 0.0
        self.wave_speed = 0.02

        self.framebuffer_id = gl.glGenFramebuffers(1)

        depth_texture_descriptor = TextureDescriptor()
        depth_texture_descriptor.internal_format=gl.GL_DEPTH_COMPONENT
        depth_texture_descriptor.format=gl.GL_DEPTH_COMPONENT
        depth_texture_descriptor.type=gl.GL_FLOAT
        depth_texture_descriptor.wrap_s=gl.GL_CLAMP_TO_BORDER
        depth_texture_descriptor.wrap_t=gl.GL_CLAMP_TO_BORDER
        depth_texture_descriptor.min_filter=gl.GL_NEAREST
        depth_texture_descriptor.max_filter=gl.GL_NEAREST

        reflectrefract_textrure_descriptor = TextureDescriptor()
        reflectrefract_textrure_descriptor.internal_format=gl.GL_RGB
        reflectrefract_textrure_descriptor.format=gl.GL_RGB

        # Create depth texture
        OpenGLTextureLib().build('depth_texture', TextureData(image_bytes=None, width=self.SHADOW_WIDTH, height=self.SHADOW_WIDTH), descriptor=depth_texture_descriptor)
        depth_texture_id = OpenGLTextureLib().get_id('depth_texture')

        # Create reflection texture
        OpenGLTextureLib().build('reflection_texture', TextureData(image_bytes=None, width=self.REFLECTION_WIDTH, height=self.REFLECTION_HEIGHT), descriptor=reflectrefract_textrure_descriptor)
        reflection_texture_id = OpenGLTextureLib().get_id('reflection_texture')

        # Create refraction texture
        OpenGLTextureLib().build('refraction_texture', TextureData(image_bytes=None, width=self.REFRACTION_WIDTH, height=self.REFRACTION_HEIGHT), descriptor=reflectrefract_textrure_descriptor)
        refraction_texture_id = OpenGLTextureLib().get_id('refraction_texture')

        # Create depth refraction texture
        OpenGLTextureLib().build('depth_refraction_texture', TextureData(image_bytes=None, width=self.REFRACTION_WIDTH, height=self.REFRACTION_HEIGHT), descriptor=depth_texture_descriptor)
        depth_refraction_texture_id = OpenGLTextureLib().get_id('depth_refraction_texture')

        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_texture_id)

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.framebuffer_id)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_TEXTURE_2D, depth_texture_id, 0)
        gl.glDrawBuffer(gl.GL_NONE)
        gl.glReadBuffer(gl.GL_NONE)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        self.reflection_frameBuffer_id = self.createFrameBuffer()
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, reflection_texture_id, 0)
        self.createDepthBufferAttachment(self.REFLECTION_WIDTH, self.REFLECTION_HEIGHT)
        gl.glReadBuffer(gl.GL_NONE)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        self.refraction_frameBuffer_id = self.createFrameBuffer()
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, refraction_texture_id, 0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_refraction_texture_id)
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, depth_refraction_texture_id, 0)
        gl.glReadBuffer(gl.GL_NONE)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        self.initializedWaterPlane = False
        self.water = None

    def on_create_entity(self, entity: Entity, components: Component | tuple[Component]):
        mesh, material, transform = components
        if (not self.initializedWaterPlane):
            if(SceneManager().get_active_scene().get_component(entity, InfoComponent).tag == 'sea_floor'):
                self.water = entity
                self.initializedWaterPlane = True

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
        if not (self.water == None):
            self.waterPlane = SceneManager().get_active_scene().get_component(self.water, TransformComponent).translation.y + 0.05
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

        #Water pass render reflection
        OpenGLRenderer().resize(self.REFLECTION_WIDTH, self.REFLECTION_HEIGHT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.reflection_frameBuffer_id)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)

        main_camera = SceneManager().get_main_camera_entity()
        camera_transform = SceneManager().get_active_scene().get_component(main_camera, TransformComponent)
        camera_controller = SceneManager().get_active_scene().get_component(main_camera, CameraControllerComponent)
        distance = 2.0 * (camera_transform.translation.y - self.waterPlane)
        camera_transform.translation = glm.vec3(camera_transform.translation.x, camera_transform.translation.y - distance, camera_transform.translation.z)
        self.inevrtCamera(-camera_controller.pitch)

        for components in self.get_filtered_components():
            mesh, material, transform = components

            if len(mesh.attributes) == 0:
                continue

            if material.name == 'M_WoodFloor':
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
            if material.instance.has_uniform('waterPlane'):
                material.instance.set_uniform('waterPlane', self.waterPlane)
            if material.instance.has_uniform('clip'):
                material.instance.set_uniform('clip', 1)

            if (mesh.indices is None):
                OpenGLRenderer().draw(mesh, material)
            else:
                OpenGLRenderer().draw_indexed(mesh, material)

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        if OpenGLRenderer().use_framebuffer:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, OpenGLRenderer().framebuffer_id)
            OpenGLRenderer().resize(int(OpenGLRenderer().framebuffer_width), int(OpenGLRenderer().framebuffer_height))
        else:
            OpenGLRenderer().resize(Application().get_window().width, Application().get_window().height)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        camera_transform.translation = glm.vec3(camera_transform.translation.x, camera_transform.translation.y + distance, camera_transform.translation.z)
        self.inevrtCamera(camera_controller.pitch)
        
        #Water pass render refraction
        OpenGLRenderer().resize(self.REFRACTION_WIDTH, self.REFRACTION_HEIGHT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.refraction_frameBuffer_id)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)

        for components in self.get_filtered_components():
            mesh, material, transform = components

            if len(mesh.attributes) == 0:
                continue

            if material.name == 'M_WoodFloor':
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
            if material.instance.has_uniform('clip'):
                material.instance.set_uniform('clip', 2)
            if material.instance.has_uniform('waterPlane'):
                material.instance.set_uniform('waterPlane', self.waterPlane)

            if (mesh.indices is None):
                OpenGLRenderer().draw(mesh, material)
            else:
                OpenGLRenderer().draw_indexed(mesh, material)

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        if OpenGLRenderer().use_framebuffer:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, OpenGLRenderer().framebuffer_id)
            OpenGLRenderer().resize(int(OpenGLRenderer().framebuffer_width), int(OpenGLRenderer().framebuffer_height))
        else:
            OpenGLRenderer().resize(Application().get_window().width, Application().get_window().height)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

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
        gl.glDisable(gl.GL_BLEND)

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

        if material.instance.has_uniform('clip'):
            material.instance.set_uniform('clip', 0)

        if material.instance.has_uniform('cameraCoords'):
            material.instance.set_uniform('cameraCoords', material.instance.data.cameraCoords)

        if material.instance.has_uniform('useTextures'):
            material.instance.set_uniform('useTextures', int(material.instance.data.useTextures))

        if material.instance.has_uniform('metallic'):
            material.instance.set_uniform('metallic', material.instance.data.metallic)

        if material.instance.has_uniform('roughness'):
            material.instance.set_uniform('roughness', material.instance.data.roughness)

        if material.instance.has_uniform('generate'):
            material.instance.set_uniform('generate', material.instance.data.generate)

        if material.instance.has_uniform('ao'):
            material.instance.set_uniform('ao', material.instance.data.ao)

        if material.instance.has_uniform('offset'):
            self.offset += self.wave_speed * Application().delta_time
            self.offset %= 1
            material.instance.set_uniform('offset', self.offset)

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
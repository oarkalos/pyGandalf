from pyGandalf.scene.entity import Entity

import glm
import wgpu

import uuid
from enum import Enum

class Component(object):
    pass

class InfoComponent(Component):
    def __init__(self, tag = 'UnnamedEntity'):
        self.tag = tag
        self.enabled = True

class TransformComponent(Component):
    def __init__(self, translation: glm.vec3, rotation: glm.vec3, scale: glm.vec3):
        self.translation = translation
        self.rotation = rotation
        self.scale = scale

        self.local_matrix = glm.mat4(1.0)
        self.world_matrix = glm.mat4(1.0)
        self.quaternion = glm.quat()

        self.dirty = True
        self.static = False
    
    def get_world_position(self) -> glm.vec3:
        return (self.world_matrix * glm.vec4(self.translation, 1.0)).xyz

class LinkComponent(Component):
    def __init__(self, parent: Entity):
        self.parent_id = 0
        if parent != None:
            self.parent_id = parent.id
        self.parent: Entity = parent
        self.prev_parent: Entity = parent
        self.children: list[Entity] = []

class CameraComponent(Component):
    class Type(Enum):
        PERSPECTIVE = 1
        ORTHOGRAPHIC = 2

    def __init__(self, fov, aspect_ratio, near, far, zoom_level, type: Type, primary = True):
        self.zoom_level = zoom_level
        self.fov = fov
        self.near = near
        self.far = far
        self.aspect_ratio = aspect_ratio
        self.type: CameraComponent.Type = type

        self.view = glm.mat4(1.0)
        if type is CameraComponent.Type.ORTHOGRAPHIC:
            self.projection = glm.ortho(-self.aspect_ratio * self.zoom_level, self.aspect_ratio * self.zoom_level, -self.zoom_level, self.zoom_level, self.near, self.far)
        elif type is CameraComponent.Type.PERSPECTIVE:
            self.projection = glm.perspective(glm.radians(self.fov), self.aspect_ratio, self.near, self.far)
        self.view_projection = glm.mat4(1.0)

        self.primary = primary

class CameraControllerComponent(Component):
    def __init__(self, movement_speed = 3.5, mouse_sensitivity = 1.25):
        self.front = glm.vec3(0.0, 0.0, 1.0)
        self.right = glm.vec3(1.0, 0.0, 0.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)
        self.world_up = glm.vec3(0.0, 1.0, 0.0)
        self.yaw = -90.0
        self.pitch = 0.0
        self.movement_speed = movement_speed
        self.mouse_sensitivity = mouse_sensitivity
        self.zoom = 45.0
        self.prev_mouse_x = 0.0
        self.prev_mouse_y = 0.0

class StaticMeshComponent(Component):
    def __init__(self, name, attributes = None, indices = None):
        self.name = name
        self.attributes = attributes
        self.indices = indices

        self.render_pipeline = None
        self.buffers = []
        self.index_buffer = None
        self.changed = False

        self.batch = -1
        self.load_from_file = True if attributes == None else False

        self.hash = uuid.uuid4()

class MaterialComponent(Component):            
    def __init__(self, name: str):
        self.name = name
        self.instance = None

class LightComponent(Component):
    def __init__(self, color, intensity):
        self.color = color
        self.intensity = intensity

class WebGPUComputeComponent(Component):
    def __init__(self, compute_shader: str, textures: list[str], entry_point: str) -> None:
        self.shader: str = compute_shader
        self.pipeline: wgpu.GPUComputePipeline = None
        self.encoder: wgpu.GPUCommandEncoder = None
        self.map_buffers: list[wgpu.GPUBuffer] = []
        self.bind_groups: list[wgpu.GPUBindGroup] = []

        self.uniform_buffers: dict[str, wgpu.GPUBuffer] = {}
        self.input_storage_buffers: dict[str, wgpu.GPUBuffer] = {}
        self.output_storage_buffers: dict[str, wgpu.GPUBuffer] = {}
        self.other_uniforms: dict = {}
        self.buffer_types: dict[str, CPUBuffer] = {}

        self.textures: list[str] = textures

        self.work_group = -1
        self.invocation_count_x = 1
        self.invocation_count_y = 1
        self.invocation_count_z = 1
        self.entry_point = entry_point
        self.output: list[bytearray] = []
        self.output_ready = False
        self.dispatch = False

class TerrainComponent(Component):
    def __init__(self, scale, elevationScale, mapSize, patch_resolution, vertices_per_patch, camera = None):
        self.minHeight = 0.0
        self.maxHeight = 0.0
        self.scale : float = scale
        self.elevationScale : float = elevationScale
        self.mapSize : int = mapSize
        self.patch_resolution : int = patch_resolution
        self.vertices_per_patch : int = vertices_per_patch
        self.cameraCoords: glm.vec2 = glm.vec2(0.0, 0.0)
        self.camera: Entity = camera

        self.generate: bool = False
        self.cameraMoved: bool = False

        self.minTerrainHeight = []
        self.maxTerrainHeight = []
        self.heightMap = []
        self.heights = []
        self.vertices = []
        self.indices = []

from enum import Enum

class GUIType(Enum):
    DRAG = 0
    INPUT = 1
    CHECKBOX = 2
    COMBO = 3

class GUIData:
    def __init__(self, speed = 0, min = 0, max = 0, type: GUIType = GUIType.DRAG, comboValues = ['', '']):
        self.speed = speed
        self.min = min
        self.max = max
        self.type = type
        self.comboValues = comboValues

class ComputeComponent(Component):
    def __init__(self, compute_shader: str, textures: list[int], x: int, y: int, z: int, uniformsData = [], guiData: dict[str, GUIData] = {}):
        self.shader: str = compute_shader
        self.textures: list[int] = textures
        self.dispatch = False

        self.ID: int = 0
        self.uniformsDictionary: dict[str, str] = {}
        self.uniformsData = uniformsData
        self.guiData: dict[str, GUIData] = guiData
        self.workGroupsX = x
        self.workGroupsY = y
        self.workGroupsZ = z
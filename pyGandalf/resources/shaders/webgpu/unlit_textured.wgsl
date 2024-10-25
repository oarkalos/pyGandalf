struct VertexInput {
    @location(0) a_Position : vec3<f32>,
    @location(1) a_TexCoord: vec2<f32>,
};
struct VertexOutput {
    @builtin(position) v_Position: vec4<f32>,
    @location(0) v_TexCoord : vec2<f32>,
};

struct UniformData {
    viewMatrix: mat4x4f,
    projectionMatrix: mat4x4f,
    objectColor: vec4f,
};

struct ModelData {
    modelMatrix: array<mat4x4f, 512>,
};

@group(0) @binding(0) var<uniform> u_UniformData: UniformData;
@group(0) @binding(1) var<storage, read> u_ModelData: ModelData;
@group(1) @binding(0) var u_Texture: texture_2d<f32>;
@group(1) @binding(1) var u_Sampler: sampler;

@vertex
fn vs_main(@builtin(instance_index) ID: u32, in: VertexInput) -> VertexOutput {
    var out: VertexOutput;
    var mvp: mat4x4f = u_UniformData.projectionMatrix * u_UniformData.viewMatrix * u_ModelData.modelMatrix[ID];
    out.v_Position = mvp * vec4<f32>(in.a_Position, 1.0);
    out.v_TexCoord = in.a_TexCoord;
    return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
    // gamma correct
    let physical_color = pow(u_UniformData.objectColor.rgb, vec3<f32>(2.2));
    return textureSample(u_Texture, u_Sampler, in.v_TexCoord) * vec4<f32>(physical_color, u_UniformData.objectColor.a);
}
struct VertexInput {
    @location(0) a_Position : vec3<f32>
};
struct VertexOutput {
    @builtin(position) v_Position: vec4<f32>
};

struct UniformData {
    projectionMatrix: mat4x4f,
    viewMatrix: mat4x4f,
    modelMatrix: mat4x4f,
};

@group(0) @binding(0) var<uniform> u_UniformData: UniformData;

@vertex
fn vs_main(in: VertexInput) -> VertexOutput {
    var out: VertexOutput;
    var mvp: mat4x4f = u_UniformData.projectionMatrix * u_UniformData.viewMatrix * u_UniformData.modelMatrix;
    out.v_Position = mvp * vec4<f32>(in.a_Position, 1.0);
    return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
    // gamma correct
    let physical_color = pow(vec3<f32>(1.0, 1.0, 1.0), vec3<f32>(2.2));
    return vec4<f32>(physical_color, 1.0);
}
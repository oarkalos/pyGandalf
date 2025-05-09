struct VertexInput {
    @location(0) a_Position : vec3<f32>,
    @location(1) a_Normal: vec3<f32>,
    @location(2) a_TexCoord: vec2<f32>,
    @location(3) a_Tangent: vec3<f32>,
    @location(4) a_Bitangent: vec3<f32>,
};
struct VertexOutput {
    @builtin(position) v_Position: vec4<f32>,
    @location(0) v_TexCoord : vec2<f32>,
    @location(1) v_TangentViewPos : vec3<f32>,
    @location(2) v_TangentFragPos : vec3<f32>,
    @location(3) v_TangentLightPos0 : vec3<f32>,
    @location(4) v_TangentLightPos1 : vec3<f32>,
    @location(5) v_TangentLightPos2 : vec3<f32>,
    @location(6) v_TangentLightPos3 : vec3<f32>,
};

struct UniformData {
    viewMatrix: mat4x4f,
    projectionMatrix: mat4x4f,
    objectColor: vec4f,
    viewPosition: vec4<f32>,
    lightPositions: array<vec4f, 4>,
    lightColors: array<vec4f, 4>,
    lightIntensities: array<vec4f, 4>,
    lightCount: f32,
};

struct ModelData {
    modelMatrix: array<mat4x4f, 512>,
};

@group(0) @binding(0) var<uniform> u_UniformData: UniformData;
@group(0) @binding(1) var<storage, read> u_ModelData: ModelData;
@group(1) @binding(0) var u_AlbedoTexture: texture_2d<f32>;
@group(1) @binding(1) var u_AlbedoSampler: sampler;
@group(1) @binding(2) var u_NormalMap: texture_2d<f32>;
@group(1) @binding(3) var u_NormalSampler: sampler;
@group(1) @binding(4) var u_DisplacementMap: texture_2d<f32>;
@group(1) @binding(5) var u_DisplacementSampler: sampler;

@vertex
fn vs_main(@builtin(instance_index) ID: u32, in: VertexInput) -> VertexOutput {
    let modelMat3x3 = mat3x3f(u_ModelData.modelMatrix[ID][0].xyz, u_ModelData.modelMatrix[ID][1].xyz, u_ModelData.modelMatrix[ID][2].xyz);
    var normalMatrix: mat3x3f = transpose(modelMat3x3);

    var T: vec3f = normalize(normalMatrix * in.a_Tangent);
    var B: vec3f = normalize(normalMatrix * in.a_Bitangent);
    var N: vec3f = normalize(normalMatrix * in.a_Normal);

    // Re-orthogonalize T with respect to N
    T = normalize(T - dot(T, N) * N);

    var TBN: mat3x3f = transpose(mat3x3f(T, B, N));

    var out: VertexOutput;
    var mvp: mat4x4f = u_UniformData.projectionMatrix * u_UniformData.viewMatrix * u_ModelData.modelMatrix[ID];
    out.v_Position = mvp * vec4<f32>(in.a_Position, 1.0);
    out.v_TexCoord = in.a_TexCoord;
    out.v_TangentViewPos = TBN * u_UniformData.viewPosition.xyz;
    out.v_TangentFragPos = TBN * (u_ModelData.modelMatrix[ID] * vec4f(in.a_Position, 1.0)).xyz;

    if (u_UniformData.lightCount == 1) {
        out.v_TangentLightPos0 = TBN * u_UniformData.lightPositions[0].xyz;
    } else if (u_UniformData.lightCount == 2) {
        out.v_TangentLightPos0 = TBN * u_UniformData.lightPositions[0].xyz;
        out.v_TangentLightPos1 = TBN * u_UniformData.lightPositions[1].xyz;
    } else if (u_UniformData.lightCount == 3) {
        out.v_TangentLightPos0 = TBN * u_UniformData.lightPositions[0].xyz;
        out.v_TangentLightPos1 = TBN * u_UniformData.lightPositions[1].xyz;
        out.v_TangentLightPos2 = TBN * u_UniformData.lightPositions[2].xyz;
    } else if (u_UniformData.lightCount == 4) {
        out.v_TangentLightPos0 = TBN * u_UniformData.lightPositions[0].xyz;
        out.v_TangentLightPos1 = TBN * u_UniformData.lightPositions[1].xyz;
        out.v_TangentLightPos2 = TBN * u_UniformData.lightPositions[2].xyz;
        out.v_TangentLightPos3 = TBN * u_UniformData.lightPositions[3].xyz;
    }

    return out;
}

const heightScale: f32 = 0.1;

fn ParallaxMapping(texCoords: vec2f, viewDir: vec3f) -> vec2f
{
    let height: f32 = textureSample(u_DisplacementMap, u_DisplacementSampler, texCoords).r;     
    return texCoords - viewDir.xy * (height * heightScale);
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
    var camDir: vec3<f32> = normalize(in.v_TangentViewPos - in.v_TangentFragPos);
    var offsetTexCoord: vec2f = ParallaxMapping(in.v_TexCoord, camDir);

    if (offsetTexCoord.x > 1.0 || offsetTexCoord.y > 1.0 || offsetTexCoord.x < 0.0 || offsetTexCoord.y < 0.0) {
    	discard;
    }

    var textureColor: vec4<f32> = textureSample(u_AlbedoTexture, u_AlbedoSampler, offsetTexCoord);

    var normal: vec3f = textureSample(u_NormalMap, u_NormalSampler, offsetTexCoord).rgb;

    normal = normalize(normal);
    var diffuse: vec3<f32> = vec3<f32>(0.0);
    var specular: vec3<f32> = vec3<f32>(0.0);
    var ambient: vec3<f32> = vec3<f32>(0.0);

    var ambientCoefficient: f32 = 0.1;
    var u_Glossiness: f32 = 3.0;

    for (var f: f32 = 0.0; f < u_UniformData.lightCount; f = f + 1.0) {
        var i: i32 = i32(f);
        var tangentLightPos: vec3f;

        if (i == 0) {
            tangentLightPos = in.v_TangentLightPos0;
        } else if (i == 1) {
            tangentLightPos = in.v_TangentLightPos1;
        } else if (i == 2) {
            tangentLightPos = in.v_TangentLightPos2;
        } else if (i == 3) {
            tangentLightPos = in.v_TangentLightPos3;
        }

        // ambient
        ambient = ambient + u_UniformData.lightColors[i].rgb * u_UniformData.lightIntensities[i].x;

        // diffuse
        var lightDir: vec3<f32> = normalize(tangentLightPos - in.v_TangentFragPos);
        var diff: f32 = max(dot(lightDir, normal), 0.0);
        var D: vec3<f32> = diff * u_UniformData.lightColors[i].rgb * u_UniformData.lightIntensities[i].x;
        diffuse = diffuse + D;

        // specular
        var halfwayDir: vec3<f32> = normalize(lightDir + camDir);
        var spec: f32 = pow(max(dot(normal, halfwayDir), 0.0), 32.0) * u_Glossiness;
        var S: vec3<f32> = u_UniformData.lightColors[i].rgb * spec * u_UniformData.lightIntensities[i].x;
        specular = specular + S;
    }

    ambient = ambientCoefficient * ambient;

    var BlinnPhong: vec3<f32> = ambient + diffuse + specular;
    var finalColor: vec3<f32> = textureColor.rgb * BlinnPhong;
    finalColor = pow(finalColor, vec3<f32>(1.0 / 1.2));

    // gamma correct
    let physicalColor = pow(finalColor * u_UniformData.objectColor.rgb, vec3<f32>(2.2));
    
    return vec4f(physicalColor.r, physicalColor.g, physicalColor.b, textureColor.a);
}
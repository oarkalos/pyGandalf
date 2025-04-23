#version 430 core

in vec4 clipSpace;
in vec2 texCoord;
in vec3 toCameraVector;
in vec3 v_Position;

out vec4 color;

uniform sampler2D reflection;
uniform sampler2D refraction;
uniform sampler2D dudvMap;
uniform sampler2D normalMap;
uniform sampler2D depthMap;
uniform float offset;

// Light properties
uniform int u_LightCount = 0;
uniform vec3 u_LightPositions[16];
uniform vec3 u_LightColors[16];
uniform float u_LightIntensities[16];

const float waveStrength = 0.03;
const float shineDamper = 8.0;
const float reflectivity = 0.3;

float invLerp(float a, float b, float v){
    return ((v - a) / (b - a));
}

void main(){
    vec2 normalizedDeviceCoords = ((clipSpace.xy/clipSpace.w) / 2.0) + 0.5;
    vec2 refractionCoords = vec2(normalizedDeviceCoords.x, normalizedDeviceCoords.y);
    vec2 reflectionCoords = vec2(normalizedDeviceCoords.x, -normalizedDeviceCoords.y);

    float nearPlane = 0.1;
    float farPlane = 2000.0;
    float depth = texture(depthMap, refractionCoords).r;
    float floorDistance = 2.0 * nearPlane * farPlane / (farPlane + nearPlane - (2.0 * depth - 1.0) * (farPlane - nearPlane));

    depth = gl_FragCoord.z;
    float waterDistance = 2.0 * nearPlane * farPlane / (farPlane + nearPlane - (2.0 * depth - 1.0) * (farPlane - nearPlane));
    float waterDepth = floorDistance - waterDistance;
    float smoothFactor = clamp(waterDepth / 20.0, 0.0, 1.0);

    vec2 distortedTexCoords = texture(dudvMap, vec2(texCoord.x + offset, texCoord.y)).rg * 0.1;
    distortedTexCoords = texCoord + vec2(distortedTexCoords.x, distortedTexCoords.y + offset);

    vec2 totalDistortion = (texture(dudvMap, distortedTexCoords).rg * 2.0 - 1.0) * waveStrength * smoothFactor;

    refractionCoords += totalDistortion;
    refractionCoords = clamp(refractionCoords, 0.001, 0.999);

    reflectionCoords += totalDistortion;
    reflectionCoords.x = clamp(reflectionCoords.x, 0.001, 0.999);
    reflectionCoords.y = clamp(reflectionCoords.y, -0.999, -0.001);

    vec4 refractionColor = texture(refraction, refractionCoords);
    vec4 reflectionColor = texture(reflection, reflectionCoords);

    vec4 normalColour = texture(normalMap, distortedTexCoords);
    vec3 normal = vec3(normalColour.r * 2.0 - 1.0, normalColour.b * 3.0, normalColour * 2.0 - 1.0);
    normal = normalize(normal);

    vec3 viewVector = normalize(toCameraVector);
    float fresnelFactor = dot(viewVector, normal);
    fresnelFactor = pow(fresnelFactor, 0.5);
    fresnelFactor = clamp(fresnelFactor, 0.0, 1.0);

    vec3 lightDir = v_Position - u_LightPositions[0];
    vec3 reflectedLight = reflect(normalize(lightDir), normal);
    float specular = max(dot(reflectedLight, viewVector), 0.0);
    specular = pow(specular, shineDamper);
    vec3 specularHighlights = u_LightColors[0] * specular * reflectivity * smoothFactor;

    color = mix(reflectionColor, refractionColor, fresnelFactor);
    color = mix(color, vec4(0.0, 0.3, 0.5, 1.0), 0.3) + vec4(specularHighlights, 0.0);
    color.a = clamp(waterDepth / 5.0, 0.0, 1.0);
}
#version 410 core

in vec3 v_Position;
in vec3 v_Normal;
in vec2 v_TexCoord;

// Camera properties
uniform vec3 u_ViewPosition = vec3(0.0, 0.0, 10.0);

//Material properties
uniform vec3  u_Color;
uniform float metallic;
uniform float roughness;
uniform float ao;

// Light properties
uniform int u_LightCount = 0;
uniform float u_LightIntensities[16];
uniform vec3 u_LightPositions[16];
uniform vec3 u_LightColors[16];

//Terrain shading parameters
uniform float _Height_of_blend;
uniform float _Depth;
uniform float maxHeight;
uniform float heightOfSnow;
uniform float heightOfGrass;
uniform vec4 rockColor;
uniform float rockBlendAmount;
uniform float slopeTreshold;
uniform vec4 snowColor;
uniform vec4 grassColor;
uniform vec4 sandColor;

out vec4 FragColor;

const float PI = 3.14159265359;

float invLerp(float a, float b, float v){
    return ((v - a) / (b - a));
}

float DistributionGGX(vec3 N, vec3 H, float roughness)
{
    float a = roughness*roughness;
    float a2 = a*a;
    float NdotH = max(dot(N, H), 0.0);
    float NdotH2 = NdotH*NdotH;

    float nom   = a2;
    float denom = (NdotH2 * (a2 - 1.0) + 1.0);
    denom = PI * denom * denom;

    return nom / denom;
}

float GeometrySchlickGGX(float NdotV, float roughness)
{
    float r = (roughness + 1.0);
    float k = (r*r) / 8.0;

    float nom   = NdotV;
    float denom = NdotV * (1.0 - k) + k;

    return nom / denom;
}

float GeometrySmith(vec3 N, vec3 V, vec3 L, float roughness)
{
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    float viewG = GeometrySchlickGGX(NdotV, roughness);
    float lightG = GeometrySchlickGGX(NdotL, roughness);

    return lightG * viewG;
}

vec3 fresnelSchlick(float cosTheta, vec3 F0)
{
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

vec4 PBR(vec3 albedo, vec3 normal, float met, float rough, float ambientOcc){
    vec3 N = normal;
    vec3 V = normalize(u_ViewPosition - v_Position);
    // calculate reflectance at normal incidence; if dia-electric (like plastic) use F0 
    // of 0.04 and if it's a metal, use the albedo color as F0 (metallic workflow)    
    vec3 F0 = vec3(0.04); 
    F0 = mix(F0, albedo, met);

    // reflectance equation
    vec3 Lo = vec3(0.0);
    for(int i = 0; i < u_LightCount; ++i) 
    {
        // calculate per-light radiance
        vec3 L = normalize(u_LightPositions[i] - v_Position);
        vec3 H = normalize(V + L);
        float distance = length(u_LightPositions[i] - v_Position);
        float attenuation = 1.0 / (distance * distance);
        vec3 radiance = u_LightColors[i] * attenuation * u_LightIntensities[i];

        // Cook-Torrance BRDF
        float NDF = DistributionGGX(N, H, rough);   
        float G   = GeometrySmith(N, V, L, rough);      
        vec3 F    = fresnelSchlick(max(dot(H, V), 0.0), F0);
           
        vec3 numerator    = NDF * G * F; 
        float denominator = 4.0 * max(dot(N, V), 0.0) * max(dot(N, L), 0.0) + 0.0001; // + 0.0001 to prevent divide by zero
        vec3 specular = numerator / denominator;

        // kS is equal to Fresnel
        vec3 kS = F;
        // for energy conservation, the diffuse and specular light can't
        // be above 1.0 (unless the surface emits light); to preserve this
        // relationship the diffuse component (kD) should equal 1.0 - kS.
        vec3 kD = vec3(1.0) - kS;
        // multiply kD by the inverse metalness such that only non-metals 
        // have diffuse lighting, or a linear blend if partly metal (pure metals
        // have no diffuse light).
        kD *= 1.0 - met;	  

        // scale light by NdotL
        float NdotL = max(dot(N, L), 0.0);        

        // add to outgoing radiance Lo
        Lo += (kD * albedo / PI + specular) * radiance * NdotL;  // note that we already multiplied the BRDF by the Fresnel (kS) so we won't multiply by kS again
    }

    // ambient lighting (note that the next IBL tutorial will replace 
    // this ambient lighting with environment lighting).
    vec3 ambient = vec3(0.05) * albedo * ambientOcc;
    
    vec3 color = ambient + Lo;

    // HDR tonemapping
    color = color / (color + vec3(1.0));
    // gamma correct
    color = pow(color, vec3(1.0 / 2.2)); 

    return vec4(color, 1.0);

}

vec3 HeightSplattingValues(float snowHeight, float grassHeight){
    //Lerp values
    vec3 values;
    float heightInRange = invLerp(0.0, maxHeight, v_Position.y);

    //x above snow
    values.x = invLerp(snowHeight, 1.0, heightInRange);
    //y above grass
    values.y = invLerp(grassHeight, snowHeight, heightInRange);
    //z below grass (sand)
    values.z = invLerp(0.0, grassHeight, heightInRange);

    return values;
}

vec4 HeightSplatting(vec4 Color1, vec4 Color2, float frac){
    float opac1 = _Height_of_blend - frac;
    float opac2 = frac;
    float ma = max(Color1.a+ opac1, Color2.a + opac2) - _Depth;

    float b1 = max(Color1.a+ opac1 - ma, 0);
    float b2 = max(Color2.a+ opac2 - ma, 0);

    return vec4((Color1.rgb * b1 + Color2.rgb * b2) / (b1 + b2), 1.0);
}

float SlopeBlending(float Slope, float BlendAmount, float NormalY){
    float slope = 1-NormalY; // slope = 0 when terrain is completely flat
    float grassBlendHeight = Slope* (1-BlendAmount);
    return 1 - clamp((slope-grassBlendHeight)/(Slope-grassBlendHeight), 0.0, 1.0);
}

void main()
{
    vec3 N = v_Normal;
    vec3 values = HeightSplattingValues(heightOfSnow, heightOfGrass);
    vec4 color = HeightSplatting(HeightSplatting(sandColor, grassColor, values.z), HeightSplatting(grassColor, snowColor, values.x), values.y);
    float rockBlendValue = SlopeBlending(slopeTreshold, rockBlendAmount, N.y);
    vec4 finalWithRock = HeightSplatting(rockColor, color, rockBlendValue);

    FragColor = PBR(finalWithRock.xyz, N, metallic, roughness, ao);
}
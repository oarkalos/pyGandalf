#version 430 core

in vec3 v_Position;
in vec3 v_Normal;
in vec2 v_TexCoord;

//albedo textures
uniform sampler2D grassAlbedo;
uniform sampler2D snowAlbedo;
uniform sampler2D sandAlbedo;

//normal textures
uniform sampler2D grassNormal;
uniform sampler2D snowNormal;
uniform sampler2D sandNormal;

//mask textures
uniform sampler2D grassMask;
uniform sampler2D snowMask;
uniform sampler2D sandMask;

//rock textures
uniform sampler2D rockAlbedo;
uniform sampler2D rockNormal;
uniform sampler2D rockMask;

in float height;

uniform ivec2 tiling;
uniform int useTextures = 1;
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
uniform int mapSize;

out vec4 FragColor;

const float PI = 3.14159265359;

// Easy trick to get tangent-normals to world-space to keep PBR code simplified.
// Don't worry if you don't get what's going on; you generally want to do normal 
// mapping the usual way for performance anyways; I do plan make a note of this 
// technique somewhere later in the normal mapping tutorial.
vec3 getNormalFromMap(sampler2D u_NormalMap, vec2 uv)
{
    vec3 tangentNormal = texture(u_NormalMap, uv).xyz * 2.0 - 1.0;

    vec3 Q1  = dFdx(v_Position);
    vec3 Q2  = dFdy(v_Position);
    vec2 st1 = dFdx(uv);
    vec2 st2 = dFdy(uv);

    vec3 N   = normalize(v_Normal);
    vec3 T  = normalize(Q1*st2.t - Q2*st1.t);
    vec3 B  = -normalize(cross(N, T));
    mat3 TBN = mat3(T, B, N);

    return normalize(TBN * tangentNormal);
}

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

vec2 Bombing(vec2 UVS){
    vec2 floorUVS = floor(UVS);
    vec3 p3 = fract(floorUVS.xyx * vec3(0.1031, 0.1030, 0.0973));

    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy) + UVS;
}

vec4 UVSBombimg1(){
    vec2 UVS1 = Bombing(floor(v_TexCoord)) + v_TexCoord;
    vec2 UVS2 = Bombing(floor(v_TexCoord + vec2(0.5, 10))) + v_TexCoord;
    return vec4(UVS1.x, UVS1.y, UVS2.x, UVS2.y);
}

vec4 UVSBombimg2(){
    vec2 UVS1 = Bombing(floor(v_TexCoord + vec2(-10, 0.5))) + v_TexCoord;
    vec2 UVS2 = Bombing(floor(v_TexCoord + vec2(20.5, 0.5))) + v_TexCoord;
    return vec4(UVS1.x, UVS1.y, UVS2.x, UVS2.y);
}

vec2 UVSBombimgLerValue(){
    vec2 tmp = (fract(tiling) * vec2(2.0, 2.0)) - vec2(1.0, 1.0);
    return smoothstep(vec2(0.25, 0.25), vec2(0.75, 0.75), abs(tmp));
}

vec4 calculateAlbedo(vec3 values, vec2 UVS1, vec2 UVS2, vec2 UVS3, vec2 UVS4, vec2 lerpValues){
    vec4 grassColor = mix(mix(texture(grassAlbedo, UVS1), texture(grassAlbedo, UVS2), lerpValues.r), mix(texture(grassAlbedo, UVS3), texture(grassAlbedo, UVS4), lerpValues.r), lerpValues.g);
    vec4 snowColor = mix(mix(texture(snowAlbedo, UVS1), texture(snowAlbedo, UVS2), lerpValues.r), mix(texture(snowAlbedo, UVS3), texture(snowAlbedo, UVS4), lerpValues.r), lerpValues.g);
    vec4 sandColor = mix(mix(texture(sandAlbedo, UVS1), texture(sandAlbedo, UVS2), lerpValues.r), mix(texture(sandAlbedo, UVS3), texture(sandAlbedo, UVS4), lerpValues.r), lerpValues.g);
    return HeightSplatting(HeightSplatting(sandColor, grassColor, values.z), HeightSplatting(grassColor, snowColor, values.x), values.y);
}

vec4 calculateNormal(vec3 values, vec2 UVS1, vec2 UVS2, vec2 UVS3, vec2 UVS4, vec2 lerpValues){
    vec4 grassNormal = vec4(mix(mix(getNormalFromMap(grassNormal, UVS1), getNormalFromMap(grassNormal, UVS2), lerpValues.r), mix(getNormalFromMap(grassNormal, UVS3), getNormalFromMap(grassNormal, UVS4), lerpValues.r), lerpValues.g), 1.0);
    vec4 snowNormal = vec4(mix(mix(getNormalFromMap(snowNormal, UVS1), getNormalFromMap(snowNormal, UVS2), lerpValues.r), mix(getNormalFromMap(snowNormal, UVS3), getNormalFromMap(snowNormal, UVS4), lerpValues.r), lerpValues.g), 1.0);
    vec4 sandNormal = vec4(mix(mix(getNormalFromMap(sandNormal, UVS1), getNormalFromMap(sandNormal, UVS2), lerpValues.r), mix(getNormalFromMap(sandNormal, UVS3), getNormalFromMap(sandNormal, UVS4), lerpValues.r), lerpValues.g), 1.0);
    return HeightSplatting(HeightSplatting(sandNormal, grassNormal, values.z), HeightSplatting(grassNormal, snowNormal, values.x), values.y);
}

vec4 calculateMask(vec3 values, vec2 UVS1, vec2 UVS2, vec2 UVS3, vec2 UVS4, vec2 lerpValues){
    vec4 grassMask = mix(mix(texture(grassMask, UVS1), texture(grassMask, UVS2), lerpValues.r), mix(texture(grassMask, UVS3), texture(grassMask, UVS4), lerpValues.r), lerpValues.g);
    vec4 snowMask = mix(mix(texture(snowMask, UVS1), texture(snowMask, UVS2), lerpValues.r), mix(texture(snowMask, UVS3), texture(snowMask, UVS4), lerpValues.r), lerpValues.g);
    vec4 sandMask = mix(mix(texture(sandMask, UVS1), texture(sandMask, UVS2), lerpValues.r), mix(texture(sandMask, UVS3), texture(sandMask, UVS4), lerpValues.r), lerpValues.g);
    float roughness = mix(mix(sandMask.a, grassMask.a, values.z), mix(grassMask.a, snowMask.a, values.x), values.y);
    return vec4(HeightSplatting(HeightSplatting(sandMask, grassMask, values.z), HeightSplatting(grassMask, snowMask, values.x), values.y).xyz, roughness);
}

void main()
{
    vec3 values = HeightSplattingValues(heightOfSnow, heightOfGrass);
    float rockBlendValue = SlopeBlending(slopeTreshold, rockBlendAmount, v_Normal.y);

    vec3 normal;
    vec4 mask;
    vec4 albedo;
    vec4 rockA = rockColor;
    vec4 rockN = vec4(0.0);
    vec4 rockM = vec4(0.0);

    if(useTextures == 0){
        albedo = HeightSplatting(HeightSplatting(sandColor, grassColor, values.z), HeightSplatting(grassColor, snowColor, values.x), values.y);
        normal = v_Normal;
        mask = vec4(metallic, ao, 1.0, roughness);
    }else{
        vec4 bombing1 = UVSBombimg1();
        vec4 bombing2 = UVSBombimg2();
        vec2 lerpValues = UVSBombimgLerValue();

        albedo = calculateAlbedo(values, vec2(bombing1.xy), vec2(bombing1.zw), vec2(bombing2.xy), vec2(bombing2.zw), lerpValues);
        normal = calculateNormal(values, vec2(bombing1.xy), vec2(bombing1.zw), vec2(bombing2.xy), vec2(bombing2.zw), lerpValues).xyz;
        mask = calculateMask(values, vec2(bombing1.xy), vec2(bombing1.zw), vec2(bombing2.xy), vec2(bombing2.zw), lerpValues);

        rockA = texture(rockAlbedo, v_TexCoord);
        rockN = vec4(getNormalFromMap(rockNormal, v_TexCoord), 1.0);
        rockM = texture(rockMask, v_TexCoord);

        normal = HeightSplatting(rockN, vec4(normal, 1.0), rockBlendValue).xyz;
        mask = HeightSplatting(rockM, mask, rockBlendValue);
    }
    albedo = HeightSplatting(rockA, albedo, rockBlendValue);

    FragColor = PBR(albedo.xyz, normal, mask.r, mask.a, mask.b);
}
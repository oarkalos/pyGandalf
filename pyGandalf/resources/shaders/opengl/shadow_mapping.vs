#version 330 core
layout(location = 0) in vec3 a_Position;
layout(location = 1) in vec3 a_Normal;
layout(location = 2) in vec2 a_TexCoord;

uniform mat4 u_ModelViewProjection;
uniform mat4 u_Model;

uniform mat4 u_LightSpaceMatrix;

out vec3 v_Position;
out vec3 v_Normal;
out vec2 v_TexCoord;
out vec4 v_FragPosLightSpace;

void main()
{
    v_Position = (u_Model * vec4(a_Position, 1.0)).xyz;
    v_Normal = (transpose(inverse(u_Model)) * vec4(a_Normal, 0.0)).xyz;
    v_TexCoord = a_TexCoord;
    v_FragPosLightSpace = u_LightSpaceMatrix * vec4(v_Position, 1.0);

    gl_Position = u_ModelViewProjection * vec4(a_Position, 1.0);
}
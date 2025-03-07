#version 430 core
layout (location = 0) in vec3 a_Position;
layout (location = 1) in vec2 a_TexCoord;

uniform mat4 u_ModelViewProjection;
uniform mat4 u_Model;

// Camera position
uniform vec3 u_ViewPosition = vec3(0.0, 0.0, 10.0);

out vec4 clipSpace;
out vec2 texCoord;
out vec3 toCameraVector;
out vec3 v_Position;

void main()
{
    vec4 worldPosition = u_Model * vec4(a_Position, 1.0);
    v_Position = worldPosition.xyz;
    clipSpace = u_ModelViewProjection * vec4(a_Position, 1.0);
    texCoord = a_TexCoord * 10.0;
    toCameraVector = u_ViewPosition - worldPosition.xyz;
    gl_Position = clipSpace;
}
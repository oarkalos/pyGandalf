#version 450

#extension GL_NV_mesh_shader : require

layout(local_size_x = 25) in;
layout(triangles, max_vertices = 100, max_primitives = 50) out;

// Custom vertex output block
layout (location = 0) out PerVertexData
{
  vec4 color;
} v_out[];  // [max_vertices]

uniform mat4 u_ModelViewProjection;
uniform mat4 u_Model;

const vec3 vertices[4] = {vec3(-0.025,-0.025,0), vec3(-0.025,0.025,0), vec3(0.025,-0.025,0), vec3(0.025,0.025,0)};
const vec3 colors[4] = {vec3(1.0,0.0,0.0), vec3(0.0,1.0,0.0), vec3(0.0,0.0,1.0), vec3(1.0,1.0,0.0)};

void main()
{
  uint mi = gl_WorkGroupID.x;
  uint thread_id = gl_LocalInvocationID.x;
  float offsetX = 5.1 * (mi / 128);
  float offsetY = 5.1 * (mi % 128);

  uint verticesOffset = thread_id * 4;
  uint indicesOffset = thread_id * 6;

  float localOffsetX = thread_id / 5;
  float localOffsetY = thread_id % 5;
  gl_MeshVerticesNV[0 + verticesOffset].gl_Position = u_ModelViewProjection * vec4(vertices[0 + verticesOffset].x + 0.05 * (offsetY + localOffsetY), vertices[0 + verticesOffset].y + 0.05 * (offsetX + localOffsetX), 0.0, 1.0); 
  gl_MeshVerticesNV[1 + verticesOffset].gl_Position = u_ModelViewProjection * vec4(vertices[1 + verticesOffset].x + 0.05 * (offsetY + localOffsetY), vertices[1 + verticesOffset].y + 0.05 * (offsetX + localOffsetX), 0.0, 1.0); 
  gl_MeshVerticesNV[2 + verticesOffset].gl_Position = u_ModelViewProjection * vec4(vertices[2 + verticesOffset].x + 0.05 * (offsetY + localOffsetY), vertices[2 + verticesOffset].y + 0.05 * (offsetX + localOffsetX), 0.0, 1.0); 
  gl_MeshVerticesNV[3 + verticesOffset].gl_Position = u_ModelViewProjection * vec4(vertices[3 + verticesOffset].x + 0.05 * (offsetY + localOffsetY), vertices[3 + verticesOffset].y + 0.05 * (offsetX + localOffsetX), 0.0, 1.0); 
  // Vertices color
  v_out[0 + verticesOffset].color = vec4(colors[0], 1.0);
  v_out[1 + verticesOffset].color = vec4(colors[1], 1.0);
  v_out[2 + verticesOffset].color = vec4(colors[2], 1.0);
  v_out[3 + verticesOffset].color = vec4(colors[3], 1.0);

  gl_PrimitiveIndicesNV[0 + indicesOffset] = 2 + verticesOffset;
  gl_PrimitiveIndicesNV[1 + indicesOffset] = 1 + verticesOffset;
  gl_PrimitiveIndicesNV[2 + indicesOffset] = 0 + verticesOffset;
  gl_PrimitiveIndicesNV[3 + indicesOffset] = 2 + verticesOffset;
  gl_PrimitiveIndicesNV[4 + indicesOffset] = 3 + verticesOffset;
  gl_PrimitiveIndicesNV[5 + indicesOffset] = 1 + verticesOffset;

  // Vertices position


  // Triangle indices

  // Number of triangles  
  gl_PrimitiveCountNV = 98;
}
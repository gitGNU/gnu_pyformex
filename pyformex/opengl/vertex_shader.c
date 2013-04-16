uniform mat4 modelview;
uniform mat4 projection;
uniform vec3 objectColor;
uniform float pointSize;

void main()
{
  // Transforming The Vertex
  //gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;
  gl_Position = projection * modelview * gl_Vertex;
  //gl_Position =  projection * gl_ModelViewMatrix * gl_Vertex;
  //gl_Position = gl_ProjectionMatrix * modelview * gl_Vertex;
}

uniform mat4 perspective;
uniform vec3 objectColor;
uniform float pointSize;

void main()
{
  // Transforming The Vertex
  gl_Position = gl_Vertex * perspective;
}

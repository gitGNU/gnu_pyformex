#ifdef GL_ES
precision mediump float;
#endif

attribute vec3 vertexPosition;
attribute vec3 vertexNormal;
attribute vec3 vertexColor;
attribute vec2 vertexTexturePos;
attribute float vertexScalar;

uniform mat4 modelview;     // xtk: view
uniform mat4 projection;    // xtk: perspective
uniform int colormode;      // xtk useObjectColor;

uniform mat4 objectTransform;
uniform bool useScalars;
uniform bool scalarsReplaceMode;
uniform float scalarsMin;
uniform float scalarsMax;
uniform vec3 scalarsMinColor;
uniform vec3 scalarsMaxColor;
uniform float scalarsMinThreshold;
uniform float scalarsMaxThreshold;
uniform int scalarsInterpolation;
uniform vec3 objectColor;

uniform float pointsize;

varying float fDiscardNow;
varying vec4 fVertexPosition;
varying vec3 fragmentColor;
varying vec2 fragmentTexturePos;
varying vec3 fVertexNormal;
varying vec3 fTransformedVertexNormal;

void main()
{
  // Pass color to fragment shader
  // Set single color
  if (colormode == 1) {
    fragmentColor = objectColor;
  } else if (colormode == 3) {
    fragmentColor = gl_Color;
  } else {
    // Default black opaque
    fragmentColor = vec4(0.,0.,1.,1.);
  }

  /* TODO:

     ALL gl_ variables should be changed to corresponding
     uploaded attributes.
  */


  // Pass normal to fragment shader
  fVertexNormal = gl_Normal;
  fTransformedVertexNormal = modelview * vec4(gl_Normal,1.);

  // setup vertex Point Size
  gl_PointSize = pointsize;
  // Transforming The Vertex
  gl_Position = projection * modelview * gl_Vertex;
}

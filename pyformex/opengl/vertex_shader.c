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

uniform bool lighting;
uniform float ambient;
uniform float diffuse;
uniform float specular;
uniform vec3 specmat;
uniform float shininess;
uniform float alpha;
uniform vec3 light; // Currently 1 light: need multiple


varying float fDiscardNow;
varying vec4 fVertexPosition;
varying vec4 fragColor;        // Final fragment color, including opacity
varying vec3 fragmentColor;
varying vec2 fragmentTexturePos;
varying vec3 fTransformedVertexNormal;


void main()
{
  if (colormode == 1) {
    // Single color
    fragmentColor = objectColor;
  } else if (colormode == 3) {
    // Vertex color
    fragmentColor = vertexColor;
  } else {
    // Default black
    fragmentColor = vec3(0.,0.,0.);
  }

  // Add in lighting
  if (lighting) {
    fTransformedVertexNormal = mat3(modelview[0].xyz,modelview[1].xyz,modelview[2].xyz) * vertexNormal;

    vec3 nNormal = normalize(fTransformedVertexNormal);
    vec3 nlight = normalize(light);

    /* // t2 += ' vec3 lightDirection = vec3(-10.0, 4.0, -20.0); */
    /* // I liked the following better */
    /* vec3 lightDirection = vec3(0,0,-10); */
    /* lightDirection = normalize(lightDirection); */
    /* vec3 eyeDirection = normalize(-fVertexPosition.xyz); */
    /* vec3 reflectionDirection = reflect(-lightDirection, nNormal); */
    /* // t2 += ' vec3 reflectionDirection = nNormal; <-- to disable reflection */
    /* // configure specular (10.0 is material property), diffuse and ambient */
    /* float specular = pow(max(dot(reflectionDirection, eyeDirection), 0.0), 10.0); */
    float ndiffuse = diffuse * max(dot(nNormal,nlight),0.0);

    // total color is sum of ambient, diffuse and specular
    vec3 fcolor = fragmentColor;
    fragmentColor = vec3(fcolor * ambient +
			 fcolor * ndiffuse +
			 specmat * specular);
  }

  // Add in opacity
  fragColor = vec4(fragmentColor,alpha);

  // setup vertex Point Size
  gl_PointSize = pointsize;
  // Transforming The Vertex
  gl_Position = projection * modelview * vec4(vertexPosition,1.0);
}

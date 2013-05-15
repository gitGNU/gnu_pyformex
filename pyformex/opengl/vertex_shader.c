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
uniform float shininess;
uniform float opacity;

varying float fDiscardNow;
varying vec4 fVertexPosition;
varying vec4 fragColor;        // Final fragment color, including opacity
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
    // Default black
    fragmentColor = vec3(0.,0.,0.);
  }


  if (lighting) {
    // Pass normal to fragment shader
    fVertexNormal = gl_Normal;
    fTransformedVertexNormal = modelview * vec4(gl_Normal,1.);

    // compute lighted color
    vec3 nNormal = normalize(fTransformedVertexNormal);
    if (fVertexNormal == vec3(0.0,0.0,0.0)) {
      // ignore the lighting if the normals are 0,0,0
      fragmentColor = vec3(1.,1.,0.);
    } else {
      vec3 light = vec3(1.0, 1.0, 1.0);
      /* // t2 += ' vec3 lightDirection = vec3(-10.0, 4.0, -20.0); */
      /* // I liked the following better */
      /* vec3 lightDirection = vec3(0,0,-10); */
      /* lightDirection = normalize(lightDirection); */
      /* vec3 eyeDirection = normalize(-fVertexPosition.xyz); */
      /* vec3 reflectionDirection = reflect(-lightDirection, nNormal); */
      /* // t2 += ' vec3 reflectionDirection = nNormal; <-- to disable reflection */
      /* // configure specular (10.0 is material property), diffuse and ambient */
      /* float specular = pow(max(dot(reflectionDirection, eyeDirection), 0.0), 10.0); */
      float ndiffuse = diffuse * max(dot(nNormal,light),0.0);
      ndiffuse = diffuse * abs(dot(nNormal,light));
      //float ndiffuse = diffuse * max(dot(fVertexNormal,light),0.0);
      // .. and now setup the fragment color using these three values and the
      // opacity
      fragmentColor = vec3(fragmentColor * ambient +
			   fragmentColor * diffuse +
			   vec3(0.0,0.0,0.0) * specular);
    }
    //fragmentColor = vec3(0.,0.,1.);
  }


  // Final color including opacity
  fragColor = vec4(fragmentColor,opacity);

  /* TODO:

     ALL gl_ variables should be changed to corresponding
     uploaded attributes.
  */

  // setup vertex Point Size
  gl_PointSize = pointsize;
  // Transforming The Vertex
  gl_Position = projection * modelview * gl_Vertex;
}

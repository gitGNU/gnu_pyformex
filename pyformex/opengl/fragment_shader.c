#ifdef GL_ES
precision mediump float;
#endif

uniform bool usePicking;
uniform bool useTexture;
uniform bool volumeTexture;
uniform bool useLabelMapTexture; // which activates textureSampler2
uniform sampler2D textureSampler;
uniform sampler2D textureSampler2;
uniform float labelmapOpacity;
uniform float volumeLowerThreshold;
uniform float volumeUpperThreshold;
uniform float volumeScalarMin;
uniform float volumeScalarMax;
uniform vec3 volumeScalarMinColor;
uniform vec3 volumeScalarMaxColor;
uniform float volumeWindowLow;
uniform float volumeWindowHigh;

uniform bool lighting;
uniform float ambient;
uniform float diffuse;
uniform float specular;
uniform float shininess;
uniform float opacity;

varying float fDiscardNow;
varying vec4 fVertexPosition;
varying vec3 fragmentColor;
varying vec2 fragmentTexturePos;
varying vec3 fVertexNormal;
varying vec3 fTransformedVertexNormal;

void main(void) {
  if (lighting) {
    vec3 nNormal = normalize(fTransformedVertexNormal);
    if (fVertexNormal == vec3(0.0,0.0,0.0)) {
      // ignore the lighting if the normals are 0,0,0
      gl_FragColor = vec4(1.,0.,0., opacity);
    } else {
      // compute lighted color
      vec3 light = vec3(0.0, 1.0, 1.0);
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
      // .. and now setup the fragment color using these three values and the
      // opacity
      gl_FragColor = vec4(fragmentColor * ambient +
			  fragmentColor * diffuse +
			  vec3(0.2,0.0,0.0) * specular,
			  opacity);
    }
  } else {
    // no light
    gl_FragColor = vec4(0.,0.,1., opacity);
  }
}

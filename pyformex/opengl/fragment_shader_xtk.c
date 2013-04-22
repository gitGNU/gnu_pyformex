#ifdef GL_ES
precision mediump float;
#endif

uniform bool usePicking;
uniform bool useTexture;
uniform bool volumeTexture;
uniform bool useLabelMapTexture; // which activates textureSampler2
uniform sampler2D textureSampler;
uniform sampler2D textureSampler2;
uniform float objectOpacity;
uniform float labelmapOpacity;
uniform float volumeLowerThreshold;
uniform float volumeUpperThreshold;
uniform float volumeScalarMin;
uniform float volumeScalarMax;
uniform vec3 volumeScalarMinColor;
uniform vec3 volumeScalarMaxColor;
uniform float volumeWindowLow;
uniform float volumeWindowHigh;

varying float fDiscardNow;
varying vec4 fVertexPosition;
varying vec3 fragmentColor;
varying vec2 fragmentTexturePos;
varying vec3 fVertexNormal;
varying vec3 fTransformedVertexNormal;

void main(void) {
 if (fDiscardNow > 0.0) {
   discard; // really discard now
 }
  // in picking mode, we don't want any extras but just the plain color
 if (usePicking) {
   gl_FragColor = vec4(fragmentColor, 1.0);
 } else if (useTexture) {
   vec4 texture1 = texture2D(textureSampler,fragmentTexturePos);
   vec4 textureSum = texture1;
  // perform window level
   if (volumeTexture) {
     float _windowLow = (volumeWindowLow / volumeScalarMax);
     float _windowHigh = (volumeWindowHigh / volumeScalarMax);
     vec3 _minrange = vec3(_windowLow,_windowLow,_windowLow);
     vec3 _maxrange = vec3(_windowHigh,_windowHigh,_windowHigh);
     vec3 fac = _maxrange - _minrange;
     textureSum = vec4((textureSum.r - _minrange)/fac,1);
  // map volume scalars to a linear color gradient
     textureSum = textureSum.r * vec4(volumeScalarMaxColor,1) + (1.0 - textureSum.r) * vec4(volumeScalarMinColor,1);
   }
   if (useLabelMapTexture) { // special case for label maps
     vec4 texture2 = texture2D(textureSampler2,fragmentTexturePos);
     if (texture2.a > 0.0) { // check if this is the background
  // label
       if (labelmapOpacity < 1.0) { // transparent label map
         textureSum = mix(texture2, textureSum, 1.0 - labelmapOpacity);
       } else {
         textureSum = texture2; // fully opaque label map
       }
     }
   }
  // threshold functionality for 1-channel volumes
   if (volumeTexture) {
     float _volumeLowerThreshold = (volumeLowerThreshold / volumeScalarMax);
     float _volumeUpperThreshold = (volumeUpperThreshold / volumeScalarMax);
     if (texture1.r < _volumeLowerThreshold ||
         texture1.r > _volumeUpperThreshold) {
       discard;
     };
   };
   gl_FragColor = textureSum;
   gl_FragColor.a = objectOpacity;
 } else {
  // configure advanced lighting
   vec3 nNormal = normalize(fTransformedVertexNormal);
  // .. ignore the lightning if the normals are 0,0,0
   if (fVertexNormal == vec3(0.0,0.0,0.0)) {
     gl_FragColor = vec4(fragmentColor,1.0);
     return;
   }
   vec3 light = vec3(0.0, 0.0, 1.0);
  // t2 += ' vec3 lightDirection = vec3(-10.0, 4.0, -20.0);
  // I liked the following better
   vec3 lightDirection = vec3(0,0,-10);
   lightDirection = normalize(lightDirection);
   vec3 eyeDirection = normalize(-fVertexPosition.xyz);
   vec3 reflectionDirection = reflect(-lightDirection, nNormal);
  // t2 += ' vec3 reflectionDirection = nNormal; <-- to disable reflection
  // configure specular (10.0 is material property), diffuse and ambient
   float specular = pow(max(dot(reflectionDirection, eyeDirection), 0.0), 10.0);
   float diffuse = 0.8 * max(dot(nNormal, light), 0.0);
   float ambient = 0.3;
  // .. and now setup the fragment color using these three values and the
  // opacity
   gl_FragColor = vec4(fragmentColor * ambient +
                       fragmentColor * diffuse +
                       vec3(0.2, 0.2, 0.2) * specular,
                       objectOpacity);
 }
}

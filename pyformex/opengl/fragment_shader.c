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
    gl_FragColor = vec4(fragmentColor * ambient +
			fragmentColor * diffuse +
			vec3(0.2,0.2,0.2) * specular,
			opacity);
  } else {
    gl_FragColor = vec4(fragmentColor, opacity);
  }
}

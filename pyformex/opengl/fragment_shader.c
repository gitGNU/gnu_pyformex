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
   gl_FragColor = vec4(fragmentColor, 1.0);
}

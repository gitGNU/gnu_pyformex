#ifdef GL_ES
precision mediump float;
#endif

varying vec3 fragmentColor;
varying vec4 fragColor;

uniform float alpha;

void main(void) {

  gl_FragColor = fragColor;
}

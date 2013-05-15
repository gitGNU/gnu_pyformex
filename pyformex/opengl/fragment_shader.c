#ifdef GL_ES
precision mediump float;
#endif

varying vec4 fragColor;

void main(void) {
  gl_FragColor = fragColor;
}

#ifdef GL_ES
precision mediump float;
#endif

varying vec3 fragmentColor;
varying vec4 fragColor;

uniform float alpha;

void main(void) {

  // Add in opacity
  fragColor = vec4(fragmentColor,0.3);

  gl_FragColor = fragColor;
}

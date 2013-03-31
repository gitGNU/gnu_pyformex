#ifdef GL_ES
precision mediump float;
#endif

attribute vec3 vertexPosition;
attribute vec3 vertexNormal;
attribute vec3 vertexColor;
attribute vec2 vertexTexturePos;
attribute float vertexScalar;

uniform mat4 view;
uniform mat4 perspective;
uniform vec3 center;
uniform mat4 objectTransform;
uniform bool useObjectColor;
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
uniform float pointSize;

varying float fDiscardNow;
varying vec4 fVertexPosition;
varying vec3 fragmentColor;
varying vec2 fragmentTexturePos;
varying vec3 fVertexNormal;
varying vec3 fTransformedVertexNormal;

void main(void) {
  // setup varying -> fragment shader
  // use the old mat3 constructor to be compatible with mac/safari
  fTransformedVertexNormal = mat3(view[0].xyz,view[1].xyz,view[2].xyz) * mat3(objectTransform[0].xyz,objectTransform[1].xyz,objectTransform[2].xyz) * vertexNormal;
  fVertexNormal = vertexNormal;
  fDiscardNow = 0.0; // don't discard by default
  // t += ' vec4 gVertexPosition = vec4(fVertexPosition.xyz - focus, 1.0);
  vec3 vertexPosition2 = vertexPosition - center;
  fVertexPosition = view * objectTransform * vec4(vertexPosition2, 1.0);
  fragmentTexturePos = vertexTexturePos;
  if (useScalars) { // use scalar overlays
    float scalarValue = vertexScalar; // ..and threshold
    if (scalarValue < scalarsMinThreshold || scalarValue > scalarsMaxThreshold) {
      if (scalarsReplaceMode) {
        fragmentColor = objectColor; // outside threshold
      } else {
        fDiscardNow = 1.0;
  // if we don't replace the colors, just
  // discard this vertex (fiber length
  // thresholding f.e.)
      }
    } else {
      if (scalarsReplaceMode) {
        if (scalarsInterpolation == 1) {
  // the zeroMaxColor is the "zero" point for the interpolation of the "max"
  // colors
  // and used for the positive curvatures similarly the zeroMinColor for the
  // negative curvatures.
            vec3 zeroMaxColor;
            vec3 zeroMinColor;
            zeroMaxColor[0] = scalarsMaxColor[0]*0.33;
            zeroMaxColor[1] = scalarsMaxColor[1]*0.33;
            zeroMaxColor[2] = scalarsMaxColor[2]*0.33;
            zeroMinColor[0] = scalarsMinColor[0]*0.33;
            zeroMinColor[1] = scalarsMinColor[1]*0.33;
            zeroMinColor[2] = scalarsMinColor[2]*0.33;
            if(scalarValue < 0.0) {fragmentColor = scalarValue/(scalarsMin) * scalarsMinColor + (1.0 - scalarValue/(scalarsMin)) * (zeroMinColor)};
            else {fragmentColor = scalarValue/(scalarsMax) * scalarsMaxColor + (1.0 - scalarValue/(scalarsMax)) * (zeroMaxColor)};
        } else {
  // t += ' fragmentColor = (scalarValue-scalarsMin)/(scalarsMax-scalarsMin) *
  // scalarsMaxColor + (1.0 - (scalarValue-scalarsMin)/(scalarsMax-scalarsMin))
  // * scalarsMinColor;
            fragmentColor = scalarValue * scalarsMaxColor + (1.0 - scalarValue) * scalarsMinColor;
          }
      } else {
        fragmentColor = vertexColor; // if we don't replace and
  // didn't discard, just use
  // the point color here
      }
    }
  } else if (useObjectColor) {
    fragmentColor = objectColor;
  } else {
    fragmentColor = vertexColor;
  }
  // setup vertex Point Size and Position in the GL context
  gl_PointSize = pointSize;
  gl_Position = perspective * fVertexPosition;
}

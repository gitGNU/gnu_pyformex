/* $Id$ */
//
//  This file is part of pyFormex
//  pyFormex is a tool for generating, manipulating and transforming 3D
//  geometrical models by sequences of mathematical operations.
//  Home page: http://pyformex.org
//  Project page:  http://savannah.nongnu.org/projects/pyformex/
//  Copyright 2004-2012 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
//  Distributed under the GNU General Public License version 3 or later.
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program.  If not, see http://www.gnu.org/licenses/.
//

/* Vertex shader

If you add a uniform value to the shader, you should also add it
in shader.py, in order to allow setting the uniform value.
 */

#define MAX_LIGHTS 4

#ifdef GL_ES                   // This is True in WebGL shader
precision mediump float;
#endif

attribute vec3 vertexPosition;
attribute vec3 vertexNormal;
attribute vec3 vertexColor;
attribute vec2 vertexTexturePos;
attribute float vertexScalar;

uniform bool pyformex;              // Is the shader being used in pyFormex
uniform mat4 modelview;
uniform mat4 projection;
uniform mat4 pickmat;
uniform bool useObjectColor;
uniform bool highlight;

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

uniform bool builtin;
uniform bool picking;

uniform bool lighting;     // Are the lights on?
uniform int nlights;       // Number of lights?  <= MAX_LIGHTS
uniform vec3 ambicolor;                // Total ambient color
uniform vec3 diffcolor[MAX_LIGHTS];    // Colors of diffuse light
uniform vec3 speccolor[MAX_LIGHTS];    // Colors of reflected light
uniform vec3 lightdir[MAX_LIGHTS];     // Light directions

uniform float ambient;     // Material ambient value
uniform float diffuse;     // Material diffuse value
uniform float specular;    // Material Intensity of reflection
uniform float shininess;   // Material surface shininess
uniform float alpha;       // Material opacity


varying float fDiscardNow;
varying vec4 fvertexPosition;
varying vec3 fvertexNormal;
varying vec4 fragColor;        // Final fragment color, including opacity
varying vec3 fragmentColor;
varying vec2 fragmentTexturePos;
varying vec3 fTransformedVertexNormal;


void main()
{
  // Set color
  if (picking) {
    fragmentColor = vec3(0.,0.,0.);

  } else {

    if (highlight) {
      // Highlight color, currently hardwired yellow
      fragmentColor = vec3(1.,1.,0.);
    } else if (useObjectColor) {
      // Single color
      fragmentColor = objectColor;
    } else {
      // Vertex color
      if (builtin) {
	fragmentColor = gl_Color;
      } else {
	fragmentColor = vertexColor;
      }
    }

    // Add in lighting
    if (highlight) {
    } else {
      if (lighting) {
	if (builtin) {
	  fvertexNormal = gl_Normal;
	} else {
	  fvertexNormal = vertexNormal;
	}
	fTransformedVertexNormal = mat3(modelview[0].xyz,modelview[1].xyz,modelview[2].xyz) * fvertexNormal;
	vec3 nNormal = normalize(fTransformedVertexNormal);
	vec3 fcolor = fragmentColor;

	// ambient
	fragmentColor = fcolor * ambicolor * ambient;

	// add diffuse and specular for each light
	//fragmentColor = vec3(0.3,0.,0.);
	for (int i=0; i<nlights; ++i) {
	  vec3 nlight = normalize(lightdir[i]);
	  //vec3 eyeDirection = normalize(-vertexPosition);
	  vec3 eyeDirection = normalize(vec3(0.,0.,1.));
	  vec3 reflectionDirection = reflect(-nlight, nNormal);
	  float nspecular = specular*pow(max(dot(reflectionDirection,eyeDirection), 0.0), shininess);
	  float ndiffuse = diffuse * max(dot(nNormal,nlight),0.0);
	  vec3 diffcol = vec3(1.,1.,0.);
	  //fragmentColor += fcolor * (diffcolor[i] * ndiffuse + speccolor[i] * nspecular);
	  //fragmentColor += (fcolor + diffcolor[i]) * ndiffuse / 2;
	  //fragmentColor += (fcolor + speccolor[i]) * nspecular / 2;
	  fragmentColor += (fcolor + diffcolor[i])/2 * ndiffuse;
	  fragmentColor += (fcolor + speccolor[i])/2 * nspecular;
	}
      }
    }
    // Add in opacity
    fragColor = vec4(fragmentColor,alpha);

    // setup vertex Point Size
    gl_PointSize = pointsize;

  }

  // Transforming the vertex coordinates
  if (builtin) {
    fvertexPosition = gl_Vertex;
  } else {
    fvertexPosition = vec4(vertexPosition,1.0);
  }

  if (picking) {
    gl_Position = pickmat * projection * modelview * fvertexPosition;
  } else {
    gl_Position = projection * modelview * fvertexPosition;
  }
}

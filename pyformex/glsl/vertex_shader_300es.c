// $Id$
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

// Vertex shader

#version 300 es

#ifdef GL_ES                   // This is True in WebGL shader
precision mediump float;
#endif

// If you add a uniform value to the shader, you should also add it
// in shader.py, in order to allow setting the uniform value.

#define MAX_LIGHTS 4

in vec3 vertexCoords;
in vec3 vertexNormal;
in vec3 vertexColor;
in vec3 vertexOffset;       // offset for rendertype -1
in vec2 vertexTexturePos;
in float vertexScalar;

uniform bool pyformex;              // Is the shader being used in pyFormex
uniform mat4 modelview;
uniform mat4 projection;
uniform mat4 modelviewprojection;
uniform mat3 normalstransform;
uniform mat4 pickmat;
uniform float pointsize;
uniform bool highlight;
uniform bool picking;
uniform bool alphablend;   // Switch transparency on/off
uniform int rendertype;
uniform vec3 offset3;       // offset for rendertype 1

uniform int drawface;        // Which side of the face to draw (0,1,2)
uniform int useObjectColor;  // 0 = no, 1 = single color, 2 = twosided color
uniform vec3 objectColor;    // front and back color (1) or front color (2)
uniform vec3 objectBkColor;  // back color (2)
uniform int useTexture;    // 0: no texture, 1: single texture

uniform float ambient;     // Material ambient value
uniform float diffuse;     // Material diffuse value
uniform float specular;    // Material Intensity of reflection
uniform float shininess;   // Material surface shininess
uniform float alpha;       // Material opacity
uniform float bkalpha;     // Material backside opacity

uniform bool lighting;          // Are the lights on?
uniform int nlights;            // Number of lights?  <= MAX_LIGHTS
uniform vec3 ambicolor;                // Total ambient color
uniform vec3 diffcolor[MAX_LIGHTS];    // Colors of diffuse light
uniform vec3 speccolor[MAX_LIGHTS];    // Colors of reflected light
uniform vec3 lightdir[MAX_LIGHTS];     // Light directions

out vec4 fragColor;     // Final fragment color, including opacity
out vec3 nNormal;       // normalized transformed normal
out vec2 texCoord;      // Pass texture coordinate

void main()
{
  vec3 fragmentColor;
  // Set color
  if (picking) {
    fragmentColor = vec3(0.,0.,0.);

  } else {

    if (highlight) {
      // Highlight color, currently hardwired yellow
      fragmentColor = vec3(1.,1.,0.);
    } else if (useObjectColor == 2 && drawface == -1) {
      // Object color, front and back have different color, backside
      fragmentColor = objectBkColor;
    } else if (useObjectColor > 0) {
      // Object color, front side or both sides same color
      fragmentColor = objectColor;
    } else {
      // Vertex color
      fragmentColor = vertexColor;
    }

    // Add in lighting
    if (highlight) {
      fragColor = vec4(fragmentColor,1.);
    } else {

      if (lighting) {

	vec3 fTransformedVertexNormal = normalstransform * vertexNormal;

	nNormal = normalize(fTransformedVertexNormal);

        /* if (drawface == -1 && nNormal[2] < 0.0) { */
	/*   nNormal = -nNormal; */
	/* } */

        if (drawface == -1) {
	  nNormal = -nNormal;
	}

	vec3 fcolor = fragmentColor;

	// ambient
	fragmentColor = fcolor * ambicolor * ambient;

	// add diffuse and specular for each light
	for (int i=0; i<MAX_LIGHTS; ++i) {
	  if (i < nlights) {
	    vec3 nlight = normalize(lightdir[i]);
	    vec3 eyeDirection = normalize(vec3(0.,0.,1.));
	    vec3 reflectionDirection = reflect(-nlight, nNormal);
	    float nspecular = specular*pow(max(dot(reflectionDirection,eyeDirection), 0.0), shininess);
	    float ndiffuse = diffuse * max(dot(nNormal,nlight),0.0);
	    fragmentColor += (fcolor + diffcolor[i])/2. * ndiffuse;
	    fragmentColor += (fcolor + speccolor[i])/2. * nspecular;
	  }
	}
      } //lighting

      // Add in opacity
      if (alphablend) {
	if (drawface == -1) {
	  fragColor = vec4(fragmentColor,bkalpha);
	} else {
	  fragColor = vec4(fragmentColor,alpha);
	}
      }	else {
      	fragColor = vec4(fragmentColor,1.);
      }
    }

    // setup vertex Point Size
    gl_PointSize = pointsize;

  }

  // Transforming the vertex coordinates
  vec4 position = vec4(vertexCoords,1.0);

  if (picking) {
    gl_Position = pickmat * projection * modelview * position;
  } else {
    gl_Position = projection * modelview * position;
  }
  if (rendertype == 1) {
    gl_Position.x += offset3.x;
    gl_Position.y += offset3.y;
  } else if (rendertype == -1) {
    gl_Position.x += vertexOffset.x;
    gl_Position.y += vertexOffset.y;
  }

  if (useTexture > 0) {
    texCoord = vertexTexturePos;
  }
}

// End

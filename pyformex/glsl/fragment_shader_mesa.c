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

// Fragment shader

#version 120

#ifdef GL_ES
precision mediump float;
#endif

varying vec4 fragColor;
varying vec3 nNormal;        // normalized transformed normal
varying vec2 texCoord;

uniform int useTexture;    // 0: no texture, 1: single texture
uniform int texmode;       // 0: GL_REPLACE, 1: GL_MODULATE, 2: GL_DECAL
uniform float alpha;       // Material opacity
uniform vec3 objectColor;  // front and back color (1) or front color (2)

uniform sampler2D tex;

void main(void) {

  //if (nNormal[2] < 0.0)
  //  discard;

  if (useTexture > 0) {
    vec4 texColor = texture2D(tex,texCoord);
    if (texmode == 0) {
      // GL_REPLACE
      gl_FragColor = texColor;
    } else if (texmode == 1) {
      // GL_MODULATE
      gl_FragColor = fragColor * texColor;
    } else if (texmode == 2) {
      // GL_DECAL
      gl_FragColor = vec4( fragColor.rgb * (1.0-texColor.a) + texColor.rgb * texColor.a, fragColor.a);
    } else if (texmode == 3) {
      // Our own mixture using the object alpha
      gl_FragColor = vec4( fragColor.rgb * alpha + texColor.rgb * (1.-alpha), fragColor.a);
    } else if (texmode == 4) {
      // Color text
      //gl_FragColor = vec4(fragColor.xyz,texColor.a);
      gl_FragColor = vec4(objectColor.xyz,texColor.a);
    }
  } else {
    gl_FragColor = fragColor;
  }
}

// End

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

// Geometry shader

#version 130

#ifdef GL_ES
precision mediump float;
#endif

layout(lines) in;
layout(line_strip, max_vertices=2) out;

uniform vec2 screenSize;
uniform float patternSize;

noperspective out float texCoord;

void main()
{
    vec2 winPos0 = screenSize.xy * gl_in[0].gl_Position.xy / gl_in[0].gl_Position.w;
    vec2 winPos1 = screenSize.xy * gl_in[1].gl_Position.xy / gl_in[1].gl_Position.w;
    gl_Position = gl_in[0].gl_Position;
    texCoord = 0.0;
    EmitVertex();
    gl_Position = gl_in[1].gl_Position;
    texCoord = 0.5 * length(winPos1-winPos0) / patternSize;
    EmitVertex();
}

// End

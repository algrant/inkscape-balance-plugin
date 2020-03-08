#!/usr/bin/env python 
'''
MIT License

Copyright (c) 2020 Al Grant, al@algrant.ca

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import math, inkex, simplestyle, simplepath, bezmisc
from cubicsuperpath import CubicSuperPath as csp
from lxml import etree

class AreaCoG(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self) 

    def linearArea(self, x0, y0, x1, y1):
        return 0.5*(x0*y1-y0*x1)

    def linearLamina(self, u0, v0, u1, v1):
        return (u0*u0 + u1*u0 + u1*u1)*(v1 - v0)/6.0
    
    def quadraticArea(self, x0, y0, x1, y1, x2, y2):
        return (- 2*x1*y0 -x2*y0 + 2*x0 *y1 - 2*x2*y1 + x0*y2 + 2*x1*y2) / 6.0

    def quadraticLamina(self, u0, v0, u1, v1, u2, v2):
        #Generated using Mathematica
        return (1/30.0)*(u0*u0*(-5*v0 + 4*v1 + v2) + u0*(u2*(v2 - v0) + 2*u1*(-2*v0 + v1 + v2)) 
                        -2*u1*u1*(v0 - v2) - 2*u1*u2*(v0 + v1 - 2*v2) 
                        -u2*u2*(v0 + 4*v1 - 5*v2))

    def cubicArea(self, x0, y0, x1, y1, x2, y2, x3, y3):
        return (          - 6*x1*y0 - 3*x2*y0 -   x3*y0  
                + 6*x0*y1           - 3*x2*y1 - 3*x3*y1  
                + 3*x0*y2 + 3*x1*y2           - 6*x3*y2
                +   x0*y3 + 3*x1*y3 + 6*x2*y3           )/20.0

    def cubicLamina(self, u0, v0, u1, v1, u2, v2, u3, v3):
        #Generated using Mathematica
        return (1/840.0)*(5*u0**2*(-(28*v0) + 21*v1 + 6*v2 + v3) + u0* (15*u1*(-(7*v0) + 
                3*(v1 + v2) + v3) + 6*u2*(-(5*v0) + 3*v2 + 2*v3) + u3*(-(5*v0) - 3*v1 + 
                3*v2 + 5*v3)) - 18*u2**2*v0 - 5*u3**2*v0 -  15*u2*u3*v0 - 27*u2**2*v1 -  
                30*u3**2*v1 - 45*u2*u3*v1 - 105*u3**2*v2 - 45*u2*u3*v2 +  5*(9*u2**2 + 
                21*u3*u2 + 28*u3**2)*v3 + 9*u1**2*(-(5*v0) + 3*v2 + 2*v3) - 
                3*u1*(2*u3*(2*v0 + 3*v1 - 5*v3) + 3*u2*(5*v0 + 3*v1 - 3*v2 - 5*v3)))

    def drawCrossHairs(self, layer, x, y, style = None, rad = 10):
        # create crosshair group
        group = etree.SubElement(layer, inkex.addNS('g','svg'))
        
        # add circle (actually diamond...)
        if style:
            circle = etree.SubElement(group,inkex.addNS('path','svg'))
            circle.set('style', style)
            circleLine = [ 
                ['M',[x-rad/2,y]],
                ['L',[x,y-rad/2]],
                ['L',[x+rad/2,y]],
                ['L',[x,y+rad/2]],
                ['Z',[]]
            ]
            circle.set('d', str(inkex.Path(circleLine)))

        # add crosshairs
        crosshairX = etree.SubElement(group,inkex.addNS('path','svg'))
        crosshairY = etree.SubElement(group,inkex.addNS('path','svg'))

        chxLine = [['M',[x,y-rad]],['L',[x,y+rad]]]
        chyLine = [['M',[x-rad,y]],['L',[x+rad,y]]]

        crosshairX.set('d', str(inkex.Path(chxLine))) 
        crosshairX.set('style', 'stroke:#CC0000;stroke-width:1.0px;')
        crosshairY.set('d', str(inkex.Path(chyLine))) 
        crosshairY.set('style', 'stroke:#CC0000;stroke-width:1.0px;')

    def genAreaAndLamina(self, path):
        p = path.to_arrays()
        area = 0
        lamina_x = 0
        lamina_y = 0
        startX, startY = p[0][1][0], p[0][1][1]

        for cmd,params in p:
            if cmd == 'L':
                x1,y1 = params[0],params[1]
                area += self.linearArea(x0, y0, x1, y1)
                lamina_x += self.linearLamina(x0, y0, x1, y1)
                lamina_y -= self.linearLamina(y0, x0, y1, x1)
                x0,y0 = x1,y1

            if cmd == 'C':
                x1,y1 = params[0],params[1]
                x2,y2 = params[2],params[3]
                x3,y3 = params[4],params[5]
                area += self.cubicArea(x0,y0,x1,y1,x2,y2,x3,y3)
                lamina_x += self.cubicLamina(x0, y0, x1, y1, x2, y2, x3, y3)
                lamina_y -= self.cubicLamina(y0, x0, y1, x1, y2, x2, y3, x3)
                x0,y0 = x3,y3
            
            if cmd == 'M':
                x0,y0 = params[0],params[1]
                xStart, yStart = x0,y0

            if cmd == 'Z':
                area += self.linearArea(x0, y0, xStart, yStart)
                lamina_x += self.linearLamina(x0, y0, xStart, yStart)
                lamina_y -= self.linearLamina(y0, x0, yStart, xStart)

        if (area < 0):
            # path is going counter-clockwise, numbers are inverted, 
            # will be an issue once we add objects together
            area = -area
            lamina_x = -lamina_x
            lamina_y = -lamina_y

        return [area, lamina_x, lamina_y]

    def effect(self):
        closed_paths = []
        for id, node in self.svg.selected.items():
            if node.tag == inkex.addNS('path','svg'):
                area, lamina_x, lamina_y = self.genAreaAndLamina(node.path)
                closed_paths.append([node, area, lamina_x, lamina_y])
                self.drawCrossHairs(node.getparent(), lamina_x/area, lamina_y/area, node.get('style'))

        tot_mass, tot_lamx, tot_lamy = 0,0,0

        if len(closed_paths) > 1:
            for node, mass, lamina_x, lamina_y in closed_paths:
                tot_mass += mass
                tot_lamx += lamina_x
                tot_lamy += lamina_y

            self.drawCrossHairs(closed_paths[0][0].getparent().getparent(), tot_lamx/tot_mass, tot_lamy/tot_mass)


if __name__ == '__main__':
    e = AreaCoG()
    e.run()


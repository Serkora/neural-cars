import math
import operator
import pyglet
from pyglet.gl import *

from geometry import Point, Line, Box, Quad, PI, TAU, DEG_TO_RAD, RAD_TO_DEG

class Entity(object):
	def __init__(self, x=0, y=0, size=1, rot=0):
		self.x = x
		self.y = y
		self.size = size
		self.rot = rot
		self.batch = pyglet.graphics.Batch()
	
	def draw(self):
		glLoadIdentity()
		glTranslatef(self.x, self.y, 0.0)
		glRotatef(-self.rot * RAD_TO_DEG, 0, 0, 1)
		glScalef(self.size, self.size, 1.0)
		self.batch.draw()

class DBox(Entity):
	def __init__(self, x, y, width, height):
		super().__init__()
		self.x = x
		self.y = y
		self.width = width
		self.height = height

		coords = (0,0, 0,self.height, self.width,self.height, self.width,0)

		self.batch.add(4, pyglet.gl.GL_LINE_LOOP, None,
			('v2f', coords),
			('c3B', (50, 0, 120) * 4))

	def is_point_inside(self):
		pass

class Polygon(Entity):
	def __init__(self, *points):
		self.points = [Point(point) for point in points]
		

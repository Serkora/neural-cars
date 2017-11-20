import math
import operator
import pyglet
from pyglet.gl import *

from collections import namedtuple
import graphtools

Box = namedtuple('Box', ('x', 'y', 'width', 'height'))

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
		glRotatef(-self.rot * 180 / math.pi, 0, 0, 1)
		glScalef(self.size, self.size, 1.0)
		self.batch.draw()

class Point(tuple):
	def __new__(cls, x, y):
		return super().__new__(cls, (x,y))

	def __init__(self, x, y):
		super().__init__()
		self.x = x
		self.y = y

	def __getitem__(self, idx):
		return (self.x, self.y)[idx]

	def shifted(self, delta_x, delta_y):
		return Point(self.x + delta_x, self.y + delta_y)

	def translated(self, angle, distance):
		return Point(self.x + distance*math.sin(angle), self.y + distance*math.cos(angle))

class Line(object):
	def __init__(self, start, end=None, angle=None, length=0):
		self._start = Point(*start)
		if angle is not None:
			self._end = Point(self.start.x + length*math.sin(angle), self.start.y + length*math.cos(angle))
			self._angle = angle
		else:
			self._end = Point(*end)

		self._angle = None
		self._centre = None
		self._quadrant = None
		self._length = None
		self._coords = None

		self.quadrant = self.get_quadrant()

	def __len__(self):
		return 4

	def __getitem__(self, idx):
		return self.coords[idx]

	@property
	def start(self):
		return self._start

	@property
	def end(self):
		return self._end

	@property
	def coords(self):
		#if not self._coords:
		#	self._coords = self.start + self.end # tuple of length 4 for both points
		#return self._coords
		return self.start + self.end # tuple of length 4 for both points

	@property
	def length(self):
		if not self._length:
			self._length = 	((self.end.x - self.start.x) ** 2 + (self.end.y - self.start.y) ** 2) ** 0.5
		return self._length

	@property
	def angle(self):
		if not self._angle is None:
			return self._angle
		if self.end.x - self.start.x == 0:
			self._angle = [0, math.pi][self.end.y < self.start.y]
		elif self._end.y - self.start.y == 0:
			self._angle = [math.pi/2, 3*math.pi/2][self.end.x < self.start.x]
		elif self.quadrant == 1:
			self._angle = math.atan((self.end.x - self.start.x) / (self.end.y - self.start.y))
		elif self.quadrant == 2:
			self._angle = 3 * math.pi / 2 +  math.atan((self.end.y - self.start.y) / abs(self.end.x - self.start.x))
		elif self.quadrant == 4:
			self._angle = math.pi / 2 + math.atan(abs(self.end.y - self.start.y) / (self.end.x - self.start.x))
		elif self.quadrant == 3:
			self._angle = math.pi + math.atan((self.end.x - self.start.x) / (self.end.y - self.start.y))
		return self._angle

	@property
	def centre(self):
		if not self._centre:
			self._centre = self.get_centre()
		return self._centre

	def get_centre(self):
		return Point(*(sum(e) / 2 for e in zip(self.start, self.end)))

	def get_quadrant(self):
		# Returns the quadrant number the line is in
		# if start point is moved to (0,0)
		return [3,2,4,1][2 * (self.end.x >= self.start.x) + int(self.end.y >= self.start.y)]

	def rotated(self, angle, anchor="start"):
		if anchor == "start":
			anchor, end = self.start, self.end
		else:
			anchor, end = self.end, self.start
		x = anchor.x + (end.x - anchor.x) * math.cos(angle) - (end.y - anchor.y) * math.sin(angle)
		y = anchor.y + (end.x - anchor.x) * math.sin(angle) + (end.y - anchor.y) * math.cos(angle)
		return Line(anchor, (x,y))

	def rotate(self, angle):
		if anchor == "start":
			anchor, end = self.start, self.end
		else:
			anchor, end = self.end, self.start
		x = anchor.x + (end.x - anchor.x) * math.cos(angle) - (end.y - anchor.y) * math.sin(angle)
		y = anchor.y + (end.x - anchor.x) * math.sin(angle) + (end.y - anchor.y) * math.cos(angle)
		anchor.x = x
		anchor.y = y

	def moved(self, x, y):
		return Line((self.start.x + x, self.start.y + y), (self.end.x + x, self.end.y + y))

	def move(self, delta_x, delta_y):
		self._start = self.start.shifted(delta_x, delta_y)
		self._end = self.end.shifted(delta_x, delta_y)
		#self._centre = self._centre.shifted(delta_x, delta_y)

	def point_on_line(self, point, tol=math.pi/180):
		l1 = Line(self.start, point)
		l2 = Line(self.end, point)
		if (math.pi - tol <= abs(l2.angle - l1.angle) <= math.pi + tol):
			return True
		return False

	def intersects(self, line):
		return graphtools.line_intersection(self.coords, line.coords)

	def intersection(self, line):
		return graphtools.line_intersection(self.coords, line.coords)

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

class Quad(object):
	def __init__(self, coords=None, box=None):
		if box:
			self.top_left = (box.x, box.y)
			self.top_right = (box.x + box.width, box.y)
			self.bottom_right = (box.x + box.width, box.y - box.height)
			self.bottom_left = (box.x, box.y - box.height)
		elif coords:
			self.bottom_left, self.bottom_right, self.top_left, self.top_right = coords
		else:
			raise ValueError("Either coords or box must be provided!")

		self.line = self.get_line()
		self.vertices = (self.top_left, self.top_right, self.bottom_right, self.bottom_left)

		self.left = Line(self.bottom_left, self.top_left)
		self.front = Line(self.top_left, self.top_right)
		self.right = Line(self.bottom_right, self.top_right)
		self.back = Line(self.bottom_right, self.bottom_left)
		self.leftt = self.left.coords
		self.frontt = self.front.coords
		self.rightt = self.right.coords
		self.backt = self.back.coords

		self.box_vertices = self.get_box_vertices()
		self.loop_vertices = sum(self.vertices, ())

	def __len__(self):
		return 4

	def __getitem__(self, idx):
		return self.vertices[idx % 4]

	def get_line(self):
		line_start = tuple(sum(e) / 2 for e in zip(self.bottom_left, self.bottom_right))
		line_end = tuple(sum(e) / 2 for e in zip(self.top_left, self.top_right))
		return Line(line_start, line_end)

	def get_box_vertices(self):
		return sum((getattr(self, line).coords for line in ['front', 'right', 'back', 'left']), tuple())

	def intersect_quad(self, origin, quad, quad_origin):
		return False

class Polygon(Entity):
	def __init__(self, *points):
		self.points = [Point(point) for point in points]
		

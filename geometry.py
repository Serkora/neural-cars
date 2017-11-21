import time
import math
import numpy as np
from collections import namedtuple
try:
	from cext import cmodule
except ImportError:
	cmodule = None

PI = math.pi
TAU = PI * 2
RAD_TO_DEG = 180 / PI
DEG_TO_RAD = PI / 180

Box = namedtuple('Box', ('x', 'y', 'width', 'height'))
Point = namedtuple("Point", ("x", "y"))

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
			self._angle = [0, PI][self.end.y < self.start.y]
		elif self._end.y - self.start.y == 0:
			self._angle = [PI/2, 3*PI/2][self.end.x < self.start.x]
		elif self.quadrant == 1:
			self._angle = math.atan((self.end.x - self.start.x) / (self.end.y - self.start.y))
		elif self.quadrant == 2:
			self._angle = 3 * PI / 2 +  math.atan((self.end.y - self.start.y) / abs(self.end.x - self.start.x))
		elif self.quadrant == 4:
			self._angle = PI / 2 + math.atan(abs(self.end.y - self.start.y) / (self.end.x - self.start.x))
		elif self.quadrant == 3:
			self._angle = PI + math.atan((self.end.x - self.start.x) / (self.end.y - self.start.y))
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

	def point_on_line(self, point, tol=PI/180):
		l1 = Line(self.start, point)
		l2 = Line(self.end, point)
		if (PI - tol <= abs(l2.angle - l1.angle) <= PI + tol):
			return True
		return False

	def intersects(self, line):
		return segment_intersection(self.coords, line)

	def intersection(self, line):
		return segment_intersection(self.coords, line)

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

def segment_intersection(segment1, segment2, point=True):
	if cmodule:	return cmodule.intersection(segment1, segment2)

	x1, y1, x2, y2 = segment1
	x3, y3, x4, y4 = segment2
	dx1 = x1 - x2
	dx2 = x3 - x4
	dy1 = y1 - y2
	dy2 = y3 - y4

	# common denomiator in determinant calculation
	denom = dx1*dy2 - dy1*dx2
	if denom == 0:
		return

	# check that segments intersect rather than infinite lines
	# i.e. ends of one line are located on different sides of
	# the other line.
	# check if line1 intersects infinite line2
	a = (x3*y4 - y3*x4)
	d1a = dy2 * x1 - dx2*y1 + a
	d1b = dy2 * x2 - dx2*y2 + a
	if d1a * d1b > 0:
		return

	# check if line2 intersects infinite line1
	b = (x1*y2 - y1*x2)
	d2a = dy1 * x3 - dx1*y3 + b
	d2b = dy1 * x4 - dx1*y4 + b
	if d2a * d2b > 0:
		return

	if point:
		# calculate the determinant to find the intersection point
		x = (b * dx2 - dx1 * a) / denom
		y = (b * dy2 - dy1 * a) / denom
		return (x,y)
	else:
		return True


def segment_line_intersection(segment, line):
	if cmodule:	return cmodule.intersection(line1, line2)

	x1, y1, x2, y2 = segment
	x3, y3, x4, y4 = line
	dx1 = x1 - x2
	dx2 = x3 - x4
	dy1 = y1 - y2
	dy2 = y3 - y4

	# common denomiator in determinant calculation
	denom = dx1*dy2 - dy1*dx2
	if denom == 0:
		return

	# check that segments intersect rather than infinite lines
	# i.e. ends of one line are located on different sides of
	# the other line.
	# check if line1 intersects infinite line2
	a = (x3*y4 - y3*x4)
	d1a = dy2 * x1 - dx2*y1 + a
	d1b = dy2 * x2 - dx2*y2 + a
	if d1a * d1b > 0:
		return

	return True

line_intersection = segment_intersection

def same_direction(angle1, angle2):
	mx = max(angle1, angle2)
	mn = min(angle1, angle2)
	return mx - mn < PI / 2 or (TAU - mx) + mn < PI / 2

def left_of(angle1, angle2):
	#print("angle1 = %.1f, angle2 = %.1f, pi = %.2f" % (angle1, angle2, PI))
	return -PI < (angle1 - angle2) < 0 or PI < (angle1 - angle2) < TAU

def right_of(angle1, angle2):
	return not left_of(angle1, angle2)

def translate(point, angle, distance):
	return Point(point.x + distance*math.sin(angle), point.y + distance*math.cos(angle))

def shift(point, delta):
	return Point(point.x + delta[0], point.y + delta[1])

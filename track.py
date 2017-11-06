import math
import pyglet
from drawables import *

tau = 2 * math.pi

class TrackSection(Entity):
	def __init__(self, quad=None, line=None, width=50, section=None, point=None):
		super().__init__()

		if quad:
			self.quad = quad
			self.line = quad.get_line()
		elif line:
			self.line = line
			if (line.end.x - line.start.x) == 0:
				angle = 0 if line.end.y < line.start.y else -1
			else:
				angle = math.atan((line.end.y - line.start.y) / (line.end.x - line.start.x))

			self.quad = Quad(coords=(
				self.move_point(line.start.x, line.start.y, angle, width/2, 'left'),
				self.move_point(line.start.x, line.start.y, angle, width/2, 'right'),
				self.move_point(line.end.x, line.end.y, angle, width/2, 'left'),
				self.move_point(line.end.x, line.end.y, angle, width/2, 'right'),
			))
		elif section and point and width:
			self.line = Line(section.quad.get_line().end, point)
			if (self.line.end.x - self.line.start.x) == 0:
				angle = 0 if self.line.end.y < self.line.start.y else -1
			else:
				angle = math.atan((self.line.end.y - self.line.start.y) / (self.line.end.x - self.line.start.x))
			if self.line.end.x < self.line.start.x:
				angle = -angle
			self.quad = Quad(coords=(section.quad.top_left, section.quad.top_right,
				self.move_point(self.line.end.x, self.line.end.y, angle, width/2, 'left'),
				self.move_point(self.line.end.x, self.line.end.y, angle, width/2, 'right'),
			))
		else:
			raise ValueError("Either quad or line with width must be provided to built a Track Section")

		self.colour = (100,100,100)
		self.length = self.line.length
		self.rotated_corners()
		self.make_box()

	def move_point(self, x, y, angle, distance, direction):
		if direction == "left":
			left_angle = math.pi / 2 - angle
			new_x = x - math.cos(left_angle) * distance
			new_y = y + math.tan(left_angle) * (x - new_x)
		elif direction == "right":
			right_angle = angle - math.pi / 2
			new_x = x + math.cos(right_angle) * distance
			new_y = y - math.tan(right_angle) * (x - new_x)
		return Point(new_x, new_y)

	def rotated_corners(self):
		pass

	def make_box(self):
		left = self.quad.left.rotated(self.quad.line.angle)
		top = self.quad.front.rotated(self.quad.line.angle)
		self.dbox = DBox(*left.start, top.length, left.length)

	def getcarline(self, car):
		left = self.quad.left.rotated(self.quad.line.angle)
		top = self.quad.front.rotated(self.quad.line.angle)
		line = Line(left.start, (car.x, car.y)).rotated(self.quad.line.angle)
		return line

	def add_to_batch(self, batch, colours=None, sides=True):
		batch.add(2, pyglet.gl.GL_LINES, None,
			('v2f', self.line.coords),
			('c3B', (0,100,100,100,255,255))
		)

		if colours:
			colours = (colours * 4)[:12]
		else:
			colours = self.colour * 4

		if sides:
			batch.add(4, pyglet.gl.GL_LINES, None,
				('v2f', self.quad.left.coords + self.quad.right.coords),
				('c3B', colours))
		else:
			batch.add(4, pyglet.gl.GL_LINE_LOOP, None,
				('v2f', sum(self.quad.vertices, tuple())),
				('c3B', colours))

	def car_has_left(self, car):
		carfrontline = Line(self.quad.top_left, (car.x, car.y))
		carbackline = Line(self.quad.bottom_right, (car.x, car.y))

		if (self.quad.front.angle - carfrontline.angle) % (2 * math.pi) <= math.pi / 2:
			return 1
		elif (self.quad.back.angle - carbackline.angle) % (2 * math.pi) <= math.pi / 2:
			return -1
		return 0

	def car_hit_border(self, left=None, right=None, car=None):
		if not (left and right) and car:
			left = Line(car.top_left, car.bottom_left)
			right = Line(car.top_right, car.bottom_right)
		for border in [self.quad.left, self.quad.right]:
			if border.intersects(left):
				return "left"
			elif border.intersects(right):
				return "right"
		return False

class Track(Entity):
	def __init__(self):
		super().__init__()
		self.sections = []
		self.width = 75

		self.add_section(line=Line((-50, -50), (50, 50)))
		self.add_section(section=self.sections[-1], point=(75, 75))
		self.add_section(section=self.sections[-1], point=(100, 175))
		self.add_section(section=self.sections[-1], point=(200, 205))
		self.add_section(section=self.sections[-1], point=(270, 135), width=50)
		self.add_section(section=self.sections[-1], point=(300, 85), width=50)
		self.add_section(section=self.sections[-1], point=(250, -50), width=50)
		self.add_section(section=self.sections[-1], point=(220, -150), width=70)

	def draw_labels(self):
		pass

	def add_section(self, *args, width=None,**kwargs):
		section = TrackSection(*args, **kwargs, width=width or self.width)
		section.add_to_batch(self.batch)
		self.sections.append(section)
		return section

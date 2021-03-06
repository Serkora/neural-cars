import math
import pyglet
from pyglet.graphics.vertexbuffer import VertexBufferObject
import geometry
from geometry import Point, Line, Box, Quad
from drawables import *
from cext import cmodule

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
		self.colour = (200/255,200/255,200/255)
		self.length = self.line.length
		self.rotated_corners()
		self.make_box()

	def move_point(self, x, y, angle, distance, direction):
		if direction == "left":
			left_angle = PI / 2 - angle
			new_x = x - math.cos(left_angle) * distance
			new_y = y + math.tan(left_angle) * (x - new_x)
		elif direction == "right":
			right_angle = angle - PI / 2
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
		if colours:
			colours = (colours * 4)[:12]
		else:
			colours = self.colour * 4

		if sides:
			batch.add(2, pyglet.gl.GL_LINES, None,
				('v2f', self.line.coords),
				('c3f', (0,100/255,100/255,100/255,1,1))
			)

			batch.add(4, pyglet.gl.GL_LINES, None,
				('v2f', self.quad.left.coords + self.quad.right.coords),
				('c3f', colours))
		else:
			batch.add(4, pyglet.gl.GL_LINE_LOOP, None,
				('v2f', self.quad.loop_vertices),
				('c3f', colours))

	def get_vertices(self):
		return self.quad.left.coords + self.quad.right.coords

	def get_colours(self, colours=None, side=True):
		if colours:
			colours = (colours * 4)[:12]
		else:
			colours = self.colour * 4
		return colours

	def changed_section(self, pos):
		left = self.quad.leftt
		next_line = (pos[0], pos[1], left[2] + left[2] - left[0], left[3] + left[3] - left[1])
		prev_line = (pos[0], pos[1], left[0] - left[2] + left[0], left[1] - left[3] + left[1])
		if not geometry.segment_line_intersection(next_line, self.quad.frontt):
			return 1
		elif not geometry.segment_line_intersection(prev_line, self.quad.backt):
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
		self.circular = False

		self.make_track_new()
		self.length = len(self.sections)
		if cmodule:
			self.caddr = self.set_ctrack()

		self.init_vbo()

	def __del__(self):
		if cmodule:
			cmodule.delete_track(self.caddr)

	def set_ctrack(self):
		def section_to_array(section):
			out = []
			out.append(section.quad.front.coords)
			out.append(section.quad.back.coords)
			out.append(section.quad.left.coords)
			out.append(section.quad.right.coords)
			out.append(section.quad.line.coords)
			out.append(section.quad.line.angle)
			return out
		sections = [section_to_array(sec) for sec in self.sections]
		return cmodule.store_track(sections)

	def init_vbo(self):
		self.vert_vbo = VertexBufferObject(self.length * 32, GL_ARRAY_BUFFER, GL_DYNAMIC_DRAW)
		self.col_vbo = VertexBufferObject(self.length * 48, GL_ARRAY_BUFFER, GL_DYNAMIC_DRAW)
		self.coords = Vec(*sum((s.get_vertices() for s in self.sections), ()))
		self.colours = Vec(*sum((s.get_colours() for s in self.sections), ()))
		self.vert_vbo.set_data(self.coords)
		self.col_vbo.set_data(self.colours)

	def draw(self):
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()

		glLoadIdentity()
		self.col_vbo.bind()
		glColorPointer(3, GL_FLOAT, 0, self.col_vbo.ptr)
		self.vert_vbo.bind()
		glVertexPointer(2, GL_FLOAT, 0, self.vert_vbo.ptr)
		glEnableClientState(GL_VERTEX_ARRAY)
		glEnableClientState(GL_COLOR_ARRAY)
		glTranslatef(self.x, self.y, 0.0)
		glRotatef(-self.rot * RAD_TO_DEG, 0, 0, 1)
		glScalef(self.size, self.size, 1.0)
		glDrawArrays(GL_LINES, 0, self.length * 8)
		glDisableClientState(GL_COLOR_ARRAY)
		glDisableClientState(GL_VERTEX_ARRAY)
		self.col_vbo.unbind()
		self.vert_vbo.unbind()

		glPopMatrix()

	def make_track(self):
		self.add_section(line=Line((-50, -50), (50, 50)))
		self.add_section(section=self.sections[-1], point=(75, 75))
		self.add_section(section=self.sections[-1], point=(100, 175))
		self.add_section(section=self.sections[-1], point=(90, 220))
		self.add_section(section=self.sections[-1], point=(80, 260))
		self.add_section(section=self.sections[-1], point=(50, 320))
		self.add_section(section=self.sections[-1], point=(65, 370))
		self.add_section(section=self.sections[-1], point=(80, 390))
		self.add_section(section=self.sections[-1], point=(105, 420))

	def make_track_new(self):
		#points = [(0, 100), (20, 150), (50, 250), (100, 280), (150, 300)]
		points = [(0, 100), (20, 150), (50, 250), (100, 260), (160, 230),
				(180,180), (180, 120), (200, 50), (200, 20), 
				(100, -120), (20, -90), (0, -40)]
		prev_quad = Quad(box=Box(0, 50, self.width, 50))
		#prev_quad = Quad(coords=((0,0),(0,self.width),(0,50),(self.width,50)))
		for point in points:
			prev_quad, new_quad = self.make_section_quad(point, prev_quad)
			self.add_section(quad=prev_quad)
			prev_quad = new_quad
		self.add_section(quad=prev_quad)
		quad = Quad(coords=(prev_quad.top_left, prev_quad.top_right, self.sections[0].quad.bottom_left, self.sections[0].quad.bottom_right))
		self.add_section(quad)
		self.circular = True

	def make_section_quad(self, point, previous, width=None):
		width = width or self.width
		point = Point(*point)
		left = Line(previous.top_left, point)
		top_right = geometry.translate(left.end, left.angle+PI/2, width)
		bottom_right = geometry.translate(left.start, left.angle+PI/2, width)
		right = Line(bottom_right, top_right)
		intersection = previous.right.intersection(right)
		if intersection:
			bottom_right = intersection
			p = previous
			previous = Quad(coords=(p.bottom_left, p.bottom_right, p.top_left, bottom_right))
		else:
			bottom_right = previous.top_right
		new_quad = Quad(coords=(left.start, bottom_right, left.end, top_right))
		return previous, new_quad

	def make_track_tests(self):
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

	def check_car_collision(self, car):
		if cmodule:
			return cmodule.check_car_collision(car.x, car.y, car.rot, car.section_idx)
		box = car.lines[1:4:2] # left and right sides only
		#box = car.lines
		for line in box:
			if self.find_intersection(line, car.section_idx):
				return True

	def find_intersection(self, line, idx):
		prev_border = None
		while True:
			if idx < 0:
				idx += self.length
			elif idx >= self.length:
				idx -= self.length

			quad = self.sections[idx].quad
			point = geometry.segment_intersection(line, quad.leftt)
			if point:
				return point
			point = geometry.segment_intersection(line, quad.rightt)
			if point:
				return point

			if prev_border != "back" and geometry.segment_intersection(line, quad.frontt, False):
				prev_border = "front"
				idx += 1
			elif prev_border != "front" and geometry.segment_intersection(line, quad.backt, False):
				prev_border = "back"
				idx -= 1
			else:
				break



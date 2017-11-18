import math
import time
from collections import defaultdict
import pyglet

import graphtools
import neural
from drawables import *
from cext import ctrack

car_batch = None

class Camera(object):
	def __init__(self, car, direction, max_dist, origin=(0,0)):
		self.car = car
		self.max_dist = max_dist
		self.direction = direction
		self.origin = Point(*origin)
		self.line = Line(self.origin, angle=self.angle, length=self.max_dist)
		self.focus = self.line.end
		self.distance = self.max_dist

	@property
	def angle(self):
		return self.car.rot + self.direction
	
	def	update(self):
		#self.line = Line(self.origin, angle=self.angle, length=self.max_dist).moved(*self.car.position)
		#self.line = Line(self.origin, angle=self.angle, length=self.max_dist)
		#self.line.move(*self.car.position)
		t1 = time.time()
		#self.line = Line(self.car.position, angle=self.angle, length=self.max_dist)
		t2 = time.time()
		#self.get_focus()
		self.get_focus_new()
		t3 = time.time()
		self.car.set_and_get_avg_time("crline", (t2-t1))
		self.car.set_and_get_avg_time("focus", (t3-t2))

	def get_focus_new(self):
		t1 = time.time()
		point = ctrack.test2(self.line.coords, self.car.section_idx)
		t2 = time.time()
		if point:
			#self.focus = Point(*point)
			self.focus = point
			self.distance = ((self.focus[0] - self.car.x) ** 2 + (self.focus[1] - self.car.y) ** 2) ** 0.5
		else:
			self.focus = self.line.end
			self.distance = self.max_dist
		t3 = time.time()
		self.car.set_and_get_avg_time("focint", (t2-t1))
		self.car.set_and_get_avg_time("focdist", (t3-t2))

	def get_focus(self):
		last_border = None
		i = self.car.section_idx
		while True:
			t1 = time.time()
			if i < 0 or i >= len(self.car.track.sections):
				i %= len(self.car.track.sections)
			section = self.car.track.sections[i]
			t2 = time.time()
			if graphtools.left_of(self.line.angle, section.quad.line.angle):
				self.focus = self.line.intersection(section.quad.left)
			else:
				self.focus = self.line.intersection(section.quad.right)
			t3 = time.time()

			if self.focus:
				#self.distance = Line(self.origin.shifted(*self.car.position), self.focus).length
				#self.distance = Line(self.origin.shifted(*self.car.position), self.focus).length
				#self.focus = Point(*self.focus)
				#self.distance = ((self.focus.x - self.car.position.x) ** 2 + (self.focus.y - self.car.position.y) ** 2) ** 0.5
				self.distance = ((self.focus[0] - self.car.x) ** 2 + (self.focus[1] - self.car.y) ** 2) ** 0.5
				t4 = time.time()
				self.car.set_and_get_avg_time('secsel', (t2 - t1))
				self.car.set_and_get_avg_time('focint', (t3 - t2))
				self.car.set_and_get_avg_time('focdist', (t4 - t3))
				return

			if last_border != "back" and self.line.intersects(section.quad.front):
				last_border = "front"
				i += 1
			elif last_border != "front" and self.line.intersects(section.quad.back):
				last_border = "back"
				i -= 1
			else:
				t5 = time.time()
				self.car.set_and_get_avg_time('secsel', (t2 - t1))
				self.car.set_and_get_avg_time('focint', (t3 - t2))
				self.car.set_and_get_avg_time('bordint', (t5 - t3))
				break
			t5 = time.time()
			self.car.set_and_get_avg_time('secsel', (t2 - t1))
			self.car.set_and_get_avg_time('focint', (t3 - t2))
			self.car.set_and_get_avg_time('bordint', (t5 - t3))
			t5 = time.time()
		self.focus = self.line.end
		self.distance = self.max_dist

class Car(Entity):
	def __init__(self, human=False):
		super().__init__()

		self.max_speed = 150
		self.rot = 0
		self.prev_rot = 0
		self.speed = 0
		self.max_steering = 180
		self.steering = 0

		self.width = 10
		self.height = 30

		self.quad = Quad(box=Box(-self.width/2, self.height/2, self.width, self.height))
		self.points_batch = pyglet.graphics.Batch()

		self.top_left = Line((0,0), self.quad.top_left).rotated(-self.rot).moved(self.x, self.y).end
		self.top_right = Line((0,0), self.quad.top_right).rotated(-self.rot).moved(self.x, self.y).end
		self.bottom_left = Line((0,0), self.quad.bottom_left).rotated(-self.rot).moved(self.x, self.y).end
		self.bottom_right = Line((0,0), self.quad.bottom_right).rotated(-self.rot).moved(self.x, self.y).end
		self.corner_distance = Line(self.position, self.quad.top_left).length
		self.corner_angle = Line(self.position, self.quad.top_right).angle

		self.track = None
		self.collided = False
		self.section = None
		self.section_idx = -1
		self.section_batch = pyglet.graphics.Batch()

		self.info_label = pyglet.text.Label(text="", x=0, y=400)

		self.construct()
		corner_angle = math.atan(self.width / self.height)
		self.cameras = [Camera(self, 0, 175), Camera(self, corner_angle, 100), Camera(self, -corner_angle, 100),
						Camera(self, 3 * corner_angle, 50), Camera(self, -3 * corner_angle, 50),
						Camera(self, math.pi/2, 30), Camera(self, -math.pi/2, 30)
						]
		self.cameras = [Camera(self, 0,175)] * 9

		self.start_time = time.time()
		self.time = 0
		self.last_action = 0
		self.action_rate = 0.1 # only do something once every 100ms
		self.driver = neural.Driver(2+len(self.cameras)) # neural network
		self.human = human

		self.times = defaultdict(list)

	def set_and_get_avg_time(self, cat, time, limit=10):
		self.times[cat].append(time)
		if len(self.times[cat]) > limit:
			self.times[cat].pop(0)
		return sum(self.times[cat]) / len(self.times[cat])

	def get_avg_time(self, cat):
		return len(self.times[cat]) and sum(self.times[cat]) / len(self.times[cat]) or 0

	def construct(self):
		global car_batch
		if car_batch:
			self.batch = car_batch
			return
		colours = (255,0,0, 255,0,0, 0,255,0, 0,255,0)

		self.batch.add(4, pyglet.gl.GL_LINE_LOOP, None,
			('v2f', sum(self.quad.vertices, tuple())),
			('c3B', colours))

		self.points_batch.add(4, pyglet.gl.GL_POINTS, None,
			('v2f', sum(self.quad.vertices, tuple())),
			('c3B', (255,0,0) * 4))

		car_batch = self.batch

	@property
	def position(self):
		return Point(self.x, self.y)

	@position.setter
	def position(self, point):
		point = Point(*point)
		self.x = point.x
		self.y = point.y

	def draw(self):
		super().draw()

		glLoadIdentity()
		#self.draw_points()
		#self.draw_cameras()

	def draw_section(self):
		self.section_batch.draw()

	def draw_labels(self):
		self.info_label.draw()

	def draw_points(self):
		glPointSize(5)
		self.points_batch.draw()

	def draw_cameras(self):
		glLoadIdentity()
		glPointSize(5)
		for camera in self.cameras:
			pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
				('v2f', camera.line.coords))
			pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
				('v2f', camera.focus))

	def update(self, dt):
		if self.collided: return
		if not self.human and self.time > 3 and self.section_idx == 0:
			self.collided = True
			return
		if abs(self.steering) > 5:
			self.collided = True # broke
			return
		self.time += dt
		#self.iters = (self.iters + 1) % 10
		t0 = time.time()
		if self.time - self.last_action  > self.action_rate:
			self.make_action()
			self.last_action = self.time
		t1 = time.time()
		self.rotate(dt)
		t2 = time.time()
		self.move(dt)
		t3 = time.time()
		if self.check_collision():
			self.move(-dt)
			self.rotate(-dt)
			self.speed = 0
			self.collided = True
			return
		t4 = time.time()
		self.check_section_change()
		t5 = time.time()
		[camera.update() for camera in self.cameras]
		t6 = time.time()
		a = 1000 * self.set_and_get_avg_time('action', t1 - t0)
		r = 1000 * self.set_and_get_avg_time('rotate', t2 - t1)
		m = 1000 * self.set_and_get_avg_time('move', t3 - t2)
		c = 1000 * self.set_and_get_avg_time('collision', t4 - t3)
		s = 1000 * self.set_and_get_avg_time('section_change', t5 - t4)
		d = 1000 * self.set_and_get_avg_time('camera', t6 - t5)
		self.times['string'] = "act=%.3f,move=%.3f, rot=%.3f, coll=%.3f,cam=%.3f,sec=%.3f" % (a, m, r, c, d, s)
		l = 1000 * self.get_avg_time('crline')
		f = 1000 * self.get_avg_time('focus')
		s = 1000 * self.get_avg_time('secsel')
		fi = 1000 * self.get_avg_time('focint')
		fd = 1000 * self.get_avg_time('focdist')
		bi = 1000 * self.get_avg_time('bordint')
		self.times['string'] = "crline:%.3f,focus:%.3f,secsel:%.3f,focint:%.3f,focdist:%.3f,bordint:%.3f" % (l, f, s, fi, fd, bi)
		#self.info_label.text = "action: %.5f, move: %.5f, rotate: %.5f, section change: %.5f" % (
		#	(t2 - t1, t3 - t2, t4 - t3, t5 - t4))

	def make_action(self):
		if self.human:
			return
		# feed the data to the neural network
		distances = [camera.distance for camera in self.cameras]
		self.steering = self.driver.compute(self.speed, self.steering, *distances) #0-0.5 is left, 0.5-1 is right
		if self.steering > 1:
			self.steering = 1
		elif self.steering < -1:
			self.steering = -1
		#print("\rself.steering = %.3f" % self.steering, end="")

	def update_points(self):
		vertices = sum([self.top_left, self.top_right, self.bottom_right, self.bottom_left], tuple())
		self.points_batch = pyglet.graphics.Batch()
		self.points_batch.add(4, pyglet.gl.GL_POINTS, None,
			('v2f', vertices),
			('c3B', (255,0,0, 150,150,0, 0,150,150, 0,0,255)))

	def accelerate(self, diff):
		new_speed = self.speed + diff
		self.speed = min(self.max_speed, abs(self.speed + diff))
		if new_speed < 0:
			self.speed = -self.speed

	def move(self, dt):
		direction = self.rot
		delta_x = self.speed * math.sin(direction) * dt
		delta_y = self.speed * math.cos(direction) * dt
		self.x += delta_x
		self.y += delta_y

		self.top_left = self.top_left.shifted(delta_x, delta_y)
		self.top_right = self.top_right.shifted(delta_x, delta_y)
		self.bottom_left = self.bottom_left.shifted(delta_x, delta_y)
		self.bottom_right = self.bottom_right.shifted(delta_x, delta_y)

		#[camera.update() for camera in self.cameras]

	def rotate(self, dt):
		if not self.steering:
			return
		degree = self.max_steering * self.steering * dt
		self.rot += (degree * math.pi / 180) *  [-1, 1][self.speed >= 0]
		self.rot %= 2 * math.pi
		self.prev_rot = self.rot

		self.rotate_corners()
		#[camera.update() for camera in self.cameras]
	
	def rotate_corners(self):
		new_left = Line(self.position, angle=-self.corner_angle + self.rot, length=self.corner_distance).end
		new_right = Line(self.position, angle=self.corner_angle + self.rot, length=self.corner_distance).end
		dlx, dly = new_left.x - self.top_left.x, new_left.y - self.top_left.y
		drx, dry = new_right.x - self.top_right.x, new_right.y - self.top_right.y
		self.top_left = new_left
		self.bottom_right = self.bottom_right.shifted(-dlx, -dly)
		self.top_right = new_right
		self.bottom_left = self.bottom_left.shifted(-drx, -dry)

	def reset_corners(self):
		self.top_left = Line((0,0), self.quad.top_left).rotated(-self.rot).moved(self.x, self.y).end
		self.top_right = Line((0,0), self.quad.top_right).rotated(-self.rot).moved(self.x, self.y).end
		self.bottom_left = Line((0,0), self.quad.bottom_left).rotated(-self.rot).moved(self.x, self.y).end
		self.bottom_right = Line((0,0), self.quad.bottom_right).rotated(-self.rot).moved(self.x, self.y).end

	def put_on_track(self, track):
		self.winner = False
		self.collided = False
		self.track = track
		self.change_section(0)
		self.time = 0
		self.position = self.section.quad.line.centre
		self.rot = self.section.quad.line.angle
		self.reset_corners()
		self.speed = 0
		self.last_action = 0
		[camera.update() for camera in self.cameras]
		self.start_time = time.time()

	def change_section(self, idx):
		self.section = self.track.sections[idx]
		self.section_idx = idx
		self.section_batch = pyglet.graphics.Batch()
		self.section.add_to_batch(self.section_batch, colours=(0,150,0,0,150,0,0,85,120,0,85,120), sides=False)

	def check_section_change(self):
		if not self.track:
			return
		change = self.section.car_has_left(self)
		new_idx = self.section_idx + change
		if new_idx < 0:# and not self.track.circular:
			self.collided = True
		elif new_idx == len(self.track.sections) and not self.track.circular:
			self.collided = True
			self.winner = True
			return
		elif change:
			self.change_section(new_idx % len(self.track.sections))

	def check_collision(self):
		if not (self.track and self.section):
			return
		left_line = Line(self.top_left, self.bottom_left)
		right_line = Line(self.top_right, self.bottom_right)
		last_border = None
		i = self.section_idx
		while True:
			if i < 0 or i >= len(self.track.sections):
				break
			section = self.track.sections[i]
			if section.car_hit_border(left=left_line, right=right_line):
				return True
			if last_border != "back" and (left_line.intersects(section.quad.front) or right_line.intersects(section.quad.front)):
				last_border = "front"
				i += 1
			elif last_border != "front" and (left_line.intersects(section.quad.back) or right_line.intersects(section.quad.back)):
				last_border = "back"
				i -= 1
			else:
				break

	def check_collision_old(self):
		if not (self.track and self.section):
			return
		start = max(self.section_idx - 1, 0)
		end = min(self.section_idx + 2, len(self.track.sections))
		for section in self.track.sections[start:end]:
			if section.car_hit_border(car=self):
				return True


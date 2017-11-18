import math
import time
from collections import defaultdict
import pyglet
import numpy as np

import graphtools
import neural
from drawables import *
from cext import cmodule

car_batch = None

class SensorRig(object):
	def __init__(self, car, angles, distances):
		if len(angles) != len(distances):
			raise ValueError("Number of angles and distances provided must match")
		self.car = car
		self.angles = np.array(angles)
		self.max_distances = distances
		self.distances = self.max_distances[:] # copy just in case
		#self.points = [(0,0)] * len(self.distances)
		self.caddr = cmodule.store_sensors(self.angles, self.max_distances)

	def __del__(self):
		cmodule.delete_sensors(self.caddr)

	def get_distances(self, position, rotation, section_idx):
		self.distances = cmodule.find_track_intersection(self.caddr, position, rotation, section_idx)

	def reset(self):
		self.distances = self.max_distances[:]
		#self.points = [(0,0)] * len(self.distances)

	@property
	def points(self):
		if not self.distances:
			return []
		x = np.array([self.car.x] * len(self.angles)) + np.sin(self.angles+self.car.rot) * self.distances
		y = np.array([self.car.y] * len(self.angles)) + np.cos(self.angles+self.car.rot) * self.distances
		return zip(x,y)

class Car(Entity):
	def __init__(self, human=False, sensors=None):
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
		if not sensors:
			self.sensors = SensorRig(self,
				(-math.pi/2, -3 * corner_angle, -corner_angle, 
				0,
				corner_angle, 3 * corner_angle, math.pi/2),
				(30, 50, 100, 175, 100, 50, 30))
		elif sensors == 1:
			self.sensors = SensorRig(self, (0,), (175,))
		else:
			n = sensors // 2 * 2 + 1
			angles = tuple(-math.pi/2 + i*math.pi/(n-1) for i in range(n))
			distances = (100,) * n
			self.sensors = SensorRig(self, angles, distances)

		self.start_time = time.time()
		self.time = 0
		self.last_action = 0
		self.action_rate = 0.1 # only do something once every 100ms
		self.driver = neural.Driver(2+len(self.sensors.distances)) # neural network
		self.human = human

		self.times = defaultdict(list)

	def set_and_get_avg_time(self, cat, time, limit=20):
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

	def draw_section(self):
		glLoadIdentity()
		self.section_batch.draw()

	def draw_labels(self):
		self.info_label.draw()

	def draw_points(self):
		glPointSize(5)
		self.points_batch.draw()

	def draw_sensors(self):
		glLoadIdentity()
		glPointSize(5)
		for point in self.sensors.points:
			pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
				('v2f', point))

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
		#self.sensors.get_distances((self.x, self.y), self.rot, self.section_idx)
		self.sensors.distances = cmodule.find_track_intersection(self.sensors.caddr, (self.x, self.y), self.rot, self.section_idx)
		t6 = time.time()
		a = 1000 * self.set_and_get_avg_time('action', t1 - t0)
		r = 1000 * self.set_and_get_avg_time('rotate', t2 - t1)
		m = 1000 * self.set_and_get_avg_time('move', t3 - t2)
		c = 1000 * self.set_and_get_avg_time('collision', t4 - t3)
		s = 1000 * self.set_and_get_avg_time('section_change', t5 - t4)
		d = 1000 * self.set_and_get_avg_time('sensors', t6 - t5, limit=1)
		self.times['string'] = "act=%.3f,move=%.3f, rot=%.3f, coll=%.3f,sen=%.3f,sec=%.3f" % (a, m, r, c, d, s)

	def make_action(self):
		return
		if self.human:
			return
		# feed the data to the neural network
		distances = self.sensors.distances
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

	def rotate(self, dt):
		if not self.steering:
			return
		degree = self.max_steering * self.steering * dt
		self.rot += (degree * math.pi / 180) *  [-1, 1][self.speed >= 0]
		self.rot %= 2 * math.pi
		self.prev_rot = self.rot

		self.rotate_corners()
	
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
		self.sensors.reset()
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


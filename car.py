import math
import time
import pyglet
import numpy as np
from collections import defaultdict

import neural
from drawables import *
from geometry import Point, Line, PI, TAU, DEG_TO_RAD, RAD_TO_DEG
try:
	from cext import cmodule
except ImportError:
	cmodule = None

car_batch = None

class SensorRig(object):
	def __init__(self, car, angles, distances):
		if len(angles) != len(distances):
			raise ValueError("Number of angles and distances provided must match")
		self.car = car
		self.size = len(angles)
		self.angles = np.array(angles)
		self.max_distances = distances
		self.distances = self.max_distances[:] # copy just in case
		#self.points = [(0,0)] * len(self.distances)
		if cmodule:
			self.caddr = cmodule.store_sensors(self.angles, self.max_distances)

	def __del__(self):
		if cmodule:
			cmodule.delete_sensors(self.caddr)

	def sensor_distance(self, idx, position, rotation, section_idx):
		x = position[0] + math.sin(self.angles[idx] + rotation) * self.max_distances[idx]
		y = position[1] + math.cos(self.angles[idx] + rotation) * self.max_distances[idx]
		line = (position[0], position[1], x, y)
		point = self.car.track.find_intersection(line, section_idx)
		if point:
			return ((point[0] - position[0]) ** 2 + (point[1] - position[1]) ** 2) ** 0.5
		else:
			return self.max_distances[idx]

	def get_distances(self, position, rotation, section_idx):
		if cmodule:
			self.distances = cmodule.find_rig_distances(self.caddr, position, rotation, section_idx)
		else:
			self.distances = tuple(self.sensor_distance(i, position, rotation, section_idx) for i in range(self.size))

	def reset(self):
		self.distances = self.max_distances[:]

	@property
	def points(self):
		if not self.distances:
			return []
		x = np.array([self.car.x] * self.size) + np.sin(self.angles+self.car.rot) * self.distances
		y = np.array([self.car.y] * self.size) + np.cos(self.angles+self.car.rot) * self.distances
		return zip(x,y)

class Car(Entity):
	def __init__(self, sensors=None, human=False, timeperf=False):
		super().__init__()

		self.max_speed = 150
		self.rot = 0
		self.speed = 0
		self.max_steering = 180
		self.steering = 0

		self.width = 10
		self.height = 30

		self.quad = Quad(box=Box(-self.width/2, self.height/2, self.width, self.height))

		self.corner_distance = Line(self.position, self.quad.top_left).length
		self.corner_angle = Line(self.position, self.quad.top_right).angle
		_ = self.corners # to set corner attributes

		self.track = None
		self.collided = False
		self.section = None
		self.section_idx = -1
		self.section_batch = pyglet.graphics.Batch()
		self.section_batch_idx = -1

		self.info_label = pyglet.text.Label(text="", x=0, y=400)

		self.construct()
		if not sensors:
			self.sensors = SensorRig(self,
				(-PI/2, -3 * self.corner_angle, -self.corner_angle, 
				0,
				self.corner_angle, 3 * self.corner_angle, PI/2),
				(30, 50, 100, 175, 100, 50, 30))
		elif sensors == 1:
			self.sensors = SensorRig(self, (0,), (175,))
		else:
			n = sensors // 2 * 2 + 1
			angles = tuple(-PI/2 + i*PI/(n-1) for i in range(n))
			distances = (100,) * n
			self.sensors = SensorRig(self, angles, distances)

		self.start_time = time.time()
		self.time = 0
		self.last_action = 0
		self.action_rate = 0.001 # only do something once every 1ms
		self.driver = neural.Driver(2+self.sensors.size) # neural network
		self.human = human

		self.timeperf = timeperf
		self.times = defaultdict(list)
		self.times['string'] = ""

	def set_and_get_avg_time(self, cat, time, limit=20):
		self.times[cat].append(time)
		if len(self.times[cat]) > limit:
			self.times[cat].pop(0)
		return sum(self.times[cat]) / len(self.times[cat])

	def get_avg_time(self, cat):
		return len(self.times[cat]) and sum(self.times[cat]) / len(self.times[cat]) or 0

	def construct(self):
		global car_batch
		self.line_colours = (
			1,0,0,1,0,0, 1,0,0,0,1,0,
			0,1,0,0,1,0, 0,1,0,1,0,0)
		#self.line_colours = tuple(np.random.uniform(0,1, size=6*4))
		if car_batch:
			self.batch = car_batch
			return
		colours = (1,0,0, 1,0,0, 0,1,0, 0,1,0)

		self.batch.add(4, pyglet.gl.GL_LINE_LOOP, None,
			('v2f', sum(self.quad.vertices, tuple())),
			('c3f', colours))

		car_batch = self.batch

	@property
	def position(self):
		return (self.x, self.y)

	@position.setter
	def position(self, point):
		self.x = point[0]
		self.y = point[1]

	@property
	def corners(self):
		sdism = self.corner_distance*math.sin(self.rot - self.corner_angle)
		cdism = self.corner_distance*math.cos(self.rot - self.corner_angle)
		sdisp = self.corner_distance*math.sin(self.rot + self.corner_angle)
		cdisp = self.corner_distance*math.cos(self.rot + self.corner_angle)
		self.top_left = (self.x + sdism, self.y + cdism)
		self.top_right = (self.x + sdisp, self.y + cdisp)
		self.bottom_right = (self.x - sdism, self.y - cdism)
		self.bottom_left = (self.x - sdisp, self.y - cdisp)
		return self.top_left + self.top_right + self.bottom_right + self.bottom_left

	@property
	def linecoords(self):
		c = self.corners
		return (c[0],c[1],c[2],c[3],
				c[2],c[3],c[4],c[5],
				c[4],c[5],c[6],c[7],
				c[6],c[7],c[0],c[1])

	@property
	def lines(self):
		c = self.corners
		return ((c[0],c[1],c[2],c[3]),
				(c[2],c[3],c[4],c[5]),
				(c[4],c[5],c[6],c[7]),
				(c[6],c[7],c[0],c[1]))

	@property
	def sides(self):
		c = self.corners
		return 	((c[2],c[3],c[4],c[5]),
				(c[6],c[7],c[0],c[1]))

	def draw(self):
		super().draw()
		return
		glLoadIdentity()
		pyglet.graphics.draw(8, GL_LINES,
			('v2f', self.linecoords),
			('c3f', self.line_colours)
		)


	def draw_section(self):
		glLoadIdentity()
		if self.section_batch_idx != self.section_idx:
			self.section_batch = pyglet.graphics.Batch()
			self.section.add_to_batch(self.section_batch, colours=(0,150/255,0,0,150/255,0,0,85/255,120/255,0,85/255,120/255), sides=False)
			self.section_batch_idx = self.section_idx
		self.section_batch.draw()

	def draw_labels(self):
		self.info_label.draw()

	def draw_points(self):
		glPointSize(5)
		pyglet.graphics.draw(4, pyglet.gl.GL_POINTS,
			('v2f', self.corners),
			('c3f', (1,0,0, 150/255,150/255,0, 0,150/255,150/255, 0,0,1)))

	def draw_sensors(self):
		glLoadIdentity()
		glPointSize(5)
		points = tuple(self.sensors.points)
		n = len(points)
		points = sum(points,())
		pyglet.graphics.draw(n, pyglet.gl.GL_POINTS,
			('v2f', points))

	def update(self, dt):
		t0 = time.time()
		if self.collided: return
		if not self.human and self.time > 3 and self.section_idx == 0:
			self.collided = True
			return
		if abs(self.steering) > 5:
			self.collided = True # broke
			return
		self.time += dt
		t1 = time.time()
		self.rotate(dt)
		t2 = time.time()
		self.move(dt)
		t3 = time.time()
		side = self.check_collision()
		if side:
			self.move(-dt)
			self.rotate(-dt)
			self.speed = 0
			self.collided = True
			return
		t4 = time.time()
		self.check_section_change()
		t5 = time.time()
		self.sensors.get_distances((self.x, self.y), self.rot, self.section_idx)
		t6 = time.time()
		if self.time - self.last_action  > self.action_rate:
			self.make_action()
			self.last_action = self.time
		t7 = time.time()
		if self.timeperf:
			r = 1000000 * self.set_and_get_avg_time('rotate', t2 - t1)
			m = 1000000 * self.set_and_get_avg_time('move', t3 - t2)
			c = 1000000 * self.set_and_get_avg_time('collision', t4 - t3)
			s = 1000000 * self.set_and_get_avg_time('section_change', t5 - t4)
			d = 1000000 * self.set_and_get_avg_time('sensors', t6 - t5)
			a = 1000000 * self.set_and_get_avg_time('action', t7 - t6)
			t = 1000000 * self.set_and_get_avg_time('upd', t7 - t0)
			self.times['string'] = "%.3fus:act=%3dus,move=%04.1fus,rot=%04.1fus,coll=%04.1fus,sen=%04.1fus,sec=%04.1fus" % (t, a, m, r, c, d, s)

	def make_action(self):
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

	def accelerate(self, diff):
		new_speed = self.speed + diff
		self.speed = min(self.max_speed, abs(self.speed + diff))
		if new_speed < 0:
			self.speed = -self.speed

	def move(self, dt):
		if not self.speed:
			return
		direction = self.rot
		self.x += self.speed * math.sin(direction) * dt
		self.y += self.speed * math.cos(direction) * dt

	def rotate(self, dt):
		if not self.steering:
			return
		degree = self.max_steering * self.steering * dt
		if self.speed >=0:
			self.rot += degree * DEG_TO_RAD
			if self.rot > TAU:
				self.rot -= TAU
		else:
			self.rot -= degree * DEG_TO_RAD
			if self.rot < -TAU:
				self.rot += TAU

	def put_on_track(self, track):
		self.winner = False
		self.collided = False
		self.track = track
		self.change_section(0)
		self.time = 0
		#self.position = self.track.sections[0].quad.line.centre
		#self.rot = self.track.sections[0].quad.line.angle
		self.position = self.section.quad.line.centre
		self.x += np.random.random() * 20 - 10
		self.rot = self.section.quad.line.angle
		self.speed = np.random.uniform(0, 50)
		self.steering = np.random.uniform(-0.1,0.1)
		self.last_action = 0
		self.sensors.reset()
		self.start_time = time.time()

	def change_section(self, idx):
		self.section = self.track.sections[idx]
		self.section_idx = idx

	def check_section_change(self):
		if not self.track:
			return
		if cmodule:
			change = cmodule.changed_section((self.x, self.y), self.section_idx)
		else:
			change = self.section.changed_section((self.x, self.y))
		new_idx = self.section_idx + change
		if new_idx < 0:# and not self.track.circular:
			self.collided = True
		elif new_idx == self.track.length and not self.track.circular:
			self.collided = True
			self.winner = True
			return
		elif change:
			self.change_section(new_idx % self.track.length)

	def check_collision(self):
		if not self.track:
			return
		if cmodule:
			# a function call for each car is way too expensive, so access the cmodule
			# directly from here
			#return self.track.check_car_collision((self.x, self.y), self.rot, self.section_idx)
			return cmodule.check_car_collision((self.x, self.y), self.rot, self.section_idx)
		else:
			# in python it doesn't matter, an extra microsecond is negligible
			# compared to the total execution time of ~50us
			box = self.lines[1:4:2] # left and right sides only
			#box = self.lines
			for line in box:
				if self.track.find_intersection(line, self.section_idx):
					return True


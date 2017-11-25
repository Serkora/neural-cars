import math
import time
import pyglet
import numpy as np
from collections import defaultdict

import neural
import drawables
from drawables import *
from geometry import Point, Line, PI, TAU, DEG_TO_RAD, RAD_TO_DEG
try:
	from cext import cmodule
except ImportError:
	cmodule = None
#cmodule = None

class SensorRig(object):
	def __init__(self, car, angles, distances):
		if len(angles) != len(distances):
			raise ValueError("Number of angles and distances provided must match")
		self.car = car
		self.size = len(angles)
		self.angles = np.array(angles)
		self.max_distances = distances
		self.distances = self.max_distances[:] # copy just in case
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
	def __init__(self, sensors=None, human=False):
		super().__init__()

		self.update = self.update_no_track

		self.max_speed = 150
		self.rot = 0
		self.speed = 0
		self.max_steering = PI / 3
		self.steering = 0

		self.width = 10
		self.length = 30
		self.wbase = self.length / 2

		self.quad = Quad(box=Box(-self.width/2, self.length/2, self.width, self.length))

		self.corner_distance = Line(self.position, self.quad.top_left).length
		self.corner_angle = Line(self.position, self.quad.top_right).angle
		_ = self.corners # to set corner attributes

		self.track = None
		self.collided = False
		self.section = None
		self.section_idx = -1
		self.section_batch = pyglet.graphics.Batch()
		self.section_batch_idx = -1

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
		self.driver = neural.Driver(1+self.sensors.size) # neural network
		self.human = human

	def construct(self):
		self.line_colours = drawables.gradient_line_colours('red', 'green', 'green', 'red')
		self.corner_colours = drawables.vertex_colours('red', 'red', 'green', 'green')

		self.batch.add(4, pyglet.gl.GL_LINE_LOOP, None,
			('v2f', sum(self.quad.vertices, tuple())),
			('c3f', self.corner_colours))

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
		return c[:4] + c[2:6] + c[4:8] + c[6:] + c[:2]

	@property
	def lines(self):
		c = self.corners
		return (c[:4], c[2:6], c[4:8], c[6:] + c[:2])

	@property
	def sides(self):
		c = self.corners
		return (c[2:6], c[6:] + c[:2])

	def draw_section(self):
		glLoadIdentity()
		if self.section_batch_idx != self.section_idx:
			self.section_batch = pyglet.graphics.Batch()
			self.section.add_to_batch(self.section_batch, colours=(0,150/255,0,0,150/255,0,0,85/255,120/255,0,85/255,120/255), sides=False)
			self.section_batch_idx = self.section_idx
		self.section_batch.draw()

	def draw_points(self):
		glPointSize(5)
		fwx = self.x + self.wbase * math.sin(self.rot)
		fwy = self.y + self.wbase * math.cos(self.rot)
		bwx = self.x - self.wbase * math.sin(self.rot)
		bwy = self.y - self.wbase * math.cos(self.rot)
		pyglet.graphics.draw(4+2, pyglet.gl.GL_POINTS,
			('v2f', self.corners + (fwx, fwy, bwx, bwy)),
			('c3B', (255,0,0, 150,150,0, 0,150,150, 0,0,255, 0,255,0, 0,255,255)))

	def draw_sensors(self):
		glLoadIdentity()
		glPointSize(5)
		points = tuple(self.sensors.points)
		n = len(points)
		points = sum(points,())
		pyglet.graphics.draw(n, pyglet.gl.GL_POINTS,
			('v2f', points))

	def update_no_track(self, dt):
		#self.time += dt
		self.move(dt)

	def update_track(self, dt):
		#self.time += dt
		self.move(dt)
		side = self.check_collision()
		if side:
			self.speed = 0
			self.collided = True
			self.update = lambda dt: None
			return
		self.check_section_change()
		self.sensors.get_distances((self.x, self.y), self.rot, self.section_idx)
		self.make_action()

	def update_track_c(self, dt):
		#self.time += dt
		self.move(dt)
		#self.x, self.y, self.rot = cmodule.move((self.x, self.y), self.rot, self.speed, self.steering, dt))
		side = cmodule.check_car_collision((self.x, self.y), self.rot, self.section_idx)
		if side:
			self.speed = 0
			self.collided = True
			self.update = lambda dt: None
			return
		change = cmodule.changed_section((self.x, self.y), self.section_idx)
		if change:
			self.change_section(self.section_idx + change)
		self.sensors.get_distances((self.x, self.y), self.rot, self.section_idx)
		self.make_action()

	def make_action(self):
		if self.human:
			return
		# feed the data to the neural network
		self.steering = self.max_steering * self.driver.compute(self.speed, *self.sensors.distances)

	def accelerate(self, diff):
		new_speed = self.speed + diff
		self.speed = min(self.max_speed, abs(self.speed + diff))
		if new_speed < 0:
			self.speed = -self.speed

	def move(self, dt):
		if not self.speed:
			return
		direction = self.rot
		d = self.speed * dt
		sdir = math.sin(direction)
		cdir = math.cos(direction)
		fwx = self.wbase * sdir + d * math.sin(direction + self.steering)
		fwy = self.wbase * cdir + d * math.cos(direction + self.steering)
		bwx = sdir * (d - self.wbase)
		bwy = cdir * (d - self.wbase)
		self.x += (fwx + bwx) / 2
		self.y += (fwy + bwy) / 2
		self.rot = math.atan2(fwx - bwx, fwy - bwy)

	def put_on_track(self, track):
		self.winner = False
		self.collided = False
		self.track = track
		self.change_section(0)
		self.time = 0
		self.position = self.section.quad.line.centre
		self.rot = self.section.quad.line.angle
		self.x += np.random.random() * 30 - 15
		self.speed = 0
		self.steering = 0
		self.last_action = 0
		self.sensors.reset()
		self.start_time = time.time()
		if cmodule:
			self.update = self.update_track_c
		else:
			self.update = self.update_track

	def change_section(self, idx):
		if idx < 0 and not self.track.circular:
			self.collided = True
			return
		elif idx == self.track.length and not self.track.circular:
			self.collided = True
			self.winner = True
			return
		idx %= self.track.length
		self.section = self.track.sections[idx]
		self.section_idx = idx

	def check_collision(self):
		return self.track.check_car_collision(self)

	def check_section_change(self):
		change = self.section.changed_section((self.x, self.y))
		if change:
			self.change_section(self.section_idx + change)



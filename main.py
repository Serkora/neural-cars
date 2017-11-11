import operator
import time
import math
from collections import defaultdict
import pyglet
from pyglet.gl import *
from pyglet.window import key

from car import Car
from track import Track


def vec(*args):
	return (GLfloat * len(args))(*args)

class Simulator(pyglet.window.Window):
	def __init__(self, *args, **kwargs):
		config = pyglet.gl.Config(*args, sample_buffers=1, samples=1, depth_size=16, double_buffer=True, **kwargs)
		super().__init__(*args, config=config, resizable=True, vsync=True, **kwargs)
		self.keystate = key.KeyStateHandler()
		self.push_handlers(self.keystate)

		self.car = Car() # will be deleted later, not even drawn
		self.track = Track()
		self.generation = 1

		self.time = 0
		self.fps = pyglet.clock.ClockDisplay()
		self.times = defaultdict(list)
		self.counter = 0

		self.setup_labels()

		self.x = 0
		self.y = 0
		self.scale = 1

		pyglet.clock.schedule_interval(self._update, 1.0 / 60)

	def setup_labels(self):
		self.time_label = pyglet.text.Label(text="", x=10, y=self.height-20)
		self.info_label = pyglet.text.Label(text="", x=10, y=self.height-40)
		self.info_label.text = "Generation: %d" % self.generation

	def start(self, makecars=False):
		if makecars:
			self.cars = [Car() for i in range(10)]
		self.car = self.cars[0]
		[car.put_on_track(self.track) for car in self.cars]
		[car.accelerate(50) for car in self.cars]

	def evolve(self):
		self.generation += 1
		self.info_label.text = "Generation: %d" % self.generation
		cars = sorted(self.cars, key=operator.attrgetter('section_idx', 'time'), reverse=True)
		if cars[0].section_idx < 2:
			#print("Don't have at least two good specimen, randomizing")
			[car.driver.randomize() for car in self.cars]
			return
		best = cars[0]
		runnerup = cars[1]
		self.cars = [Car() for i in range(10)]
		self.cars[0].driver.copy(best.driver)
		self.cars[1].driver.copy(runnerup.driver)
		[car.driver.copy(best.driver) for car in self.cars[2:6]]
		[car.driver.copy(runnerup.driver) for car in self.cars[6:]]
		for i in range(4):
			#print("mutating a pair of cars. severity: %d, chance: %d" % (5*(i+1), 100-25*i))
			self.cars[i+2].driver.mutate(0.05*(i+1), 1-0.25*i)
			self.cars[i+2+4].driver.mutate(0.05*(i+1), 1-0.25*i)
		#print("copied and mutated!")
		return True

	def set_and_get_avg_time(self, cat, time, limit=10):
		self.times[cat].append(time)
		if len(self.times[cat]) > limit:
			self.times[cat].pop(0)
		return sum(self.times[cat]) / len(self.times[cat])

	def _update(self, dt):
		dt = min(dt, 1/30) # slow down time instead of "dropping" frames and having quick jumps in space
		self.time += dt
		t1 = time.time()
		for key in self.keystate:
			if self.keystate[key]:
				self.dispatch_event('on_key_press', key, False)
		[car.update(dt) for car in self.cars]
		if all(car.collided for car in self.cars):
			created_cars = self.evolve()
			self.start(not created_cars)
			return
		leader = sorted(self.cars, key=operator.attrgetter('section_idx'))[-1]
		if self.car.section_idx < leader.section_idx:
			self.car = leader
		t2 = time.time()
		#self.car.update(dt)
		#self.x = self.car.x
		#self.y = self.car.y
		self.counter += 1
		#if self.counter % 10: return
		self.draw()
		t3 = time.time()
		#print("\rdraw: %.3f, update: %.3f, dt = %.3f" % (t3 - t2, t2 - t1, dt), end="")
		#self.info_label.text = "\rdraw: %.3f, update: %.3f, dt = %.3f" % (t3 - t2, t2 - t1, dt)
		drawtime = self.set_and_get_avg_time('draw', t3 - t2, 5)
		updatetime = self.set_and_get_avg_time('update', t2 - t1, 5)
		carupdate = self.car.times['string']
		#print("\rdraw: %.3f, update: %.3f, dt = %.3f; car update: %s" % (drawtime, updatetime, dt, carupdate), end="")
		self.info_label.text = "draw=%.3f,upd=%.3f,dt=%.3f; car upd: %s" % (drawtime, updatetime, dt, carupdate)

	def setup2d_init(self):
		"""
		2Д. gluPerspective заменяетсяна glOrtho. Чтобы рисовать лейблы, фпс,
		какие-нибудь текстурки типа меню и т.д., которые не "в мире", а просто на экране.
		Есть проблемы — если загружать спрайты, текстуры с объектов пропадают.
		"""
		glClear(GL_COLOR_BUFFER_BIT)
		glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(0,0,0,1))
		glColor3ub(255,255,255)
		glViewport(0, 0, self.width, self.height) 
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(0, self.width, 0, self.height)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()

	def setup2d_camera(self):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		#gluOrtho2D(0+self.x, self.width+self.x, 0+self.y, self.height+self.y)
		#gluOrtho2D(0+self.x, self.width/2+self.x, 0+self.y, self.height/2+self.y)
		gluOrtho2D(self.scale*(-self.width/2 + self.x), self.scale*(self.width/2 + self.x),
			self.scale*(-self.height/2 + self.y), self.scale*(self.height/2 + self.y))
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()

	def draw(self):
		self.clear()
		self.setup2d_init()

		self.fps.draw()
		self.draw_labels()

		self.setup2d_camera()
		self.track.draw()
		#self.car.draw()
		[car.draw() for car in self.cars]
		#self.car.draw_section()
		#self.car.draw_points()
		#self.car.draw_cameras()

	def draw_labels(self):
		self.time_label.text = "Time: %.3f" % self.time
		#self.info_label.text = "x: %.2f, y: %.2f, rot: %.2f, speed: %.2f" % (
		#	self.car.x, self.car.y, self.car.rot * 180 / math.pi, self.car.speed)
		self.time_label.draw()
		self.info_label.draw()
		self.car.draw_labels()
		#self.track.draw_labels()
		
	def on_key_press(self, symbol, modifier):
		if symbol == key.ESCAPE:
			self.close()
		elif symbol == key.LEFT:
			self.car.steering = -0.5
		elif symbol == key.RIGHT:
			self.car.steering = 0.5
		elif symbol == key.UP:
			self.car.accelerate(2)
		elif symbol == key.DOWN:
			self.car.accelerate(-2)
		elif symbol == key.SPACE:
			if self.car.speed >= 0:
				self.car.speed = max(0, self.car.speed - 8)
			else:
				self.car.speed = min(0, self.car.speed + 8)
		elif symbol == key.W:
			self.y += 10
		elif symbol == key.S:
			self.y -= 10
		elif symbol == key.A:
			self.x -= 10
		elif symbol == key.D:
			self.x += 10
		elif symbol == key.E:
			if self.scale > 0.2:
				self.scale -= 0.1
		elif symbol == key.Q:
			if self.scale < 3:
				self.scale += 0.1
		elif symbol == key.C:
			self.car.check_collision()
			self.keystate[symbol] = False
		elif symbol == key.R:
			self.start()
			return
			self.car.x = 0
			self.car.y = 0
			self.car.rot = 0
			self.car.speed = 0
			self.car.update(0)
			self.car.change_section(0)
			self.car.rotate(0)
		elif symbol == key.N:
			self.car.change_section(self.car.section_idx + 1)
			self.keystate[symbol] = False
		elif symbol == key.P:
			self.car.change_section(self.car.section_idx - 1)
			self.keystate[symbol] = False

	def on_key_release(self, symbol, modifier):
		if symbol in [key.LEFT, key.RIGHT]:
			self.car.steering = 0

if __name__ == "__main__":
	simulator = Simulator(width=900)
	simulator.start(True)
	pyglet.app.run()
	print()

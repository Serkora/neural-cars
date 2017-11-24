import sys
import argparse
import operator
import time
import math
from collections import defaultdict
import pyglet
from pyglet.gl import *
from pyglet.window import key
from pyglet.graphics.vertexbuffer import VertexBufferObject
import numpy as np

from car import Car
from track import Track

try:
	from cext import cmodule
except ImportError:
	cmodule = None

def vec(*args):
	return (GLfloat * len(args))(*args)

class Simulator(pyglet.window.Window):
	def __init__(self, *args, settings=None, carnum=10, width=960, height=540, vsync=True, **kwargs):
		config = pyglet.gl.Config(sample_buffers=1, samples=1, depth_size=16, double_buffer=True)
		super().__init__(width=width, height=height, config=config, resizable=True, vsync=vsync)
		self.keystate = key.KeyStateHandler()
		self.push_handlers(self.keystate)

		self.settings = defaultdict(bool)
		if type(settings) == dict:
			self.settings.update(settings)

		self.init_speed = self.settings['speed'] if type(self.settings['speed']) == int else 25
		self.carnum = (carnum+1) // 2 * 2 # need even number
		self.cars = []
		self.car = Car(sensors=self.settings['sensors'], human=True, timeperf=self.settings['timings'] > 1) # will be deleted later if simulation starts
		self.carline_colours = tuple()
		self.track = Track()
		self.car.put_on_track(self.track)
		self.generation = 0
		self.cars_pos_vbo = VertexBufferObject(self.carnum * 64, GL_ARRAY_BUFFER, GL_DYNAMIC_DRAW)
		self.cars_col_vbo = VertexBufferObject(self.carnum * 96, GL_ARRAY_BUFFER, GL_DYNAMIC_DRAW)

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
		self.main_label = pyglet.text.Label(text="", x=10, y=self.height-20)
		self.maintimes_label = pyglet.text.Label(text="", x=10, y=self.height-40, font_name="Lucida Console", font_size=10)
		self.cartimes_label = pyglet.text.Label(text="", x=10, y=self.height-60, font_name="Lucida Console", font_size=10)
		#self.maintimes_label.text = "Generation: %d" % self.generation

	def start(self, makecars=False):
		if makecars:
			self.cars = [Car(sensors=self.settings['sensors'], timeperf=self.settings['timings'] > 1) for i in range(self.carnum)]
			self.carline_colours = sum((car.line_colours for car in self.cars),())
			self.cars_col_vbo.set_data(vec(*self.carline_colours))
		self.car = self.cars[0]
		for car in self.cars:
			car.put_on_track(self.track)
			car.accelerate(self.init_speed)

	def evolve(self):
		self.generation += 1
		#self.maintimes_label.text = "Generation: %d" % self.generation
		cars = sorted(self.cars, key=operator.attrgetter('section_idx', 'time'), reverse=True)
		if cars[0].section_idx < 1:
			#print("Don't have at least two good specimen, randomizing")
			[car.driver.randomize() for car in self.cars]
			return
			pass
		best = cars[0].driver
		runnerup = cars[1].driver
		to_mutate = (self.carnum - 2) // 2
		#print("best section: %d, runnerup section: %d" % (best.section_idx, runnerup.section_idx))
		for i, pair in enumerate(zip(self.cars[2::2], self.cars[3::2])):
			severity = 0.25 * i/to_mutate
			chance = 1 - i/to_mutate
			pair[0].driver.learn_from(best, mutate=i, chance=chance, severity=severity)
			pair[1].driver.learn_from(runnerup, mutate=i, chance=chance, severity=severity)
		#print("cars[0] == best: %s" % (self.cars[0].driver.network.layers[1].neurons[0].weights == best.driver.network.layers[1].neurons[0].weights))
		#print("cars[0] %d, best: %d" % (id(self.cars[0].driver.network.layers[1].neurons[0].weights), id(best.driver.network.layers[1].neurons[0].weights)))
		#print("copied and mutated!")

	def set_avg_time(self, cat, time, limit=10):
		self.times[cat].append(time)
		if len(self.times[cat]) > limit:
			self.times[cat].pop(0)

	def get_avg_time(self, cat):
		if len(self.times[cat]):
			return sum(self.times[cat]) / len(self.times[cat])
		else:
			return 0

	def set_and_get_avg_time(self, cat, time, limit=10):
		self.set_avg_time(cat, time, limit)
		return self.get_avg_time(cat)

	def _update(self, dt):
		dt = min(dt, 1/30) # slow down time instead of "dropping" frames and having quick jumps in space
		#dt = 1/30
		self.time += dt
		for key in self.keystate:
			if self.keystate[key]:
				self.dispatch_event('on_key_press', key, False)
		t1 = time.time()
		if len(self.cars):
			for car in self.cars:
				car.update(dt)
			if all(car.collided for car in self.cars):
				self.evolve()
				self.start()
				return
			leader = sorted(self.cars, key=operator.attrgetter('section_idx'))[-1]
			if self.car.section_idx < leader.section_idx:
				self.car = leader
		else:
			self.car.update(dt)
		t2 = time.time()
		self.x = self.car.x
		self.y = self.car.y
		self.draw()
		t3 = time.time()
		if self.settings['timings'] or self.settings['manual']:
			drawtime = 1000 * self.set_and_get_avg_time('draw', t3 - t2)
			cardraw = 1000 * self.get_avg_time('cardraw')
			coords = 1000 * self.get_avg_time('lines')
			drawcall = 1000 * self.get_avg_time('drawcall')
			updatetime = 1000 * self.set_and_get_avg_time('update', t2 - t1)
			carupdate = self.car.times['string']
			carupd = 1000000 * self.car.get_avg_time('upd')
			if carupdate:
				self.cartimes_label.text = "Per car: %s" % carupdate
			percar = 1000 * updatetime 
			if not self.settings['manual']:
				percar /= sum(not car.collided for car in self.cars)
			self.maintimes_label.text = "dt=%2dms,draw=%2dms(cars=%.2fms:coords=%.2fms,draw=%.2fms),upd=%04.1fms(%3dus/car)" % (1000*dt, drawtime, cardraw, coords, drawcall, updatetime, percar)

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
		t1 = time.time()
		self.draw_cars()
		#self.draw_cars_old()
		t2 = time.time()
		self.set_avg_time('cardraw', t2-t1)

	def draw_cars(self):
		glLoadIdentity()
		t1 = time.time()
		if len(self.cars):
			carnum = len(self.cars)
			if self.settings['drawlimit']:
				cars = np.random.choice(self.cars, self.settings['drawlimit'])
				carnum = len(cars)
				self.carline_colours = sum((car.line_colours for car in cars),())
				if self.car not in cars:
					self.car.draw() # to make sure the leader is drawn
					glLoadIdentity()
			else:
				cars = self.cars

			if cmodule:
				pos = ((car.x, car.y, car.rot) for car in cars)
				coords = cmodule.car_lines(pos, carnum)
				#c = np.array(coords, dtype=GLfloat)
				#coords = vec(*coords)
				#self.coords = np.array(coords, dtype=GLfloat).ctypes.data
				self.coords = coords
			else:
				coords = sum((car.linecoords for car in cars), ())
				self.coords = vec(*coords)
		
			t2 = time.time()

			self.cars_col_vbo.bind()
			glColorPointer(3, GL_FLOAT, 0, self.cars_col_vbo.ptr)
			self.cars_pos_vbo.set_data(self.coords)
			self.cars_pos_vbo.bind()
			glVertexPointer(2, GL_FLOAT, 0, self.cars_pos_vbo.ptr)
			glEnableClientState(GL_VERTEX_ARRAY)
			glEnableClientState(GL_COLOR_ARRAY)
			glDrawArrays(GL_LINES, 0, self.carnum * 16)
			glDisableClientState(GL_COLOR_ARRAY)
			glDisableClientState(GL_VERTEX_ARRAY)
			self.cars_col_vbo.unbind()
			self.cars_pos_vbo.unbind()

			#pyglet.graphics.draw(8 * carnum, GL_LINES,
			#	('v2f', coords),
			#	('c3B', self.carline_colours)
			#)
		else:
			t2 = time.time()
			self.car.draw()
		t3 = time.time()
		if self.settings['manual']:
			self.car.draw()
			self.car.draw_section()
			self.car.draw_points()
		if self.settings['cameras']:
			self.car.draw_sensors()
		t4 = time.time()
		self.set_avg_time('lines', t2 - t1)
		self.set_avg_time('drawcall', t3 - t2)
		self.set_avg_time('hidden', t4 - t3)

	def draw_labels(self):
		self.main_label.text = "Time: %.3f. Generation: %d" % (self.time, self.generation)
		#self.maintimes_label.text = "x: %.2f, y: %.2f, rot: %.2f, speed: %.2f" % (
		#	self.car.x, self.car.y, self.car.rot * 180 / math.pi, self.car.speed)
		self.main_label.draw()
		self.maintimes_label.draw()
		self.cartimes_label.draw()
		#self.car.draw_labels()
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
			if len(self.cars):
				self.start()
				return
			self.car.put_on_track(self.track)
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
	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-n', '--cars', action="store", type=int, default=10,
		help="Number of cars to train")
	parser.add_argument('--window-size', action="store", nargs=2, dest='wsize', metavar=('WIDTH', 'HEIGHT'), default=(960, 540))
	parser.add_argument('--width', action="store", type=int, default=None)
	parser.add_argument('--height', action="store", type=int, default=None)
	parser.add_argument('-m', '--manual', action="store_true", default=False,
		help="Drive the car yourself")
	parser.add_argument('-c', '--cameras', action="store_true", default=False,
		help="Show camera lines and points")
	parser.add_argument('--still', action="store_true", default=False,
		help="Disable neural network and don't move the cars")
	parser.add_argument('--speed', action="store", type=int, default=None,
		help="Set the initial car speed")
	parser.add_argument('-t', '--timings', action="store", type=int, default=0,
		help="Show various timings")
	parser.add_argument('-s', '--sensors', action="store", type=int, default=0,
		help="Number of sensors that span [-math.pi, math.pi]")
	parser.add_argument('--drawlimit', action="store", type=int, default=0,
		help="Max number of cars to draw (0 = draw all)")
	args = parser.parse_args()

	settings = {k:getattr(args, k) for k in ['manual', 'cameras', 'timings', 'sensors', 'drawlimit','speed']}
	simulator = Simulator(settings=settings, carnum=args.cars, width=args.width or args.wsize[0], height=args.height or args.wsize[1])
	if not args.manual:
		simulator.start(True)
	if args.still:
		for car in simulator.cars:
			car.speed = 0
			car.human = True
		
	pyglet.app.run()
	#print()

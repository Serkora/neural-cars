import sys
import os
sys.path.append(os.path.dirname(os.getcwd()))
import time
if len(sys.argv) > 1 and sys.argv[1] == "b":
	ret = os.system("python3 setup.py build")
	if ret != 0:
		sys.exit(ret)
import track
import cmodule
import math
import car
import ctypes

l1 = (0,0,5,5)
l2 = (5,0,0,5)

def intersec():
	t1 = time.time()
	r = cmodule.intersection(l1,l2)
	t2 = time.time()
	print("res = %s (%.3fus)" % (r, (1000000 * (t2 - t1))))

def ctrack():
	tr = track.Track()
	
	def section_to_array(section):
		out = []
		out.append(section.quad.front.coords)
		out.append(section.quad.back.coords)
		out.append(section.quad.left.coords)
		out.append(section.quad.right.coords)
		out.append(section.quad.line.coords)
		out.append(section.quad.line.angle)
		return out
	
	sections = [section_to_array(sec) for sec in tr.sections]
	#print(sections[0])
	#print(sections[1])
	
	cmodule.store_track(sections)

def speed_test():
	n = 100000
	t1 = time.time()
	for i in range(1):
		checks, intersections = ctrack.test(n)
	t2 = time.time()
	print("total for %d checks and %d intersections: %.3f ms" % (checks, intersections, 1000 * (t2-t1)))
	print("per exhaustive search (56/9): %.2fus" % (1000000 * (t2 - t1) / n))

def intersec_find():
	n = 1000
	t1 = time.time()
	for i in range(n):
		point = ctrack.test2((0,0 + i * 0.05,0,250), 0)
	t2 = time.time()
	t = 10**9 * (t2 - t1) / n
	print("Intersection point: (%.1f, %.1f), time per calc: %dns" % (point[0], point[1], t))

#intersec_find()

def sensors(delete=True):
	angles = (-math.pi/2, -math.pi/4, 0, math.pi/4, math.pi/2)
	distances = (50, 99, 250, 99, 50)
	addr = cmodule.store_sensors(angles, distances)
	if delete:
		cmodule.delete_sensors(addr)
	else:
		return addr

def inters():
	ctrack()
	addr = sensors(False)
	t1 = time.time()
	for i in range(1):
		inter = cmodule.find_track_intersection(addr, (0.5,0.5), 0, 0)
	t2 = time.time()
	print("intersections = %s (%.3fus)" % (str(inter), (1000000 * (t2-t1))))

def collision():
	ctrack()
	corners = (-15,15,15,15,15,-15,-15,-15)
	coll = cmodule.check_collision(corners, 0)
	print("collision = ", coll)

def linecoords():
	cars = [(1,5,0), (5,20,1)]
	cars = [(0,0,0)]
	carsgen = (car for car in cars)
	coords = cmodule.car_lines(carsgen, len(cars))
	for i in range(len(cars)):
		print("car %d coords\nC:" % i)
		c = coords[16*i:16*(i+1)]
		print("front=%s\nright=%s\nback=%s\nleft=%s" % (c[:4], c[4:8], c[8:12], c[12:]))
		_car = car.Car()
		_car.x = cars[i][0]
		_car.y = cars[i][1]
		_car.rot = cars[i][2]
		c = _car.linecoords
		print("python:\nfront=%s\nright=%s\nback=%s\nleft=%s" % (c[:4], c[4:8], c[8:12], c[12:]))

def linecoordsbench():
	c = 5000
	n = 100
	times = []
	times2 = []
	for i in range(n):
		cars = ((5,5,5) for i in range(c))
		t1 = time.time()
		coords = cmodule.car_lines(cars, c)
		t2 = time.time()
		t = 1000 * (t2-t1)
		times.append(t)
		cars = ((5,5,5) for i in range(c))
		t1 = time.time()
		coords = cmodule.car_lines2(cars, c)
		t2 = time.time()
		t = 1000 * (t2-t1)
		times2.append(t)
	avg = sum(times) / len(times)
	mn = min(times)
	mx = max(times)
	avg2 = sum(times2) / len(times2)
	mn2 = min(times2)
	mx2 = max(times2)
	print("average car_line per call: %.3fms (%.3fms to %.3fms)" % (avg, mn, mx))
	print("average car_line2 per call: %.3fms (%.3fms to %.3fms)" % (avg2, mn2, mx2))

#linecoords()

def cfloat():
	size = 6
	arr = (ctypes.c_float*size)(*[2+i for i in range(size)])
	print("arr addr: 0x%x" % id(arr))
	for i in range(size):
		print("%d: 0x%x = %.2f" % (i, id(arr[i]), arr[i]))
	#print(arr[0], hex(id(arr[0])))
	values = cmodule.get_float_array(size, id(arr))
	#print(arr[0], hex(id(arr)))
	#print(type(values))
	#print(values)

cfloat()

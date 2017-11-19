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

collision()

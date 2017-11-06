import time
import math
import numpy as np
det = np.linalg.det			# will be replaced by custom C module later

def intersection_point(line1, line2, integer=False):
	x1, x2, x3, x4 = line1.start.x, line1.end.x, line2.start.x, line2.end.x
	y1, y2, y3, y4 = line1.start.y, line1.end.y, line2.start.y, line2.end.y
	denom = (x1 - x2)*(y3 - y4) - (y1 - y2)*(x3 - x4)
	if denom == 0:
		return None
	x = ((x1*y2 - y1*x2)*(x3 - x4) - (x1 - x2)*(x3*y4 - y3*x4)) / denom
	y = ((x1*y2 - y1*x2)*(y3 - y4) - (y1 - y2)*(x3*y4 - y3*x4)) / denom
	if integer:
		x = int(x)
		y = int(y)
	#if min(x1,x2,x3,x4) <= x <= max(x1,x2,x3,x4) and min(y1,y2,y3,y4) <= y <= max(y1,y2,y3,y4):
	return (x,y)
	return None

def lines_intersect(line1, line2, integer=False):
	for l1, l2 in [(line1, line2), (line2, line1)]:
		x1, x2, x3, x4 = l1.start.x, l1.end.x, l2.start.x, l2.end.x
		y1, y2, y3, y4 = l1.start.y, l1.end.y, l2.start.y, l2.end.y
		a = y2 - y1
		b = x1 - x2
		c = x2*y1 - x1*y2
		d1 = a*x3 + b*y3 + c
		d2 = a*x4 + b*y4 + c
		#print("\rd1 = %.2f, d2 = %.2f" % (d1, d2), end="")
		if (d1 > 0 and d2 > 0) or (d1 < 0 and d2 < 0):
			return False
	return True # collinear or intersect

def line_intersection(line1, line2, integer=False):
	#return intersection_point(line1, line2)
	if lines_intersect(line1, line2):
		return intersection_point(line1, line2)
		pass
	return None

		# not working properly
	x1, x2, x3, x4 = line1.start.x, line1.end.x, line2.start.x, line2.end.x
	y1, y2, y3, y4 = line1.start.y, line1.end.y, line2.start.y, line2.end.y

	tx = x2 - x1
	ty = y2 - y1

	a = y2 - y1
	b = - (x2 - x1)
	a = -ty
	b = tx
	c = a * x1 - b * y1
	c = -a * x1 - b * y1

	#a = y2 - y1
	#b = x1 - x2
	#c = x2*y1 - x1*y2
	d1 = a*x3 + b*y3 + c
	d2 = a*x4 + b*y4 + c
	print("\rd1 = %.2f, d2 = %.2f" % (d1, d2), end="")

	d1 = a * x3 + b * y3 + c
	d2 = a * x4 + b * y4 + c

	if (d1 > 0 and d2 > 0) or (d1 < 0 and d2 < 0):
		return False

	if (d1 or d2):
		r = d1 / (d1 + d2)
		x = x3 + r * (x4 - x3)
		y = y3 + r * (y4 - y3)
		#print("\rx = %.2f, y = %.2f" % (x,y), end="")
		return (x,y)
	else:
		return None # collinear, of no use

def same_direction(angle1, angle2):
	mx = max(angle1, angle2)
	mn = min(angle1, angle2)
	return mx - mn < math.pi / 2 or (2 * math.pi - mx) + mn < math.pi / 2
		






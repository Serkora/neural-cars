import time
import math
import numpy as np
from cext import cfuncs

def line_intersection(line1, line2):
	#return cfuncs.intersection(line1, line2)
	x1, y1, x2, y2 = line1
	x3, y3, x4, y4 = line2

	dx1 = x1 - x2
	dx2 = x3 - x4
	dy1 = y1 - y2
	dy2 = y3 - y4

	# common denomiator in determinant calculation
	denom = dx1*dy2 - dy1*dx2
	if denom == 0:
		return

	# check that segments intersect rather than infinite lines
	# i.e. ends of one line are located on different sides of
	# the other line.
	# check if line1 intersects infinite line2
	b = (x3*y4 - y3*x4)
	d1b = dy2 * x1 - dx2*y1 + b
	d2b = dy2 * x2 - dx2*y2 + b
	if d1b * d2b > 0:
		return

	# check if line2 intersects infinite line1
	a = (x1*y2 - y1*x2)
	d1a = dy1 * x3 - dx1*y3 + a
	d2a = dy1 * x4 - dx1*y4 + a
	if d1a * d2a > 0:
		return

	# calculate the determinant itself to find the intersection point
	x = (a * dx2 - dx1 * b) / denom
	y = (a * dy2 - dy1 * b) / denom
	return (x,y)

def same_direction(angle1, angle2):
	mx = max(angle1, angle2)
	mn = min(angle1, angle2)
	return mx - mn < math.pi / 2 or (2 * math.pi - mx) + mn < math.pi / 2

def left_of(angle1, angle2):
	#print("angle1 = %.1f, angle2 = %.1f, pi = %.2f" % (angle1, angle2, math.pi))
	return -math.pi < (angle1 - angle2) < 0 or math.pi < (angle1 - angle2) < math.pi * 2

def right_of(angle1, angle2):
	return not left_of(angle1, angle2)


#include "common.h"

void print_array(double *array, int size) {
	if (size > 0) {
		printf("%.2f", array[0]);
	}
	int i;
	for (i=1; i<size; i++) {
		printf(", %.2f", array[i]);
	}
}

bool segment_intersection(double *segment1, double *segment2, /* out */ double *point) {
	double x1, y1, x2, y2, x3, y3, x4, y4;	// input lines
	double x, y;							// intersection point
	double dx1, dx2, dy1, dy2, a, b, denom;	// calculation variables
	double d1a, d1b, d2a, d2b;				// segment intersection checks

	x1 = segment1[0];
	y1 = segment1[1];
	x2 = segment1[2];
	y2 = segment1[3];
	x3 = segment2[0];
	y3 = segment2[1];
	x4 = segment2[2];
	y4 = segment2[3];

	dx1 = x1 - x2;
	dx2 = x3 - x4;
	dy1 = y1 - y2;
	dy2 = y3 - y4;

	// common denomiator in determinant calculation
	denom = dx1*dy2 - dy1*dx2;
	if (!denom) {
		return false;
	}

	// check that segments intersect rather than infinite lines
	// i.e. ends of one line are located on different sides of
	// the other line.
	// check if line1 intersects infinite line2
	b = (x3*y4 - y3*x4);
	d1a = dy2 * x1 - dx2*y1 + b;
	d1b = dy2 * x2 - dx2*y2 + b;
	if (d1a * d1b > 0) {
		return false;
	}

	// check if line2 intersects infinite line1
	a = (x1*y2 - y1*x2);
	d2a = dy1 * x3 - dx1*y3 + a;
	d2b = dy1 * x4 - dx1*y4 + a;
	if (d2a * d2b > 0) {
		return false;
	}

	if (point) {
		// calculate the determinant itself to find the intersection point
		x = (a * dx2 - dx1 * b) / denom;
		y = (a * dy2 - dy1 * b) / denom;

		point[0] = x;
		point[1] = y;
	}

	return true;
}

bool segment_line_intersection(double *segment, double *line) {
	double x1, y1, x2, y2, x3, y3, x4, y4;	// input lines
	double dx1, dx2, dy1, dy2, b, denom;	// calculation variables
	double d1a, d1b;						// segment intersection checks

	x1 = segment[0];
	y1 = segment[1];
	x2 = segment[2];
	y2 = segment[3];
	x3 = line[0];
	y3 = line[1];
	x4 = line[2];
	y4 = line[3];

	dx1 = x1 - x2;
	dx2 = x3 - x4;
	dy1 = y1 - y2;
	dy2 = y3 - y4;

	// common denomiator in determinant calculation
	denom = dx1*dy2 - dy1*dx2;
	if (!denom) {
		return false;
	}

	b = (x3*y4 - y3*x4);
	d1a = dy2 * x1 - dx2*y1 + b;
	d1b = dy2 * x2 - dx2*y2 + b;
	if (d1a * d1b > 0) {
		return false;
	}

	return true;
}

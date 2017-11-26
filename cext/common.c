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

inline bool _intersection(const double *line1, const double *line2, double *point, char type) {
	double x1, y1, x2, y2, x3, y3, x4, y4;	// input lines
	double x, y;							// intersection point
	double dx1, dx2, dy1, dy2, a, b, denom;	// calculation variables
	double d1a, d1b, d2a, d2b;				// line intersection checks

	x1 = line1[0];
	y1 = line1[1];
	x2 = line1[2];
	y2 = line1[3];
	x3 = line2[0];
	y3 = line2[1];
	x4 = line2[2];
	y4 = line2[3];

	dx1 = x1 - x2;
	dx2 = x3 - x4;
	dy1 = y1 - y2;
	dy2 = y3 - y4;

	// common denomiator in determinant calculation
	denom = dx1*dy2 - dy1*dx2;
	if (!denom) {
		return false;
	}

	a = (x3*y4 - y3*x4);
	if (type < 2) {
		// check that segments intersect rather than infinite lines
		// i.e. ends of one line are located on different sides of
		// the other line.
		// check if line1 intersects infinite line2
		d1a = dy2 * x1 - dx2*y1 + a;
		d1b = dy2 * x2 - dx2*y2 + a;
		if (d1a * d1b > 0) {
			return false;
		}
	}

	b = (x1*y2 - y1*x2);
	if (type < 1) {
		// check if line2 intersects infinite line1
		d2a = dy1 * x3 - dx1*y3 + b;
		d2b = dy1 * x4 - dx1*y4 + b;
		if (d2a * d2b > 0) {
			return false;
		}
	}

	if (point) {
		// calculate the determinant itself to find the intersection point
		x = (b * dx2 - dx1 * a) / denom;
		y = (b * dy2 - dy1 * a) / denom;

		point[0] = x;
		point[1] = y;
	}

	return true;
}

bool intersection(const double *line1, const double *line2, double *point, char type) {
	return _intersection(line1, line2, point, type);
}

bool segment_intersection(const double *segment1, const double *segment2, double *point) {
	return _intersection(segment1, segment2, point, SEGMENT_SEGMENT);
}

bool segment_line_intersection(const double *segment, const double *line, double *point) {
	return _intersection(segment, line, point, SEGMENT_LINE);
}

bool line_intersection(const double *line1, const double *line2, double *point) {
	return _intersection(line1, line2, point, LINE_LINE);
}

bool segments_intersect(const double *segment1, const double *segment2) {
	return _intersection(segment1, segment2, NULL, SEGMENT_SEGMENT);
}

bool segment_line_intersect(const double *segment, const double *line) {
	return _intersection(segment, line, NULL, SEGMENT_LINE);
}

bool lines_intersect(const double *line1, const double *line2) {
	return _intersection(line1, line2, NULL, LINE_LINE);
}

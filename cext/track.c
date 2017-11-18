#include "track.h"

//static void print_array(double *array, int size) {
//	if (size > 0) {
//		printf("%.2f", array[0]);
//	}
//	int i;
//	for (i=1; i<size; i++) {
//		printf(", %.2f", array[i]);
//	}
//}

struct Track track = {0, 0};

bool line_intersection(double *line1, double *line2, /* out */ double *point) {
	double x1, y1, x2, y2, x3, y3, x4, y4;	// input lines
	double x, y;							// intersection point
	double dx1, dx2, dy1, dy2, a, b, denom;	// calculation variables
	double d1a, d1b, d2a, d2b;				// segment intersection checks

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

bool find_section_intersection(double *line, int idx, double *point) {
	int prev = 0;
	while (true) {
		if (idx < 0) {
			idx += track.length;
		}
		if (idx >= track.length) {
			idx %= track.length;
		}
		if (line_intersection(line, track.sections[idx].left, point)) {
			return true;
		} else if (line_intersection(line, track.sections[idx].right, point)) {
			return true;
		}

		if (prev != 1 && line_intersection(line, track.sections[idx].front, 0)) {
			prev = 2;
			idx++;
		} else if (prev != 2 && line_intersection(line, track.sections[idx].back, 0)) {
			prev = 1;
			idx--;
		} else {
			break;
		}
	}
	return false;
}

inline void set_line(PyObject *pytuple, double line[4]) {
	int i=0;
	for (i=0; i<4; i++) {
		line[i] = PyFloat_AsDouble(PySequence_GetItem(pytuple, i));
	}
}

void set_section(PyObject *section, int idx) {
	set_line(PySequence_GetItem(section, 0), track.sections[idx].front);
	set_line(PySequence_GetItem(section, 1), track.sections[idx].back);
	set_line(PySequence_GetItem(section, 2), track.sections[idx].left);
	set_line(PySequence_GetItem(section, 3), track.sections[idx].right);
	set_line(PySequence_GetItem(section, 4), track.sections[idx].line);
	track.sections[idx].angle = PyFloat_AsDouble(PySequence_GetItem(section, 5));
	//printf("section %d. Front: ", idx);
	//print_array(track.sections[idx].front, 4);
	//printf("\n");
}

PyObject* store_track(PyObject *self, PyObject *args) {
	PyObject *sections;
	if (!PyArg_ParseTuple(args, "O", &sections)) {
		return NULL;
	}

	if (track.sections) {
		free(track.sections);
		track.sections = 0;
	}
	
	track.length = PySequence_Length(sections);
	//printf("num of sections: %zd.\n", track.length);
	//printf("size of TrackSection: %zu\n", SECTION_SIZE);
	track.sections = malloc(track.length * SECTION_SIZE);
	//printf("allocated memory\n");
	int i;
	for (i=0; i<track.length; i++) {
		PyObject *section = PySequence_GetItem(sections, i);
		set_section(section, i);
		Py_DECREF(section);
	}
	
	Py_RETURN_NONE;
}

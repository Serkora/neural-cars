#include <Python.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

typedef int bool;
#define false 0
#define true 1

struct TrackSection {
	double front[4];
	double back[4];
	double left[4];
	double right[4];
	double line[4];
	double angle;
};

struct Track {
	int length;
	struct TrackSection *sections;
};

size_t SECTION_SIZE = sizeof(struct TrackSection);
struct Track track = {0, 0};

static void print_array(double *array, int size) {
	if (size > 0) {
		printf("%.2f", array[0]);
	}
	int i;
	for (i=1; i<size; i++) {
		printf(", %.2f", array[i]);
	}
}

static bool line_intersection(double line1[4], double line2[4], /* out */ double point[2]) {
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

static bool find_section_intersection(double line[4], int idx, double point[2]) {
	int prev = 0;
	while (true) {
		if (idx < 0 || idx > track.length) {
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

static PyObject* intersection(PyObject *self, PyObject *args) {
	double line1[4];
	double line2[4];
	double point[2];
	PyObject *l1;
	PyObject *l2;

	//if (!PyArg_ParseTuple(args, "(dddd)(dddd)", &x1, &y1, &x2, &y2, &x3, &y3, &x4, &y4)) {
	//	return NULL;
	//}
	//printf("here0?");
	if (!PyArg_ParseTuple(args, "OO", &l1, &l2)) {
	//if (!PyArg_ParseTuple(args, "(dddd)(dddd)", &line1[0], &line1[1], &line1[2], &line1[3], &line2[0], &line2[1], &line2[2], &line2[3])) {
		return NULL;
	}

	int i;
	for (i=0; i<4; i++){
		line1[i] = PyFloat_AsDouble(PySequence_GetItem(l1, i));
		line2[i] = PyFloat_AsDouble(PySequence_GetItem(l2, i));
	}

	if (line_intersection(line1, line2, point)) {
		return Py_BuildValue("(dd)", point[0], point[1]);
	} else {
		Py_RETURN_NONE;
	}
}

inline static void set_line(PyObject *pytuple, double line[4]) {
	int i=0;
	for (i=0; i<4; i++) {
		line[i] = PyFloat_AsDouble(PySequence_GetItem(pytuple, i));
	}
}

static void set_section(PyObject *section, int idx) {
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

static PyObject *store_track(PyObject *self, PyObject *args) {
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

static PyObject *test(PyObject *self, PyObject *args) {
	double point[2];		// intersection
	int reps;

	if (!PyArg_ParseTuple(args, "i", &reps)) {
		return NULL;
	}
	int i, j;
	int count = 0;
	int intersections = 0;
	for (j=0; j<reps; j++) {
		double line[4] = {0 * i, 0, 30, 250};
		for (i=0; i<track.length; i++) {
			if (line_intersection(line, track.sections[i].front, point)) {
				intersections++;
			}
			if (line_intersection(line, track.sections[i].back, point)) {
				intersections++;
			}
			if (line_intersection(line, track.sections[i].left, point)) {
				intersections++;
			}
			if (line_intersection(line, track.sections[i].right, point)) {
				intersections++;
			}
			count += 4;
		}
	}

	printf("%d checks, %d intersections found.\n", count, intersections);

	return Py_BuildValue("(ii)", count, intersections);
}

static PyObject *test2(PyObject *self, PyObject *args) {
	double line[4];
	int idx;
	double point[2];		// intersection

	if (!PyArg_ParseTuple(args, "(dddd)i", &line[0], &line[1], &line[2], &line[3], &idx)) {
		return NULL;
	}

	if (find_section_intersection(line, idx, point)) {
		return Py_BuildValue("(dd)", point[0], point[1]);
	} else {
		Py_RETURN_NONE;
	}
}

/*  define functions in module */
static PyMethodDef ctrack_funcs[] =
{
     {"intersection", intersection, METH_VARARGS, "find intersection between two lines"},
     {"store_track", store_track, METH_VARARGS, "find intersection between two lines"},
     {"test", test, METH_VARARGS, "find intersection between two lines"},
     {"test2", test2, METH_VARARGS, "find intersection between two lines"},
     {NULL, NULL, 0, NULL}
};


/* module initialization */
// PyMODINIT_FUNC

static struct PyModuleDef ctrack =
{
    PyModuleDef_HEAD_INIT,
    "ctrack",	 /* name of module */
    "",          /* module documentation, may be NULL */
    -1,          /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    ctrack_funcs
};

PyMODINIT_FUNC PyInit_ctrack(void)
{
    return PyModule_Create(&ctrack);
}

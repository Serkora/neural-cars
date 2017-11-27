#ifndef TRACK
#define TRACK

#include "common.h"

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

// for use by others
bool find_section_intersection(double *line, int idx, double *point);
int out_of_section(double *pos, int idx);

// dumping data from python to C heap
PyObject* store_track(PyObject *self, PyObject *args);
void set_section(PyObject *section, int idx);

#endif

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

static size_t SECTION_SIZE = sizeof(struct TrackSection);

bool line_intersection(double *line1, double *line2, double *point);
bool find_section_intersection(double *line, int idx, double *point);
inline void set_line(PyObject *pytuple, double *line);
void set_section(PyObject *section, int idx);
PyObject* store_track(PyObject *self, PyObject *args);

#endif

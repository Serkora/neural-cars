#include "track.h"

static const size_t SECTION_SIZE = sizeof(struct TrackSection);


struct Track track = {0, 0};

bool find_section_intersection(double *line, int idx, double *point) {
	int prev = 0;
	while (true) {
		if (idx < 0) {
			idx += track.length;
		}
		if (idx >= track.length) {
			idx %= track.length;
		}
		if (segment_intersection(line, track.sections[idx].left, point)) {
			return true;
		} else if (segment_intersection(line, track.sections[idx].right, point)) {
			return true;
		}

		if (prev != 1 && segments_intersect(line, track.sections[idx].front)) {
			prev = 2;
			idx++;
		} else if (prev != 2 && segments_intersect(line, track.sections[idx].back)) {
			prev = 1;
			idx--;
		} else {
			break;
		}
	}
	return false;
}

int out_of_section(double *pos, int idx) {
	/*
	extends the side line of a section and checks if car-point
	segment intersects the front/back edges of the section.
	If it doesn't, the car must be outside.
	 */
	struct TrackSection *s = &(track.sections[idx]);
	double next_line[4] = {pos[0], pos[1], 
		s->left[2] + (s->left[2] - s->left[0]),
		s->left[3] + (s->left[3] - s->left[1])};
	double prev_line[4] = {pos[0], pos[1],
		s->left[0] - (s->left[2] - s->left[0]),
		s->left[1] - (s->left[3] - s->left[1])};
	if (!segment_line_intersect(next_line, s->front)) {
		return 1;
	} else if (!segment_line_intersect(prev_line, s->back)) {
		return -1;
	}
	return 0;
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
	track.sections = malloc(track.length * SECTION_SIZE);
	int i;
	for (i=0; i<track.length; i++) {
		PyObject *section = PySequence_GetItem(sections, i);
		set_section(section, i);
		Py_DECREF(section);
	}
	
	Py_RETURN_NONE;
}

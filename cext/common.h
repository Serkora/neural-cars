#ifndef COMMON
#define COMMON

#include <Python.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define PARSE(args, format, ...) \
	if (!PyArg_ParseTuple(args, format, __VA_ARGS__)) { \
		return NULL; \
	};

typedef int bool;
#define false 0
#define true 1

static inline double point_distance(const double *p1, const double *p2) {
	return sqrt((p1[1] - p2[1])*(p1[1] - p2[1]) + (p1[0] - p2[0])*(p1[0] - p2[0]));
}

static inline double point_distance_origin(const double *p) {
	return sqrt(p[1] * p[1] + p[0] * p[0]);
}

void print_array(double *array, int size);

static const char SEGMENT_SEGMENT = 0;
static const char SEGMENT_LINE = 1;
static const char LINE_LINE = 2;

bool intersection(const double *line1, const double *line2, double *point, char type);
bool segment_intersection(const double *segment1, const double *segment2, double *point);
bool segment_line_intersection(const double *segment, const double *line, double *point);
bool line_intersection(const double *line1, const double *line2, double *point);

bool segments_intersect(const double *segment1, const double *segment2);
bool segment_line_intersect(const double *segment, const double *line);
bool lines_intersect(const double *line1, const double *line2);
#endif

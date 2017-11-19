#ifndef COMMON
#define COMMON

#include <Python.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

typedef int bool;
#define false 0
#define true 1

inline double point_distance(const double *p1, const double *p2) {
	return sqrt((p1[1] - p2[1])*(p1[1] - p2[1]) + (p1[0] - p2[0])*(p1[0] - p2[0]));
}

void print_array(double *array, int size);

bool segment_intersection(double *segment1, double *segment2, double *point);
bool segment_line_intersection(double *segment, double *line);
#endif

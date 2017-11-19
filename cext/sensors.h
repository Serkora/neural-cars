#ifndef SENSORS
#define SENSORS

#include "common.h"

struct Sensor {
	double angle;
	double distance;
};

struct SensorRig {
	int size;
	struct Sensor *sensors;
};

static size_t SENSOR_SIZE = sizeof(struct Sensor);
static size_t SENSOR_RIG_SIZE = sizeof(struct SensorRig);

PyObject* store_sensors(PyObject *self, PyObject *args);
PyObject* delete_sensors(PyObject *self, PyObject *args);
void print_rig(struct SensorRig *rig);

inline void get_endpoint(struct Sensor *sensor, const double *pos, double rot, double *point) {
	point[0] = pos[0] + sensor->distance * sin(rot + sensor->angle);
	point[1] = pos[1] + sensor->distance * cos(rot + sensor->angle);
}

#endif

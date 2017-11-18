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
void get_endpoint(struct Sensor *sensor, const double *pos, double rot, double *point);
void print_rig(struct SensorRig *rig);

#endif

#include "sensors.h"

static const size_t SENSOR_SIZE = sizeof(struct Sensor);
static const size_t SENSOR_RIG_SIZE = sizeof(struct SensorRig);

void print_rig(struct SensorRig *rig) {
	int i;
	for (i=0; i<rig->size; i++) {
		printf("s %d: angle: %.2f, dist: %2.f\n", 
			i, rig->sensors[i].angle, rig->sensors[i].distance);
	}
}

PyObject* store_sensors(PyObject *self, PyObject *args) {
	PyObject *angles;
	PyObject *distances;

	if (!PyArg_ParseTuple(args, "OO", &angles, &distances)) {
		return NULL;
	}

	struct SensorRig *rig = malloc(SENSOR_RIG_SIZE);
	rig->size = PySequence_Length(angles);
	rig->sensors = malloc(SENSOR_SIZE * rig->size);
	int i;
	for (i=0; i<rig->size; i++) {
		rig->sensors[i].angle = PyFloat_AsDouble(PySequence_GetItem(angles, i));
		rig->sensors[i].distance = PyFloat_AsDouble(PySequence_GetItem(distances, i));
	}
	
	return Py_BuildValue("k", rig);
}

PyObject* delete_sensors(PyObject *self, PyObject *args) {
	struct SensorRig *rig;

	if (!PyArg_ParseTuple(args, "k", &rig)) {
		return NULL;
	}

	/*
	print_rig(rig);
	double point[2] = {0, 0};
	double pos[2] = {0, 0};
	int i;
	for (i=0; i<rig->size; i++) {
		get_endpoint(&(rig->sensors[i]), pos, 0, point);
		printf("sens %d. a: %.2f, d: %.2f, endpoint: (%.2f, %.2f)\n",
			i, rig->sensors[i].angle, rig->sensors[i].distance,
			point[0], point[1]);
	}
	*/

	free(rig);
	Py_RETURN_NONE;
}

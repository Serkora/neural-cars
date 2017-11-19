#include "common.h"
#include "track.h"
#include "sensors.h"

//struct Track track = {0, 0};
//struct SensorRigs rigs = {0, 0};

const double CAR_LENGTH = 30;
const double CAR_WIDTH = 10;
const double ORIGIN[2] = {0,0};
const double CORNER[2] = {CAR_WIDTH/2, CAR_LENGTH/2};
//const double CORNER_ANGLE = tan(CAR_WIDTH/CAR_LENGTH);
//const double CORNER_DISTANCE = point_distance(origin, corner);

static PyObject* intersection(PyObject *self, PyObject *args) {
	double segment1[4];
	double segment2[4];
	double point[2];
	PyObject *l1;
	PyObject *l2;

	if (!PyArg_ParseTuple(args, "OO", &l1, &l2)) {
		return NULL;
	}

	int i;
	for (i=0; i<4; i++){
		segment1[i] = PyFloat_AsDouble(PySequence_GetItem(l1, i));
		segment2[i] = PyFloat_AsDouble(PySequence_GetItem(l2, i));
	}

	if (segment_intersection(segment1, segment2, point)) {
		return Py_BuildValue("(dd)", point[0], point[1]);
	} else {
		Py_RETURN_NONE;
	}
}

PyObject* find_rig_distances(struct SensorRig *rig, double *pos, double rot, int idx) {
	PyObject *intersections = PyTuple_New(rig->size);
	int i;
	double point[2];
	double distance = 0;

	for (i=0; i<rig->size; i++) {
		get_endpoint(&(rig->sensors[i]), pos, rot, point);
		double line[4] = {pos[0], pos[1], point[0], point[1]};
		if (find_section_intersection(line, idx, point)) {
			distance = point_distance(pos, point);
		} else {
			distance = rig->sensors[i].distance;
		}
		PyTuple_SET_ITEM(intersections, i, Py_BuildValue("d", distance));
	}
	
	return intersections;
}

PyObject* find_track_intersection(PyObject *self, PyObject *args) {
	struct SensorRig *rig;
	double pos[2];
	double rot;
	int section_idx;
	// struct Track *track
	
	if (!PyArg_ParseTuple(args, "k(dd)dI", &rig, &pos[0], &pos[1], &rot, &section_idx)) {
		return NULL;
	}

	return find_rig_distances(rig, pos, rot, section_idx);
}

PyObject* check_collision(PyObject *self, PyObject *args) {
	double corners[8];
	int section_idx;
	PyObject *c;
	
	if (!PyArg_ParseTuple(args, "OI", &c, &section_idx)) {
		return NULL;
	}

	int i;
	for (i=0; i<8; i++) {
		corners[i] = PyFloat_AsDouble(PySequence_GetItem(c, i));
	}

	double box[4][4] = {
		{corners[0], corners[1], corners[2], corners[3]},
		{corners[2], corners[3], corners[4], corners[5]},
		{corners[4], corners[5], corners[6], corners[7]},
		{corners[6], corners[7], corners[0], corners[1]},
	};

	for (i=0; i<4; i++) {
		if (find_section_intersection(box[i], section_idx, 0)) {
			return Py_BuildValue("I", i+1);
		}
	}

	return Py_BuildValue("I", 0);
}

PyObject* check_collision_pos(PyObject *self, PyObject *args) {
	double pos[2];
	double rot;
	int section_idx;
	
	if (!PyArg_ParseTuple(args, "(dd)dI", &pos[0], &pos[1], &rot, &section_idx)) {
		return NULL;
	}

	double distance = point_distance(ORIGIN, CORNER);
	double angle = tan(CAR_WIDTH / CAR_LENGTH);
	double sin_left = distance * sin(rot - angle);
	double sin_right = distance * sin(rot + angle);
	double cos_left = distance * cos(rot - angle);
	double cos_right = distance * cos(rot + angle);

	double box[4][4] = {
		{pos[0] + sin_left, pos[1] + cos_left, pos[0] + sin_right, pos[1] + cos_right},
		{pos[0] + sin_right, pos[1] + cos_right, pos[0] - sin_right, pos[1] - cos_right},
		{pos[0] - sin_right, pos[1] - cos_right, pos[0] - sin_left, pos[1] - cos_left},
		{pos[0] - sin_left, pos[1] - cos_left, pos[0] + sin_left, pos[1] + cos_left}
	};

	int i;
	for (i=0; i<4; i++) {
		if (find_section_intersection(box[i], section_idx, 0)) {
			return Py_BuildValue("I", i+1);
		}
	}

	return Py_BuildValue("I", 0);
}

PyObject* changed_section(PyObject* self, PyObject *args) {
	double pos[2];
	int section_idx;
	
	if (!PyArg_ParseTuple(args, "(dd)I", &pos[0], &pos[1], &section_idx)) {
		return NULL;
	}

	int change = out_of_section(pos, section_idx);

	return Py_BuildValue("i", change);
}

/*  define functions in module */
static PyMethodDef cmodule_funcs[] =
{
	{"intersection", intersection, METH_VARARGS, "find intersection between two lines"},
	{"store_track", store_track, METH_VARARGS, "store track section info"},
	{"store_sensors", store_sensors, METH_VARARGS, "store one car sensor info"},
	{"delete_sensors", delete_sensors, METH_VARARGS, "delete sensor info from memory"},
	{"find_track_intersection", find_track_intersection, METH_VARARGS, "find first intersection"},
	{"check_collision", check_collision, METH_VARARGS, "check car collisions"},
	{"check_collision_pos", check_collision_pos, METH_VARARGS, "check car collisions"},
	{"changed_section", changed_section, METH_VARARGS, "check if need to set next section"},
	{NULL, NULL, 0, NULL}
};


/* module initialization */
// PyMODINIT_FUNC

static struct PyModuleDef cmodule =
{
    PyModuleDef_HEAD_INIT,
    "cmodule",	 /* name of module */
    "",          /* module documentation, may be NULL */
    -1,          /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    cmodule_funcs
};

PyMODINIT_FUNC PyInit_cmodule(void)
{
    return PyModule_Create(&cmodule);
}

#include "common.h"
#include "track.h"
#include "sensors.h"

//struct Track track = {0, 0};
//struct SensorRigs rigs = {0, 0};

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

PyObject* find_track_intersection(PyObject *self, PyObject *args) {
	struct SensorRig *rig;
	double pos[2];
	double rot;
	int section_idx;
	// struct Track *track
	
	if (!PyArg_ParseTuple(args, "k(dd)dI", &rig, &pos[0], &pos[1], &rot, &section_idx)) {
		return NULL;
	}

	PyObject *intersections = PyTuple_New(rig->size);

	int i;
	double point[2];
	double distance = 0;
	for (i=0; i<rig->size; i++) {
		get_endpoint(&(rig->sensors[i]), pos, rot, point);
		double line[4] = {pos[0], pos[1], point[0], point[1]};
		//printf("endpoint = (%.2f, %.2f)\n", point[0], point[1]);
		find_section_intersection(line, section_idx, point);
		//printf("intersection point = (%.2f, %.2f)\n", point[0], point[1]);
		distance = sqrt((point[0]-pos[0])*(point[0]-pos[0]) + (point[1]-pos[1])*(point[1]-pos[1]));
		//PyTuple_SET_ITEM(intersections, i, Py_BuildValue("(dd)d", point[0], point[1], distance));
		//PyTuple_SET_ITEM(intersections, i, Py_BuildValue("(dd)", point[0], point[1]));
		PyTuple_SET_ITEM(intersections, i, Py_BuildValue("d", distance));
	}
	
	return intersections;
	//Py_RETURN_NONE;
}

/*  define functions in module */
static PyMethodDef cmodule_funcs[] =
{
	{"intersection", intersection, METH_VARARGS, "find intersection between two lines"},
	{"store_track", store_track, METH_VARARGS, "store track section info"},
	{"store_sensors", store_sensors, METH_VARARGS, "store one car sensor info"},
	{"delete_sensors", delete_sensors, METH_VARARGS, "delete sensor info from memory"},
	{"find_track_intersection", find_track_intersection, METH_VARARGS, "find first intersection"},
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

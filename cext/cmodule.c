#include "common.h"
#include "track.h"
#include "sensors.h"

#define PARSE(args, format, ...) \
	if (!PyArg_ParseTuple(args, format, __VA_ARGS__)) { \
		return NULL; \
	};

const double CAR_LENGTH = 30;
const double CAR_WIDTH = 10;
const double ORIGIN[2] = {0,0};
const double H_WHEELBASE = CAR_LENGTH / 2;
const double H_TRACK = CAR_WIDTH / 2;
/* the below three will be changed later */
double CORNER[2] = {0, 0};
double CORNER_ANGLE = 0;
double CORNER_DISTANCE = 0;	
//const double CORNER_ANGLE = tan(CAR_WIDTH/CAR_LENGTH);
//const double CORNER_DISTANCE = point_distance(origin, corner);

static PyObject* py_intersection(PyObject *self, PyObject *args) {
	double line1[4];
	double line2[4];
	double point[2];
	PyObject *l1;
	PyObject *l2;
	bool needPoint;
	char type;

	PARSE(args, "OOpb", &l1, &l2, &needPoint, &type);

	int i;
	for (i=0; i<4; i++){
		line1[i] = PyFloat_AsDouble(PySequence_GetItem(l1, i));
		line2[i] = PyFloat_AsDouble(PySequence_GetItem(l2, i));
	}

	if (intersection(line1, line2, point, type)) {
		if (needPoint) {
			return Py_BuildValue("(dd)", point[0], point[1]);
		} else {
			return Py_BuildValue("b", true);
		}
	} else {
		Py_RETURN_NONE;
	}
}

PyObject* find_rig_distances(PyObject *self, PyObject *args) {
	struct SensorRig *rig;
	double pos[2];
	double rot;
	int section_idx;
	// struct Track *track
	
	PARSE(args, "k(dd)dI", &rig, &pos[0], &pos[1], &rot, &section_idx);

	PyObject *intersections = PyTuple_New(rig->size);
	int i;
	double point[2];
	double distance = 0;

	for (i=0; i<rig->size; i++) {
		get_endpoint(&(rig->sensors[i]), pos, rot, point);
		double line[4] = {pos[0], pos[1], point[0], point[1]};
		if (find_section_intersection(line, section_idx, point)) {
			distance = point_distance(pos, point);
		} else {
			distance = rig->sensors[i].distance;
		}
		PyTuple_SET_ITEM(intersections, i, Py_BuildValue("d", distance));
	}
	
	return intersections;
}

PyObject* check_box_collision(PyObject *self, PyObject *args) {
	double corners[8];
	int section_idx;
	PyObject *c;
	
	PARSE(args, "OI", &c, &section_idx);

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

PyObject* check_car_collision(PyObject *self, PyObject *args) {
	double pos[2];
	double rot;
	int section_idx;
	
	PARSE(args, "(dd)dI", &pos[0], &pos[1], &rot, &section_idx);

	// should be static really
	double corner[2] = {CAR_WIDTH/2, CAR_LENGTH/2};
	double distance = point_distance(ORIGIN, corner);
	double angle = atan(CAR_WIDTH / CAR_LENGTH);
	
	double sin_m = distance * sin(rot - angle);
	double sin_p = distance * sin(rot + angle);
	double cos_m = distance * cos(rot - angle);
	double cos_p = distance * cos(rot + angle);

	double box[4][4] = {
		{pos[0] + sin_m, pos[1] + cos_m, pos[0] + sin_p, pos[1] + cos_p},
		{pos[0] + sin_p, pos[1] + cos_p, pos[0] - sin_m, pos[1] - cos_m},
		{pos[0] - sin_m, pos[1] - cos_m, pos[0] - sin_p, pos[1] - cos_p},
		{pos[0] - sin_p, pos[1] - cos_p, pos[0] + sin_m, pos[1] + cos_m}
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
	
	PARSE(args, "(dd)I", &pos[0], &pos[1], &section_idx);

	int change = out_of_section(pos, section_idx);

	return Py_BuildValue("i", change);
}

float *lines = 0;
PyObject *car_lines(PyObject *self, PyObject *args) {
	PyObject *cars;
	int carnum;

	PARSE(args, "OI", &cars, &carnum);

	if (CORNER_DISTANCE == 0) {
		CORNER[0] = CAR_WIDTH / 2;
		CORNER[1] = CAR_LENGTH / 2;
		CORNER_DISTANCE = point_distance(ORIGIN, CORNER);
		CORNER_ANGLE = atan(CAR_WIDTH / CAR_LENGTH);
	}

	if (!lines) {
		lines = malloc(sizeof(float) * carnum * 16);
	}

	int i = 0;
	int j;
	PyObject *car;
	float sin_m, sin_p, cos_m, cos_p;
	while ((car = PyIter_Next(cars))) {
		double x, y, rot;
		PyArg_ParseTuple(car, "ddd", &x, &y, &rot);

		sin_m = CORNER_DISTANCE * sin(rot - CORNER_ANGLE);
		sin_p = CORNER_DISTANCE * sin(rot + CORNER_ANGLE);
		cos_m = CORNER_DISTANCE * cos(rot - CORNER_ANGLE);
		cos_p = CORNER_DISTANCE * cos(rot + CORNER_ANGLE);

		double corners[4][2] = {
			{x + sin_m, y + cos_m}, // top left
			{x + sin_p, y + cos_p},	// top right
			{x - sin_m, y - cos_m},	// bottom right
			{x - sin_p, y - cos_p}	// bottom left
		};

		for (j=0; j<16; j++) {
			lines[i+j] = corners[((j+2)&0xf)>>2][j%2];
		}
		i += 16;

		Py_DECREF(car);
	}

	return Py_BuildValue("k", lines);
}

PyObject* move(PyObject *self, PyObject *args) {
	double pos[2];
	double rot;
	double steering;
	double speed;
	double dt;

	PARSE(args, "dddddd", &pos[0], &pos[1], &rot, &speed, &steering, &dt);

	if (!speed) {
		return Py_BuildValue("ddd", pos[0], pos[1], rot);
	}

	double d = speed * dt;
	if (!steering) {
		return Py_BuildValue("ddd", pos[0] + d * sin(rot), pos[1] + d * cos(rot), rot);
	}

	double steer_line[4] = {H_WHEELBASE * sin(rot), H_WHEELBASE * cos(rot),0,0};
	steer_line[2] = steer_line[0] + sin(rot + steering + M_PI/2);
	steer_line[3] = steer_line[1] + cos(rot + steering + M_PI/2);
	double back_line[4] = {
		 H_TRACK * cos(rot) - H_TRACK * sin(rot),
		-H_TRACK * sin(rot) - H_TRACK * cos(rot),
		0,0
	};
	back_line[2] = back_line[0] + sin(rot + M_PI/2);
	back_line[3] = back_line[1] + cos(rot + M_PI/2);
	double cor[2];
	if (!intersection(steer_line, back_line, cor, LINE_LINE)) {
		return Py_BuildValue("ddd", pos[0] + d * sin(rot), pos[1] + d * cos(rot), rot);
	}

	double radius = point_distance_origin(cor);
	double angle = d / radius;
	if (steering < 0) {
		angle = -angle;
	}
	pos[0] += cor[0] - cor[0] * cos(angle) - cor[1] * sin(angle);
	pos[1] += cor[1] + cor[0] * sin(angle) - cor[1] * cos(angle);
	rot += angle;

	return Py_BuildValue("ddd", pos[0], pos[1], rot);
}

/*  define functions in module */
static PyMethodDef cmodule_funcs[] =
{
		/* Utilities */
	{"intersection", py_intersection, METH_VARARGS, "find intersection between two lines"},
		/* One-time data transfers */
	{"store_track", store_track, METH_VARARGS, "store track section info"},
	{"store_sensors", store_sensors, METH_VARARGS, "store one car sensor info"},
	{"delete_sensors", delete_sensors, METH_VARARGS, "delete sensor info from memory"},
		/* for per-frame updates, physics and such */
	{"find_rig_distances", find_rig_distances, METH_VARARGS, "find first intersection"},
	{"check_car_collision", check_car_collision, METH_VARARGS, "find car collisions with the track"},
	{"check_box_collision", check_box_collision, METH_VARARGS, "find box collisions with the track"},
	{"changed_section", changed_section, METH_VARARGS, "check if need to set next section"},
	{"move", move, METH_VARARGS, "move the car based on the circle of rotation"},
		/* for graphics */
	{"car_lines", car_lines, METH_VARARGS, "Get a tuple of all car lines to draw in one call"},
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

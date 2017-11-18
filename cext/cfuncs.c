#include <Python.h>

static PyObject* intersection(PyObject *self, PyObject *args) {
	double x1, y1, x2, y2, x3, y3, x4, y4;	// input lines
	double x, y;							// intersection point
	double dx1, dx2, dy1, dy2, a, b, denom;	// calculation variables
	double d1a, d1b, d2a, d2b;				// segment intersection checks

	if (!PyArg_ParseTuple(args, "(dddd)(dddd)", &x1, &y1, &x2, &y2, &x3, &y3, &x4, &y4)) {
		return NULL;
	}

	dx1 = x1 - x2;
	dx2 = x3 - x4;
	dy1 = y1 - y2;
	dy2 = y3 - y4;

	// common denomiator in determinant calculation
	denom = dx1*dy2 - dy1*dx2;
	if (!denom) {
		Py_RETURN_NONE;
	}

	// check that segments intersect rather than infinite lines
	// i.e. ends of one line are located on different sides of
	// the other line.
	// check if line1 intersects infinite line2
	b = (x3*y4 - y3*x4);
	d1a = dy2 * x1 - dx2*y1 + b;
	d1b = dy2 * x2 - dx2*y2 + b;
	if (d1a * d1b > 0) {
		Py_RETURN_NONE;
	}

	// check if line2 intersects infinite line1
	a = (x1*y2 - y1*x2);
	d2a = dy1 * x3 - dx1*y3 + a;
	d2b = dy1 * x4 - dx1*y4 + a;
	if (d2a * d2b > 0) {
		Py_RETURN_NONE;
	}

	// calculate the determinant itself to find the intersection point
	x = (a * dx2 - dx1 * b) / denom;
	y = (a * dy2 - dy1 * b) / denom;

	return Py_BuildValue("(dd)", x, y);
}


/*  define functions in module */
static PyMethodDef cfuncs_funcs[] =
{
     {"intersection", intersection, METH_VARARGS, "find intersection between two lines"},
     {NULL, NULL, 0, NULL}
};


/* module initialization */
// PyMODINIT_FUNC

static struct PyModuleDef cfuncs =
{
    PyModuleDef_HEAD_INIT,
    "cfuncs",	 /* name of module */
    "",          /* module documentation, may be NULL */
    -1,          /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    cfuncs_funcs
};

PyMODINIT_FUNC PyInit_cfuncs(void)
{
    return PyModule_Create(&cfuncs);
}

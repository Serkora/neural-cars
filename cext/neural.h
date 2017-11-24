#include "common.h"

struct Layer {
	int inputs;
	int neurons;
	double **weights;
	double *biases;
};

struct Network {
	int inputs;
	int outputs;
	int layernum;
	struct Layer *layers;
};

const size_t NETSIZE = sizeof(struct Network);
const size_t LAYERSIZE = sizeof(struct Layer);

struct Network* create_network(int inputs, int outputs);
void delete_network(struct Network *network);
void add_layer(struct Network *network, int neurons);
void activate(struct Network *net, double *inputs, double *outputs);

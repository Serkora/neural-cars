#include "neural.h"

struct Network* create_network(int inputs, int outputs) {
	struct Network *net = malloc(NETSIZE);
	net->inputs = inputs;
	net->outputs = outputs;
	net->layernum = 0;
	net->layers = 0;

	return net;
}

void delete_network(struct Network *network) {
	int i=0;
	for (i=0; i<network->layernum; i++) {
		if (network->layers[i].weights) {
			free(network->layers[i].weights);
			free(network->layers[i].biases);
		}
	}
	free(network->layers);
	free(network);
}

void add_layer(struct Network *network, int neurons) {
	
}

void activate(struct Network *network, double *inputs, double *outputs) {
	if (!network || network->layernum == 0) {
		return;
	}
	int i;
	double *ins = inputs;
	for (i=0; i<network->layernum; i++) {
		double out[network->layers[i].neurons];
		activate_layer(&network->layers[i], ins, out);
		ins = out;
	}
	for (i=0; i<network->layers[network->layernum-1].neurons; i++) {
		outputs[i] = ins[i];
	}
}

void activate_layer(struct Layer *layer, double *inputs, double *outputs) {
}

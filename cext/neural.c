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

}


#include "common.h"
#include "neural.h"

static const size_t NETSIZE = sizeof(struct Network);
static const size_t LAYERSIZE = sizeof(struct Layer);

struct Network* create_network(int inputs) {
	struct Network *net = malloc(NETSIZE);
	net->inputs = inputs;
	net->outputs = inputs;
	net->max_neurons = 0;
	net->layernum = 0;
	net->layers = NULL;

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
	if (network->layers) {
		free(network->layers);
	}
	free(network);
}

struct Network* copy_network(struct Network *net) {
	struct Network *net_copy = malloc(NETSIZE);
	net_copy->inputs = net->inputs;
	net_copy->outputs = net->outputs;
	net_copy->max_neurons = net->max_neurons;
	net_copy->layernum = net->layernum;
	net_copy->layers = malloc(LAYERSIZE * net_copy->layernum);

	int i;
	for (i=0; i<net_copy->layernum; i++) {
		struct Layer *layer = &net_copy->layers[i];
		layer->inputs = net->layers[i].inputs;
		layer->neurons = net->layers[i].neurons;
		size_t biases_size = sizeof(double) * layer->neurons;
		size_t weights_size = sizeof(double) * layer->neurons * (layer->inputs + 1);
		layer->weights = malloc(weights_size);
		layer->biases = malloc(biases_size);
		memcpy(layer->weights, net->layers[i].weights, weights_size);
		memcpy(layer->biases, net->layers[i].biases, biases_size);
	}

	return net_copy;
}

void add_layer(struct Network *network, int neurons) {
	network->layernum++;
	network->layers = realloc(network->layers, LAYERSIZE * network->layernum);
	struct Layer *layer = &network->layers[network->layernum-1];
	if (network->layernum == 1) {
		layer->inputs = network->inputs;
	} else {
		layer->inputs = network->layers[network->layernum-2].neurons;
	}
	layer->neurons = neurons;
	layer->biases = calloc(neurons, sizeof(double));
	layer->weights = malloc(sizeof(double) * neurons * (layer->inputs + 1));
	int i;
	for (i=0; i<layer->neurons*(layer->inputs+1); i++) {
		//layer->weights[i] = 1;
		layer->weights[i] = (double)rand()/RAND_MAX*2.0-1.0;
	}
	for (i=0; i<layer->neurons; i++) {
	}
	network->outputs = layer->neurons;
	if (layer->neurons > network->max_neurons) {
		network->max_neurons = layer->neurons;
	}
}

void activate_network(struct Network *network, double *input, double *output) {
	if (!network || network->layernum == 0) {
		return;
	}
	int l,n,i;
	double outputs[network->max_neurons];
	memcpy(outputs, input, network->inputs * sizeof(double));
	struct Layer *layer;
	for (l=0; l<network->layernum; l++) {
		layer = &network->layers[l];
		double sums[layer->neurons];
		for (n=0; n<layer->neurons; n++) {
			sums[n] = layer->biases[n] * layer->weights[n*(layer->inputs+1)];
			for (i=0; i<layer->inputs; i++) {
				sums[n] += outputs[i] * layer->weights[n*(layer->inputs+1) + i];
			}
		}
		for (n=0; n<layer->neurons; n++) {
			outputs[n] = tanh(sums[n]);
		}
	}

	for (i=0; i<network->outputs; i++) {
		output[i] = outputs[i];
	}
}

void randomize_network(struct Network *network) {
	int i,j;
	for (i=0; i<network->layernum; i++) {
		struct Layer *layer = &network->layers[i];
		for (j=0; j<layer->neurons*(layer->inputs+1); j++) {
			layer->weights[j] = (double)rand()/RAND_MAX*2.0-1.0;
		}
	}
}

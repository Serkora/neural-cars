#ifndef NEURAL
#define NEURAL

struct Layer {
	int inputs;
	int neurons;
	double *weights;
	double *biases;
};

struct Network {
	int inputs;
	int outputs;
	int layernum;
	int max_neurons;
	struct Layer *layers;
};

struct Network* create_network(int inputs);
void add_layer(struct Network *network, int neurons);
void activate_network(struct Network *net, double *inputs, double *outputs);
void randomize_network(struct Network *network);

struct Network* copy_network(struct Network *net);
void delete_network(struct Network *network);

#endif

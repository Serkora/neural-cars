import math
import random
import numpy as np

class PybrainDriver(object):
	def __init__(self, inputs):
		import pybrain
		import pybrain.tools.shortcuts

		self.network = pybrain.tools.shortcuts.buildNetwork(inputs, 5, 3, 1, hiddenclass=pybrain.structure.TanhLayer)
		self.randomize()

	def randomize(self):
		self.network.randomize()

	def compute(self, speed, *cameras):
		output = self.network.activate([speed, *cameras])
		return output

	def copy(self, driver):
		for i in range(len(self.network.params)):
			self.network.params[i] = driver.network.params[i]

	def mutate(self, severity, chance):
		for i in range(len(self.network.params)):
			if random.random() >= chance:
				if random.random() >= 0.5:
					self.network.params[i] += self.network.params[i] * severity
				else:
					self.network.params[i] -= self.network.params[i] * severity

class Driver(object):
	def __init__(self, inputs):
		self.network = Network(inputs, 5, 3, 1)
		self.randomize()

	def randomize(self):
		self.network.randomize()

	def compute(self, speed, *sensors):
		outputs = self.network.predict([speed, *sensors])
		return outputs[0]

	def mutate(self, severity, chance):
		for layer in self.network.layers:
			if random.random() < chance:
				for neuron in layer.neurons:
					neuron.weights = tuple(neuron.weights * np.random.uniform(-severity/2, severity/2, neuron.inputs+1) + neuron.weights)

	def learn_from(self, driver, mutate=False, chance=0, severity=0):
		self.network = driver.network.copy()
		if mutate:
			self.mutate(severity, chance)

		# minimalist tanh network

class Neuron(object):
	__slots__ = ['activation', 'weights', 'bias_weight', 'inputs']

	def __init__(self, activation, inputs):
		self.activation = activation
		self.inputs = inputs
		self.weights = np.random.uniform(size=inputs+1) * 2 - 1
		self.weights = np.ones(inputs+1)
		self.weights = tuple(np.ones(inputs+1))

	def activate(self, inputs, bias):
		return self.activation(sum(p[0]*p[1] for p in zip(self.weights, inputs + (bias,))))

	def randomize(self):
		self.weights = tuple(np.random.uniform(size=self.inputs+1) * 2 - 1)

	def __repr__(self):
		return "Neuron weights: %s" % str(self.weights)

def sigmoid(x):
	return 1/(1 + np.exp(-x))

class Layer(object):
	def __init__(self, inputs, neurons, activation='tanh', bias=0):
		self.activation = activation
		if activation == "tanh":
			func = math.tanh
		elif activation == 'sigmoid':
			func = sigmoid
		elif activation == 'unit':
			func = lambda x: x
		else:
			func = lambda x: x

		self.neurons = tuple(Neuron(func, inputs) for i in range(neurons))
		self.bias = bias

	def activate(self, inputs):
		return tuple(neuron.activate(inputs, self.bias) for neuron in self.neurons)

	def randomize(self):
		for neuron in self.neurons:
			neuron.randomize()

	def copy(self):
		layer = self.__class__(self.neurons[0].inputs, len(self.neurons), self.activation)
		for i in range(len(self.neurons)):
			layer.neurons[i].weights = tuple(self.neurons[i].weights)
		return layer

	def __repr__(self):
		return "%s layer with %d neurons:\n%s" % (self.activation, self.neurons.size, "\n".join(str(neuron) for neuron in self.neurons))

class Network(object):
	def __init__(self, inputs, *layers, activation='tanh'):
		self.inputs = inputs
		self.outputs = layers[-1]
		self.activation = activation
		self.layers = [Layer(inputs, inputs, activation)]
		for neurons in layers:
			self.layers.append(Layer(inputs, neurons, activation))
			inputs = len(self.layers[-1].neurons)

	def predict(self, inputs):
		outputs = tuple(inputs)
		for layer in self.layers:
			outputs = layer.activate(outputs)
		return outputs

	def randomize(self):
		for layer in self.layers:
			layer.randomize()

	def copy(self):
		network = self.__class__(self.inputs, self.outputs, activation=self.activation)
		network.layers = [layer.copy() for layer in self.layers]
		return network

	def __repr__(self):
		inout = "Input layer has %d inputs and %d output%s." % (self.inputs, self.outputs, "s" if self.outputs > 1 else "")
		hidden = "\n".join(str(layer) for layer in self.layers[1:])
		return "Feedforward network with %d hidden layers. \n%s\nHidden:\n%s" % (len(self.layers)-2, inout, hidden)

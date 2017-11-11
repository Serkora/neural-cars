import numpy as np
import random

class PybrainDriver(object):
	def __init__(self, inputs):
		import pybrain
		import pybrain.tools.shortcuts

		self.network = pybrain.tools.shortcuts.buildNetwork(inputs, 4, 3, 2, 1, hiddenclass=pybrain.structure.TanhLayer)
		self.randomize()

	def randomize(self):
		self.network.randomize()

	def compute(self, speed, steering, *cameras):
		output = self.network.activate([speed, steering, *cameras])
		#print("\rputput = %.3f" % output, end="")
		return steering + 1 * output

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

	def compute(self, speed, steering, *cameras):
		output = self.network.predict([speed, steering, *cameras])
		#print("\rputput = %.3f" % output, end="")
		return steering + 1 * output

	def copy(self, driver):
		self.network = driver.network.copy()

	def mutate(self, severity, chance):
		for layer in self.network.layers:
			if random.random() < chance:
				for neuron in layer.neurons:
					neuron.weights += neuron.weights * np.random.uniform(-severity/2, severity/2, neuron.weights.size)


		# minimalist tanh network

class Neuron(object):
	__slots__ = ['activation', 'weights', 'bias_weight']

	def __init__(self, activation, inputs):
		self.activation = activation
		self.weights = np.random.uniform(size=inputs) * 2 - 1
		self.weights = np.ones(inputs)
		self.bias_weight = 0

	def activate(self, inputs, bias):
		return self.activation(np.sum(self.weights * inputs) + bias*self.bias_weight)

	def randomize(self):
		self.weights = np.random.uniform(size=len(self.weights)) * 2 - 1

	def __repr__(self):
		return "Neuron weights: %s" % str(self.weights)

def sigmoid(x):
	return 1/(1 + np.exp(-x))

class Layer(object):
	def __init__(self, inputs, neurons, activation='tanh', bias=0):
		self.activation = activation
		if activation == "tanh":
			func = np.tanh
		elif activation == 'sigmoid':
			func = sigmoid
		elif activation == 'unit':
			func = lambda x: x
		else:
			func = lambda x: x

		self.neurons = np.array([Neuron(func, inputs) for i in range(neurons)])
		self.bias = bias

	def activate(self, inputs):
		return np.array([neuron.activate(inputs, self.bias) for neuron in self.neurons])

	def randomize(self):
		[neuron.randomize() for neuron in self.neurons]

	def copy(self):
		layer = self.__class__(self.neurons[0].weights.size, self.neurons.size, self.activation)
		for i in range(self.neurons.size):
			layer.neurons[i].weights = self.neurons[i].weights.copy()
		return layer

	def __repr__(self):
		return "%s layer with %d neurons:\n%s" % (self.activation, self.neurons.size, "\n".join(str(neuron) for neuron in self.neurons))

class Network(object):
	def __init__(self, inputs, *layers, activation='tanh'):
		self.inputs = inputs
		self.outputs = layers[-1]
		self.activation = activation
		self.layers = [Layer(inputs, inputs)]
		for neurons in layers[:-1]:
			self.layers.append(Layer(inputs, neurons, activation))
			inputs = len(self.layers[-1].neurons)
		# output will just be a sum of all inputs
		self.layers.append(Layer(inputs, layers[-1], activation='unit'))

	def predict(self, inputs):
		outputs = np.array(inputs)
		for layer in self.layers:
			outputs = layer.activate(outputs)
		return outputs

	def randomize(self):
		for layer in self.layers:
			layer.randomize()

	def copy(self):
		network = self.__class__(self.inputs, 1, activation=self.activation)
		network.layers = [layer.copy() for layer in self.layers]
		return network

	def __repr__(self):
		inout = "Input layer has %d inputs and %d output%s." % (self.inputs, self.outputs, "s" if self.outputs > 1 else "")
		hidden = "\n".join(str(layer) for layer in self.layers[1:])
		return "Feedforward network with %d hidden layers. \n%s\nHidden:\n%s" % (len(self.layers)-2, inout, hidden)

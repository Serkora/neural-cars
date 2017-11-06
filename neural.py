import random
import pybrain
import pybrain.tools.shortcuts
from pybrain.structure import TanhLayer, SoftmaxLayer

class Driver(object):
	def __init__(self, inputs):
		self.network = pybrain.tools.shortcuts.buildNetwork(inputs, 4, 3, 2, 1, hiddenclass=TanhLayer)
		self.randomize()

	def randomize(self):
		self.network.randomize()

	def compute(self, speed, steering, *cameras):
		#self.network.randomize()
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

import random
import pybrain
import pybrain.tools.shortcuts
from pybrain.structure import TanhLayer, SoftmaxLayer

class Driver(object):
	def __init__(self):
		self.network = pybrain.tools.shortcuts.buildNetwork(9, 6, 3, 1, hiddenclass=TanhLayer)
		self.network.randomize()

	def compute(self, speed, steering, *cameras):
		#self.network.randomize()
		output = self.network.activate([speed, steering, *cameras])
		#print("\rputput = %.3f" % output, end="")
		return steering + 0.2 * output
		#return steering + 0.3 * (random.random() - 0.5)

d = Driver()

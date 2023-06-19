from Compiler.types import *
from Compiler.library import print_ln, if_, while_do, break_loop
from Compiler.program import Program
from util import bit_and

# WIDTH = 2
KEY = 0
PLAIN = 1
class Heap(object):
	def __init__(self, capacity, WIDTH=2, value_type=sint):
		self.WIDTH = WIDTH
		self.capacity, self.size = regint(capacity), regint(0)
		self.arr = value_type.Tensor([capacity, WIDTH])
	def __len__(self):
		return self.size

	def top(self):
		return self.arr[0]
	def push(self, entry):
		WIDTH, arr, size = self.WIDTH, self.arr, self.size
		crash(size >= self.capacity)
		pos = regint(size)
		arr[pos] = entry
		size.iadd(1)
		# fix up
		@while_do(lambda: pos > 0)
		def _():
			par = (pos - 1) / 2
			higher = arr[pos][KEY] < arr[par][KEY]
			if(PLAIN):
				higher = higher.reveal()
			for i in range(WIDTH):
				arr[pos][i], arr[par][i] = higher.cond_swap(arr[pos][i], arr[par][i])
			if(PLAIN):
				@if_(higher.bit_not())
				def _():
					break_loop()
			pos.update(par)

	def pop(self):
		WIDTH, arr, size = self.WIDTH, self.arr, self.size
		crash(size <= 0)
		size.iadd(-1)
		top = arr.value_type.Array(WIDTH)
		top.assign(arr[0])
		arr[0] = arr[size]
		# fix down
		par = regint(0)
		lch = par * 2 + 1
		@while_do(lambda: lch < size)
		def _():
			having_rch = (lch < size - 1)
			higher_rch = (arr[lch+1][KEY] < arr[lch][KEY]).reveal()
			ch = bit_and(having_rch, higher_rch).if_else(lch+1, lch)
			higher = arr[ch][KEY] < arr[par][KEY]
			if(PLAIN):
				higher = higher.reveal()
			for i in range(WIDTH):
				arr[ch][i], arr[par][i] = higher.cond_swap(arr[ch][i], arr[par][i])
			if(PLAIN):
				@if_(higher.bit_not())
				def _():
					break_loop()
			par.update(ch)
			lch.update(par * 2 + 1)
		# print_ln("pop[%s]: %s", self.size, top.reveal())
		return top

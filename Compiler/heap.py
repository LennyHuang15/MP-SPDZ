from Compiler.types import *
from Compiler.library import runtime_error_if
from util_mpc import copy, alloc_arr, print_arr
from util_heap import BaseHeap, sift_up, sift_down

ASSERT = 1
class Heap(BaseHeap):
	def __init__(self, capacity, WIDTH=None, value_type=sint, key=None):
		self.capacity, self.size = regint(capacity), regint(0)
		self.arr = alloc_arr(capacity, value_type=value_type, WIDTH=WIDTH)
		if key is None:
			key = lambda el: el[0]
		self.key = key

	def top(self):
		return copy(self.arr[0])
	def push(self, entry, dist_p=regint(0)):
		arr, size = self.arr, self.size
		if ASSERT:
			runtime_error_if(size >= self.capacity, "push")
		arr[size] = entry
		size.iadd(1)
		self._sift_up()
		# sift_up(arr, pos, self.key)

	def replace_top(self, entry):
		self.arr[0] = entry
		self._sift_down()
	def _sift_down(self):
		par = regint(0)
		sift_down(self.arr, par, self.size, self.key)
	def _sift_up(self):
		sift_up(self.arr, self.size - 1, self.key)

	def pop(self):
		arr, size = self.arr, self.size
		if ASSERT:
			runtime_error_if(size <= 0, "pop")
		size.iadd(-1)
		top = copy(arr[0])
		arr[0] = arr[size]
		self._sift_down()
		return top

	def print(self, name=None):
		print_arr(self.arr, size=self.size, name=name)

# def heap2_min(a, b):
# 	empty_a, empty_b = (a.size <= 0), (b.size <= 0)
# 	crash(empty_a.bit_and(empty_b))
# 	min_dist, take_sec = a.arr.value_type(0), MemValue(True)
# 	@if_e(empty_a.bit_or(empty_b))
# 	def _():
# 		@if_e(empty_a)
# 		def _():
# 			min_dist.update(b.top()[0])
# 			take_sec.write(False)
# 		@else_ # empty_b
# 		def _():
# 			min_dist.update(a.top()[0])
# 	@else_
# 	def _():
# 		dist_a, dist_b = a.top()[0], b.top()[0]
# 		take_sec.write(dist_a < dist_b)
# 		min_dist.update(take_sec.if_else(dist_a, dist_b))
# 		# min_dist.update(min(a.top()[0], b.top()[0]))
# 	return min_dist, take_sec

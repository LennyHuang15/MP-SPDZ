from Compiler.types import *
from util_heap import BaseHeap, sift_up, sift_down

KEY = 0
class Heap(BaseHeap):
	def __init__(self, capacity, WIDTH=2, value_type=sint):
		self.capacity, self.size = regint(capacity), regint(0)
		self.arr = value_type.Tensor([capacity, WIDTH])
		self.key = lambda el: el[KEY]

	def top(self):
		return self.arr[0]
	def push(self, entry):
		arr, size = self.arr, self.size
		crash(size >= self.capacity)
		pos = regint(size)
		arr[pos] = entry
		size.iadd(1)
		sift_up(arr, pos, self.key)

	def pop(self):
		arr, size = self.arr, self.size
		crash(size <= 0)
		size.iadd(-1)
		top = arr[0].same_shape()
		top.assign(arr[0])
		arr[0] = arr[size]

		par = regint(0)
		sift_down(arr, par, size, self.key)
		return top

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

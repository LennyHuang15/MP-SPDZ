from Compiler.types import *
from Compiler.library import print_ln, print_str, \
	if_, while_do, for_range, break_loop, runtime_error_if
from util_mpc import runtime_error_if, alloc_arr, copy, ASSERT

# ASSERT = 1
class Stack(object):
	def __init__(self, capacity, WIDTH=None):
		self.capacity, self.size = regint(capacity), regint(0)
		self.arr = alloc_arr(capacity, WIDTH=WIDTH)
	def clear(self):
		self.size.update(0)

	def push(self, entry):
		arr, size = self.arr, self.size
		if ASSERT:
			runtime_error_if(size >= self.capacity, "stack push %s", size)
		arr[size] = entry
		size.iadd(1)
	def pop(self):
		arr, size = self.arr, self.size
		if ASSERT:
			runtime_error_if(size <= 0, "pop")
		size.iadd(-1)
		top = copy(arr[size])
		return top

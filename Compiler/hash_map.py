from Compiler.types import *
from Compiler.library import print_ln, print_str, \
	if_, while_do, for_range, break_loop, runtime_error_if
from util_mpc import runtime_error_if, alloc_arr, copy, ASSERT, \
	if_, if_e, else_, while_do, break_loop

FAC_HASH = 16
DEBUG = 1
class HashMap(object):
	def __init__(self, capacity):
		self.capacity, self.size = regint(capacity), regint(0)
		self.table = regint.Array(capacity)
		self.table.assign_all(-1)
		self.arr = regint.Tensor([capacity, 4])# key1, key2, val, next
		self.arr.assign_all(-1)

	def _hash(self, key1, key2):
		return (key1 % FAC_HASH + key2) % self.capacity

	def insert(self, key1, key2, val):
		table, arr = self.table, self.arr
		size, capacity = self.size, self.capacity
		if ASSERT:
			runtime_error_if(size >= capacity, "hash map full")
		key = self._hash(key1, key2)
		if DEBUG:
			print_ln("H(%s,%s) = %s", key1, key2, key)
		@if_e(table[key] == -1)
		def _():
			table[key] = size
		@else_# find a free slot
		def _():
			pos = table[key]
			@while_do(lambda: arr[pos][-1] != -1)
			def _():
				if ASSERT:
					runtime_error_if((arr[pos][0] == key1)\
						.bit_and(arr[pos][1] == key2), \
						"hash_map[%s,%s] already exists", key1, key2)
				pos.update(arr[pos][-1])
			# pos.next == -1 (free slot)
			arr[pos][-1] = size
		arr[size] = (key1, key2, val, -1)
		size.iadd(1)

	def find(self, key1, key2):
		table, arr = self.table, self.arr
		size, capacity = self.size, self.capacity
		key = self._hash(key1, key2)
		if DEBUG:
			print_ln("H(%s,%s) = %s", key1, key2, key)
		pos = table[key]
		val = regint(-1)
		@if_(pos >= 0)# else return -1
		def _():
			@while_do(lambda: pos != -1)
			def _():
				if ASSERT:
					runtime_error_if(pos >= size, \
						"hash_map[%s,%s]", key1, key2)
				@if_((arr[pos][0] == key1).bit_and(arr[pos][1] == key2))
				def _():
					val.update(arr[pos][2])
					break_loop()
				pos.update(arr[pos][-1])
		return val
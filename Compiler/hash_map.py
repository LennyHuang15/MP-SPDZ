from Compiler.types import *
from Compiler.library import print_ln, print_str, runtime_error_if, \
	if_, if_e, else_, while_do, for_range, break_loop
from util_mpc import ASSERT

DEBUG = 0
def _equal(item, keys):
	return (item[0] == keys[0]).bit_and(item[1] == keys[1])
class HashMap(object):
	def __init__(self, base_cap, FAC_HASH):
		self.base_cap, self.FAC_HASH = base_cap, FAC_HASH
		capacity = base_cap * FAC_HASH
		self.capacity, self.size = regint(capacity), regint(0)
		self.table = regint.Array(capacity)
		self.arr = regint.Tensor([capacity, 4])# key1, key2, val, next
		self.clear()
	def clear(self):
		self.size.update(0)
		cap, table, arr = self.capacity, self.table, self.arr
		@for_range(cap)
		def _(i):
			table[i] = arr[i][-1] = -1
		# self.table.assign_all(-1)
		# self.arr.assign_all(-1)

	def _hash(self, keys):
		base_cap, FAC_HASH, capacity = self.base_cap, self.FAC_HASH, self.capacity
		key1, key2 = keys
		key = key1 % FAC_HASH * base_cap + key2
		if ASSERT:
			runtime_error_if(key1 >= base_cap, "key[%s] >= %s", key1, base_cap)
			runtime_error_if(key2 >= base_cap, "key[%s] >= %s", key2, base_cap)
			runtime_error_if(key >= capacity, "hash(%s,%s) = %s", *keys, key)
		return key# % capacity

	def insert(self, keys, val):
		table, arr = self.table, self.arr
		size, capacity = self.size, self.capacity
		if ASSERT:
			runtime_error_if(size >= capacity, "hash map full")
		key = self._hash(keys)
		if DEBUG:
			print_ln("H(%s,%s) = %s", *keys, key)
		pos = regint(table[key])
		@if_e(pos == -1)# no items yet
		def _():
			table[key] = size
		@else_# search for a free slot
		def _():
			@while_do(lambda: arr[pos][-1] != -1)
			def _():
				@if_(key == 4442598)
				def _():
					print_ln("insert[%s,%s=%s,%s]: %s", *keys, key, pos, arr[pos])
				if ASSERT:
					runtime_error_if(_equal(arr[pos], keys), \
						"hash_map insert [%s,%s]: already exists", *keys)
				pos.update(arr[pos][-1])
				@if_(key == 4442598)
				def _():
					print_ln("pos[%s]: %s", pos, arr[pos])
			# pos.next == -1 (free slot)
			@if_(key == 4442598)
			def _():
				print_ln("insert2[%s,%s=%s,%s]: %s", *keys, key, pos, arr[pos])
			arr[pos][-1] = size
			@if_(key == 4442598)
			def _():
				print_ln("insert3[%s,%s=%s,%s]: %s", *keys, key, pos, arr[pos])
		if ASSERT:
			runtime_error_if(val < 0, "hash_map insert [%s,%s]: %s < 0", *keys, val)
		arr[size] = (*keys, val, -1)
		size.iadd(1)
		@if_(key == 4442598)
		def _():
			self.find(keys)

	def find(self, keys):
		table, arr = self.table, self.arr
		size, capacity = self.size, self.capacity
		key = self._hash(keys)
		if DEBUG:
			print_ln("H(%s,%s) = %s", *keys, key)
		pos, val = regint(table[key]), regint(-1)
		@while_do(lambda: pos != -1)
		def _():
			if ASSERT:
				runtime_error_if(pos >= size, "hash_map find[%s,%s]", *keys)
			@if_(key == 4442598)
			def _():
				print_ln("search[%s,%s=%s]: %s", *keys, key, arr[pos])
			@if_(_equal(arr[pos], keys))
			def _():
				val.update(arr[pos][2])
				break_loop()
			pos.update(arr[pos][-1])
		return val
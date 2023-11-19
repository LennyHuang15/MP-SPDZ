from Compiler.types import *
from Compiler.library import runtime_error_if, print_ln, \
	if_, if_e, else_, while_do, for_range, break_loop
from util_heap import BaseHeap
from util_mpc import print_arr, add_stat, OFS, ASSERT
from util_T_heap import *

# ASSERT = 1
DEBUG = 0
class Heap(BaseHeap):
	def __init__(self, cap, key, fac=2, value_type=regint):
		self.capacity, self.fac = capacity, fac
		self.key, self._merge_l = key, _merge_l
		self.size, self.size_h = [regint(0) for _ in range(2)]
		self.arr_l = alloc_arr(capacity, value_type=value_type, WIDTH=WIDTH)
		self.arr_h = alloc_arr(capacity, value_type=value_type, WIDTH=WIDTH)
	def clear(self):
		self.size.update(0)
		self.size_h.update(0)
	
	def top(self):
		pass
	def push(self, entry):
		fac, key, _merge_l = self.fac, self.key, self._merge_l
		arr_l, size = self.arr_l, self.size
		arr_h, size_h = self.arr_h, self.size_h
		@if_(size > 0)
		def _():
			runtime_error_if(size != size_h + 1, "T-heap0")
		# merge
		pos_mst, pos_men = regint(-1), regint(-1)
		pos_m = regint(size - 1)
		@while_do(lambda: pos_m >= 0)
		def _():
			d1, d2 = entry[FIELDS.W], arr_l[pos_m][FIELDS.W]
			@if_(d2 > d1 * fac)
			def _():
				pos_men.update(pos_m)
				break_loop()
			@if_(d1 <= d2 * fac)
			def _():# can merge
				@if_(pos_mst < 0)
				def _():
					pos_mst.update(pos_m)
				entry_merged = _merge_l(entry, arr_l[pos_m])
				entry.assign(entry_merged)
			pos_m.iadd(-1)
		@if_(pos_mst < 0)
		def _():
			pos_mst.update(pos_men)
		if ASSERT:
			runtime_error_if(pos_men != pos_m, "T-heap1")
			runtime_error_if(pos_men > pos_mst, "T-heap2")
		# concat the right
		@if_(pos_mst < size - 1)
		def _():# having nodes in the right, concat [pos_mst+1]
			# first move right
			@for_range(size - 1, pos_mst, -1)
			def _(i):
				arr_l[i+1] = arr_l[i]
			if ASSERT:
				runtime_error_if(size >= self.capacity, "T-heap3")
			size.iadd(1)
			# set arr_h[pos_mst+1]
			@if_e(pos_mst + 2 == size - 1)
			def _():
				arr_h[pos_mst + 1] = _merge(entry, arr_l[pos_mst + 2])
			@else_
			def _():
				arr_h[pos_mst + 1] = _merge(entry, arr_h[pos_mst + 2])
		arr_l[pos_mst + 1] = entry
		# concat the left
		@if_(pos_men >= 0)
		def _():# set arr_h[pos_men]
			@if_e(pos_men < size_h)
			def _():# having arr_h[pos_men]
				# update(arr_h[pos_men])
				arr_h[pos_men] = _merge(arr_l[pos_men], entry)
			@else_
			def _():
				arr_h[pos_men] = _merge(arr_l[pos_men], entry)
		@if_(pos_men < pos_mst)
		def _():# move left
			@for_range(pos_mst + 1, size)
			def _(i):
				arr_l[pos_men + i - pos_mst] = arr_l[i]
				arr_h[pos_men + i - pos_mst] = arr_h[i]
			size.iadd(pos_men - pos_mst)
			size_h.update(size - 1)

	def pop(self):
		pass

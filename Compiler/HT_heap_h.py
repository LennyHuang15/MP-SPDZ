from Compiler.types import *
from Compiler.library import runtime_error_if, print_ln, \
	if_, if_e, else_, while_do, for_range, break_loop
from util_heap import BaseHeap
from util_mpc import copy, alloc_arr, print_arr, add_stat, OFS, ASSERT
from util_T_heap import *
from util_T_heap import _merge

# ASSERT = 1
DEBUG = 0

class Heap(BaseHeap):
	def __init__(self, cap, key, tours_l, _merge_l, heap_l, \
			fac=2, fac_div=1):
		self.capacity, self.fac, self.fac_div = cap, fac, fac_div
		if ASSERT:
			runtime_error_if(fac < fac_div, "fac %s, fac_div %s", fac, fac_div)
		self.key, self.tours, self._merge_l = key, tours_l, _merge_l
		self.arr = alloc_arr(cap, value_type=regint, WIDTH=len(FIELDS))
		self.size = regint(0)
		self.heap_l = heap_l
	def clear(self):
		self.size.update(0)
	
	def _find_top_idx(self):# -> idx in arr
		arr, size = self.arr, self.size
		if ASSERT:
			runtime_error_if(size <= 0, "T_heap _top_idx1")
		# idx = regint(size - 1)
		idx = regint(-1)
		@for_range(size)
		def _(i):
			@if_(arr[i][FIELDS.R_WIN] == 0)
			def _():
				idx.update(i)
				break_loop()
		if ASSERT:
			runtime_error_if(idx < 0, "T_heap _top_idx2")
		return idx
	def top(self):# -> tidx
		idx = self._find_top_idx()
		return self.arr[idx][FIELDS.LIDX]

	def init_tour(self, tidx):
		entry = self.tours[tidx]
		wid, d = entry[FIELDS.WID], entry[FIELDS.W]
		return (tidx, -1, wid, wid, 0, d)
	def push(self, tidx):
		if DEBUG:
			print_ln("arr_h push %s", tidx)
		tours, key, _merge_l = self.tours, self.key, self._merge_l
		arr, size, fac, fac_div = self.arr, self.size, self.fac, self.fac_div
		# merge
		pos_mst, pos_men = regint(-1), regint(-1)
		pos_m = regint(size - 1)
		@while_do(lambda: pos_m >= 0)
		def _():
			tidx_m = arr[pos_m][FIELDS.LIDX]
			entry, entry_m = tours[tidx], tours[tidx_m]
			d1, d2 = entry[FIELDS.W], entry_m[FIELDS.W]
			@if_(d2 * fac_div > d1 * fac)
			def _():
				pos_men.update(pos_m)
				@if_(pos_mst < 0)
				def _():
					pos_mst.update(pos_men)
				break_loop()
			@if_(d1 * fac_div <= d2 * fac)
			def _():# can merge
				@if_(pos_mst < 0)
				def _():
					pos_mst.update(pos_m)
				tidx_merged = _merge_l(tidx, tidx_m)
				tidx.update(tidx_merged)
			pos_m.iadd(-1)
		if ASSERT:
			runtime_error_if(pos_men != pos_m, "T-heap1")
			runtime_error_if(pos_men > pos_mst, "T-heap2")
			runtime_error_if(size >= self.capacity, "T-heap3")
		shift_arr(arr, pos_mst+1, pos_mst+2, size-pos_mst-1)
		size.iadd(1)
		# insert at [pos_mst + 1]
		@if_e(pos_mst + 2 < size)
		def _():# having nodes in the right, concat it
			arr[pos_mst + 1] = _merge(key, tours[tidx], arr[pos_mst+2], tidx)
		@else_
		def _():# independent node
			arr[pos_mst + 1] = self.init_tour(tidx)
		# move left
		@if_(pos_men < pos_mst)
		def _():
			shift_arr(arr, pos_mst+1, pos_men+1, size - pos_mst-1)
			size.iadd(pos_men - pos_mst)
		# concat the left, and propagate
		@for_range(pos_men, -1, -1)
		def _(i):
			tidx_l = arr[pos_men][FIELDS.LIDX]
			r_win, wid = arr[pos_men][FIELDS.R_WIN], arr[pos_men][FIELDS.WID]
			arr[pos_men] = _merge(key, tours[tidx_l], arr[pos_mst+1], tidx_l)
			r_win_, wid_ = arr[pos_men][FIELDS.R_WIN], arr[pos_men][FIELDS.WID]
			if ASSERT:
				@if_(r_win_ == 0)
				def _():
					runtime_error_if(r_win == 1, "T-heap4")
					runtime_error_if(wid_ != wid, "T-heap5")
			@if_(wid_ == wid)
			def _():
				break_loop()

	def _replay_up(self, st):
		key, tours = self.key, self.tours
		arr, size = self.arr, self.size
		@for_range(st, -1, -1)
		def _(i):
			tidx = arr[i][FIELDS.LIDX]
			@if_e(i+1 >= size)
			def _():
				arr[i] = self.init_tour(tidx)
			@else_
			def _():
				arr[i] = _merge(key, tours[tidx], arr[i+1], tidx)
	def pop(self):
		tours, arr, size = self.tours, self.arr, self.size
		if ASSERT:
			runtime_error_if(size <= 0, "T-heap pop0")
		idx = self._find_top_idx()
		top = arr[idx][FIELDS.LIDX]
		@if_(idx < size - 1)
		def _():# having arr[idx+1], move left
			shift_arr(arr, idx+1, idx, size - idx - 1)
		size.iadd(-1)
		self._replay_up(idx - 1)
		return top
	def replace_top(self, tidx):
		tours, arr, size = self.tours, self.arr, self.size
		idx = self._find_top_idx()
		top = arr[idx][FIELDS.LIDX]
		self._replay_up(idx)
		return top

	def print(self, name=""):
		tours, key, arr, size = self.tours, self.key, self.arr, self.size
		print_ln("%s[%s]:", name, size)
		@for_range(size)
		def _(i):
			print_tour(arr[i])
			tidx_l = arr[i][FIELDS.LIDX]
			print_tour(tours[tidx_l], key=key)
			print_ln("")

from Compiler.types import *
from Compiler.library import if_, runtime_error_if, print_ln
from util_heap import BaseHeap, sift_up, sift_down, heapify
from util_mpc import insertion_sort, print_stats, OFS

KEY = 0
ASSERT = 0
DEBUG = 1
class Heap(BaseHeap):
	def __init__(self, cap_l, cap_h, link_index, WIDTH=2, value_type=sint):
		self.cap_l, self.cap_h = regint(cap_l), regint(cap_h)
		self.link_index = link_index
		self.arr_l = value_type.Tensor([cap_l, WIDTH])
		self.size_h, self.size = regint(0), regint(0)
		self.arr_h = regint.Tensor([cap_h, 2])# srcs, sizes_l
		self.key_l = lambda el: el[KEY]
		self.key_h = lambda el: self.top_l(el[0])[KEY]
		from link_graph import MAX_DEG
		self.dists_p = regint.Array(MAX_DEG)
	def _pos_st(self, src):
		return self.link_index[src]
	
	def top_l(self, src):
		pos_st = self._pos_st(src)
		return self.arr_l[pos_st]
	def top(self):
		src = self.arr_h[0][0]
		return self.top_l(src)

	def begin_push(self, src):
		super().begin_push(src)
		self.cur_src, self.cur_size_l = src, regint(0)
		if ASSERT:
			runtime_error_if(src >= self.cap_h, "begin push")
			pos_st, pos_en = self._pos_st(src), self._pos_st(src + 1)
			runtime_error_if(pos_en - pos_st > self.dists_p.length, "begin push_l")
	def push(self, entry, dist_p=regint(0)):
		src, arr_l, size_l = self.cur_src, self.arr_l, self.cur_size_l
		pos_st, pos_en = self._pos_st(src), self._pos_st(src + 1)
		# print_ln("push %s, %s, %s, %s", src, size_l, pos_st, pos_en)
		if ASSERT:
			runtime_error_if(pos_st + size_l >= pos_en, "push")
		arr_l[pos_st + size_l], self.dists_p[size_l] = entry, dist_p
		size_l.iadd(1)
		self.size.iadd(1)
	def end_push(self):
		src, arr_l = self.cur_src, self.arr_l
		pos_st, size_l = self._pos_st(src), self.cur_size_l
		@if_(size_l > 0)
		def _():
			if DEBUG:
				from util_mpc import print_arr
				def print_arr_l(name):
					key = lambda el: el[KEY]
					print_arr(arr_l, size_l, pos_st, key, name)
				# print_arr_l("arr_l")
				# print_arr(self.dists_p, size_l, name='dists_p')
			# sort by heuristic then heapify by real
			insertion_sort(arr_l, pos_st, pos_st + size_l, \
				ws=self.dists_p, ws_st=0)
			if DEBUG:
				print_arr_l("sorted")
				print_arr(self.dists_p, size_l, name='dists_p')
			heapify(arr_l, size_l, self.key_l, st=pos_st)
			if DEBUG:
				print_arr_l("heapified")
				print_stats(OFS.CmpHeapify)
			# add into heap_h
			arr_h, size_h = self.arr_h, self.size_h
			pos = regint(size_h)
			arr_h[pos] = (src, size_l)
			size_h.iadd(1)
			sift_up(arr_h, pos, self.key_h)
		super().end_push()

	def pop_l(self, src, size_l):
		if ASSERT:
			runtime_error_if(size_l <= 0, "pop_l")
		size_l.iadd(-1)
		arr_l, pos_st = self.arr_l, self._pos_st(src)
		top = arr_l[0].same_shape()
		top.assign(arr_l[pos_st])
		arr_l[pos_st] = arr_l[pos_st + size_l]
		
		par = regint(pos_st)
		sift_down(arr_l, par, size_l, self.key_l, st=pos_st)
		return top

	def pop(self):
		arr_h, size_h = self.arr_h, self.size_h
		if ASSERT:
			runtime_error_if(size_h <= 0, "pop")
		src, size_l = self.arr_h[0]
		top = self.pop_l(src, size_l)
		self.arr_h[0][1] = size_l
		self.size.iadd(-1)
		@if_(size_l == 0)
		def _():
			size_h.iadd(-1)
			arr_h[0] = arr_h[size_h]
		par = regint(0)
		sift_down(arr_h, par, size_h, self.key_h)
		return top

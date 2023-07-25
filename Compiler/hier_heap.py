from Compiler.types import *
from Compiler.library import if_, runtime_error_if
from util_heap import BaseHeap, sift_up, sift_down, heapify

KEY = 0
class Heap(BaseHeap):
	def __init__(self, cap_l, cap_h, link_index, WIDTH=2, value_type=sint):
		self.cap_l, self.cap_h = regint(cap_l), regint(cap_h)
		self.link_index = link_index
		self.arr_l = value_type.Tensor([cap_l, WIDTH])
		self.size_h, self.size = regint(0), regint(0)
		self.arr_h = regint.Tensor([cap_h, 2])# srcs, sizes_l
		self.key_l = lambda el: el[KEY]
		self.key_h = lambda el: self.top_l(el[0])[KEY]

	def top_l(self, src):
		pos_st = self.link_index[src]
		return self.arr_l[pos_st]
	def top(self):
		src = self.arr_h[0][0]
		return self.top_l(src)

	def begin_push(self, src):
		runtime_error_if(src >= self.cap_h, "push")
		self.cur_src, self.cur_size_l = src, regint(0)
	def push(self, entry):
		src, arr_l = self.cur_src, self.arr_l
		pos_st, size_l = self.link_index[src], self.cur_size_l
		arr_l[pos_st + size_l] = entry
		size_l.iadd(1)
		self.size.iadd(1)
	def end_push(self):
		src, arr_l = self.cur_src, self.arr_l
		pos_st, size_l = self.link_index[src], self.cur_size_l
		@if_(size_l > 0)
		def _():
			# sort by heuristic then heapify by real
			heapify(arr_l, size_l, self.key_l, st=pos_st)
			# add into heap_h
			arr_h, size_h = self.arr_h, self.size_h
			pos = regint(size_h)
			arr_h[pos] = (src, size_l)
			size_h.iadd(1)
			sift_up(arr_h, pos, self.key_h)

	def pop_l(self, src, size_l):
		runtime_error_if(size_l <= 0, "pop_l")
		size_l.iadd(-1)
		arr_l, pos_st = self.arr_l, self.link_index[src]
		top = arr_l[0].same_shape()
		top.assign(arr_l[pos_st])
		arr_l[pos_st] = arr_l[pos_st + size_l]
		
		par = regint(pos_st)
		sift_down(arr_l, par, size_l, self.key_l, st=pos_st)
		return top

	def pop(self):
		arr_h, size_h = self.arr_h, self.size_h
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

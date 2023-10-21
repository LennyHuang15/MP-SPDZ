from Compiler.types import *
from Compiler.library import if_, runtime_error_if, print_ln
from util_heap import BaseHeap, sift_up, sift_down, heapify
from util_mpc import copy, insertion_sort, print_stats, OFS

KEY = 0
ASSERT = 0
DEBUG = 0
class Heap(BaseHeap):
	def __init__(self, cap_l, cap_h, WIDTH=2, value_type=sint):
		self.cap_l, self.cap_h = regint(cap_l), regint(cap_h)
		self.arr_l = value_type.Tensor([cap_l, WIDTH])
		self.size_h, self.size = regint(0), regint(0)
		self.arr_h = regint.Tensor([cap_h, 2])# pos_st, size_l
		self.key_l = lambda el: el[KEY]
		self.key_h = lambda el: self.top_l(el[0])[KEY]
		from link_graph import MAX_DEG
		self.dists_p = regint.Array(MAX_DEG)
	
	def top_l(self, pos_st):
		return self.arr_l[pos_st]
	def top(self):
		pos_st = self.arr_h[0][0]
		return self.top_l(pos_st)

	def begin_push(self, src):
		super().begin_push(src)
		self.cur_pos_st, self.cur_size_l = regint(self.size), regint(0)
		if ASSERT:
			runtime_error_if(self.size_h >= self.cap_h, "begin push")
	def push(self, entry, dist_p=regint(0)):
		arr_l, pos_st, size_l = self.arr_l, self.cur_pos_st, self.cur_size_l
		# print_ln("push %s, %s", pos_st, size_l)
		if ASSERT:
			runtime_error_if(pos_st + size_l >= self.cap_l, "hier push")
		arr_l[pos_st + size_l], self.dists_p[size_l] = entry, dist_p
		size_l.iadd(1)
		self.size.iadd(1)
	def end_push(self):
		arr_l, pos_st, size_l = self.arr_l, self.cur_pos_st, self.cur_size_l
		@if_(size_l > 0)
		def _():
			if DEBUG:
				from util_mpc import print_arr
				def print_arr_l(name):
					print_arr(arr_l, size_l, pos_st, self.key_l, name)
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
			arr_h[pos] = (pos_st, size_l)
			size_h.iadd(1)
			sift_up(arr_h, pos, self.key_h)
		super().end_push()

	def pop_l(self, pos_st, size_l):
		if ASSERT:
			runtime_error_if(size_l <= 0, "pop_l")
		size_l.iadd(-1)
		arr_l = self.arr_l
		top = copy(arr_l[pos_st])
		# top = arr_l[0].same_shape()
		# top.assign(arr_l[pos_st])
		arr_l[pos_st] = arr_l[pos_st + size_l]
		
		par = regint(pos_st)
		sift_down(arr_l, par, size_l, self.key_l, st=pos_st)
		return top

	def pop(self):
		arr_h, size_h = self.arr_h, self.size_h
		if ASSERT:
			runtime_error_if(size_h <= 0, "pop")
		pos_st, size_l = self.arr_h[0]
		top = self.pop_l(pos_st, size_l)
		self.arr_h[0][1] = size_l
		self.size.iadd(-1)
		@if_(size_l == 0)
		def _():
			size_h.iadd(-1)
			arr_h[0] = arr_h[size_h]
		par = regint(0)
		sift_down(arr_h, par, size_h, self.key_h)
		return top

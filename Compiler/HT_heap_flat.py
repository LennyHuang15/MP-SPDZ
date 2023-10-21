from Compiler.types import *
from Compiler.library import if_, runtime_error_if, print_ln
from util_heap import BaseHeap, sift_up, sift_down, heapify
from util_mpc import insertion_sort, print_stats, OFS

KEY = 0
ASSERT = 1
DEBUG = 0
CAP_H = 16

class Heap(BaseHeap):
	def __init__(self, cap, WIDTH=2, value_type=sint):
		self.capacity, self.dists_p = regint(cap), regint(cap)
		self.arr = value_type.Tensor([cap, WIDTH])
		self.tours_h = regint.Tensor([CAP_H, 3])# tid_l, tid_r, flag
		self.arr_h = regint.Tensor([CAP_H, 3])# w, winner, flag
		self.size, self.size_h = regint(0), regint(0)
		from link_graph import MAX_DEG
		self.hfm_queue = regint.Array(MAX_DEG + CAP_H)
		self.key = lambda el: el[KEY]
		from enum import Enum
		self.FLAG = Enum('FLAG', \
			('INVALID', 'L', 'R'), start=0)
	
	# def top(self):
	# 	src = self.arr_h[0][0]
	# 	return self.top_l(src)

	def begin_push(self, src):
		super().begin_push(src)
		self.cur_src, self.old_size = src, regint(self.size)
	def push(self, entry, dist_p=regint(0)):
		src, size, FLAG = self.cur_src, self.size, self.FLAG
		arr, dists_p, hfm_queue = self.arr, self.dists_p, self.hfm_queue
		# print_ln("push %s, %s, %s, %s", src, size_l, pos_st, pos_en)
		if ASSERT:
			runtime_error_if(size >= self.capacity, "HT push")
		arr[size], dists_p[size] = entry, dist_p
		hfm_queue[size - old_size] = (dist_p, -1, -1, FLAG.INVALID)
		size.iadd(1)
	def end_push(self):
		src, arr = self.cur_src, self.arr
		size, old_size, size_h = self.size, self.old_size, self.size_h
		@if_(size > old_size)
		def _():
			size_add = size - old_size
			@for_range(size_h)
			def _(i):
				hfm_queue[size_add + i] = self.arr_h[i]
			heapify(hfm_queue, size_add + size_h, self.key)
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

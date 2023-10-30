from Compiler.types import *
from Compiler.library import runtime_error_if, print_ln, print_str, \
	if_, if_e, else_, while_do, do_while, break_loop, \
	for_range, for_range_opt_multithread, for_range_opt
from util_heap import BaseHeap
from util_mpc import copy, print_arr, add_stat, get_stat, OFS, \
	ASSERT, DATA_BOUND
from heap import Heap as HeapFlat
from link_graph import MAX_DEG
from stack import Stack
from util import max

# ASSERT = 1
DEBUG = 0
MAX_PATH = 128
PUSH_PARALLEL = 0
MULTI_THREAD = 2
def key_l(el):
	return el[0]
def dist2w(d):
	return 1
	# return DATA_BOUND / (d**1)

from enum import IntEnum
FIELDS = IntEnum('FIELDS', \
	('LIDX', 'RIDX', 'WID', 'LID', 'R_WIN', 'W'), start=0)
class Heap(BaseHeap):
	def __init__(self, cap_l, cap_h, WIDTH=2, value_type=sint):
		self.cap_l, self.cap_h = regint(cap_l), regint(cap_h)
		self.arr_l = value_type.Tensor([cap_l, WIDTH])
		self.size, self.size_l = regint(0), regint(0)
		self.tours = regint.Tensor([cap_l * 2, len(FIELDS)])
		self.size_tour = regint(0)

		self.key_h = lambda tidx: key_l(self.top_l(tidx))
		self.key_hfm = lambda tidx: self.tours[tidx][FIELDS.W]
		self.arr_h = HeapFlat(cap_h, value_type=regint, \
			key=self.key_h)

		self.hfm_queue = HeapFlat(MAX_DEG, value_type=regint, \
			key=self.key_hfm)
		self.path = Stack(MAX_PATH)
	def clear(self):
		self.size.update(0)
		self.size_l.update(0)
		self.size_tour.update(0)
		self.arr_h.clear()
	
	def top_l(self, tidx):
		if ASSERT:
			runtime_error_if(self.size <= 0, "top_l")
		wid = self.tours[tidx][FIELDS.WID]
		return self.arr_l[wid]
	def top(self):
		tidx = self.arr_h.top()
		return self.top_l(tidx)

	def begin_push(self, src):
		super().begin_push(src)
		self.hfm_queue.clear()
	def push(self, entry, dist_p=regint(0)):
		arr_l, tours, hfm_queue = self.arr_l, self.tours, self.hfm_queue
		size, size_l, size_t = self.size, self.size_l, self.size_tour
		if ASSERT:
			runtime_error_if(size_l >= self.cap_l, "push %s >= %s", size_l, self.cap_l)
		arr_l[size_l] = entry
		tours[size_t] = (-1, -1, size_l, size_l, -1, dist2w(dist_p))
		hfm_queue.push(size_t)
		for x in [size, size_l, size_t]:
			x.iadd(1)
	def end_push(self):
		if PUSH_PARALLEL:
			self._end_push_parallel()
		else:
			self._end_push()
		super().end_push()
	def _end_push_parallel(self):
		arr_l, arr_h, size_t = self.arr_l, self.arr_h, self.size_tour
		tours, hfm_queue = self.tours, self.hfm_queue
		MAX_LEV = 128
		arr_levs = regint.Tensor([MAX_LEV, MAX_DEG])
		arr_levs.assign_all(-1)
		size_levs = regint.Array(MAX_LEV)
		size_levs.assign_all(0)
		def real_comp(lev, i):
			tidx_ = arr_levs[lev][i]
			tidx1, tidx2, _, _, lev_par, _ = tours[tidx_]
			if ASSERT:
				runtime_error_if(lev_par != lev, "lev_par %s != %s", lev_par, lev)
			# really compare
			tour1, tour2 = tours[tidx1], tours[tidx2]
			wid1, wid2 = tour1[FIELDS.WID], tour2[FIELDS.WID]
			if ASSERT:
				runtime_error_if(wid1 < 0, "wid1 %s", wid1)
				runtime_error_if(wid2 < 0, "wid2 %s", wid2)
			r_win = key_l(arr_l[wid2]) < key_l(arr_l[wid1])# sbit
			r_win = r_win.reveal()
			# add_stat(OFS.Cmp)
			wid, lid = r_win.cond_swap(wid1, wid2)
			tours[tidx_][FIELDS.WID] = wid
			tours[tidx_][FIELDS.LID] = lid
			tours[tidx_][FIELDS.R_WIN] = r_win
		@if_(hfm_queue.size > 0)
		def _():
			# construct Huffman struct and save tours into levels
			# not really compare
			if DEBUG:
				print_ln("HT to build %s %s %s", self.size_l, size_t, hfm_queue.size)
			@while_do(lambda: hfm_queue.size >= 2)
			def _():
				tidx1, tidx2 = hfm_queue.pop(), hfm_queue.pop()
				tour1, tour2 = tours[tidx1], tours[tidx2]
				lev1, lev2 = tour1[FIELDS.R_WIN], tour2[FIELDS.R_WIN]
				lev_par = max(lev1, lev2) + 1
				d1, d2 = tour1[FIELDS.W], tour2[FIELDS.W]
				tours[size_t] = (tidx1, tidx2, -1, -1, lev_par, d1 + d2)
				hfm_queue.push(size_t)
				if DEBUG:
					print_ln("HT-push %s,%s->%s", lev1, lev2, lev_par)
				### save into associating level
				if ASSERT:
					runtime_error_if(lev_par >= MAX_LEV, "lev_par %s", lev_par)
				size_lev = size_levs[lev_par]
				if ASSERT:
					runtime_error_if(size_lev >= MAX_DEG, "size_levs %s", size_lev)
				arr_levs[lev_par][size_lev] = size_t
				size_levs[lev_par] += 1
				if DEBUG:
					print_arr(arr_levs[lev_par], size_lev, name="-L")
				###
				size_t.iadd(1)
			tidx = hfm_queue.pop()
			if DEBUG:
				print_ln("HT built %s %s", self.size_l ,size_t)
			# batch compare
			@for_range_opt(MAX_LEV)
			def _(lev_):
				size_lev, lev = size_levs[lev_], MemValue(lev_)
				@if_(size_lev == 0)
				def _():
					break_loop()
				SINGLE_THREAD = regint(MULTI_THREAD == 1)
				if DEBUG:
					print_ln("comp %s %s", lev_, size_lev)
					print_arr(arr_levs[lev], size_lev, name="L")
					print_ln("%s %s", size_lev < MULTI_THREAD, SINGLE_THREAD)
				@if_e((size_lev < MULTI_THREAD * 4).bit_or(SINGLE_THREAD))
				def _():
					@for_range_opt(size_lev)
					def _(i):
						real_comp(lev, i)
				@else_
				def _():
					@for_range_opt_multithread(MULTI_THREAD, size_lev)
					# @for_range(size_lev)
					def _(i):
						real_comp(lev, i)
				add_stat(OFS.Cmp, size_lev)
			arr_h.push(tidx)
	def _end_push(self):
		arr_l, arr_h, size_t = self.arr_l, self.arr_h, self.size_tour
		tours, hfm_queue = self.tours, self.hfm_queue
		if DEBUG:
			print_ln("end_push %s, %s", size_t, hfm_queue.size)
			hfm_queue.print("hfm_queue")
		@if_(hfm_queue.size > 0)
		def _():
			@while_do(lambda: hfm_queue.size >= 2)
			def _():
				tidx1, tidx2 = hfm_queue.pop(), hfm_queue.pop()
				tour1, tour2 = tours[tidx1], tours[tidx2]
				wid1, wid2 = tour1[FIELDS.WID], tour2[FIELDS.WID]
				r_win = key_l(arr_l[wid2]) < key_l(arr_l[wid1])# sbit
				r_win = r_win.reveal()
				add_stat(OFS.Cmp)
				wid, lid = r_win.cond_swap(wid1, wid2)
				d1, d2 = tour1[FIELDS.W], tour2[FIELDS.W]
				tours[size_t] = (tidx1, tidx2, wid, lid, r_win, d1 + d2)
				hfm_queue.push(size_t)
				size_t.iadd(1)
			tidx = hfm_queue.pop()
			arr_h.push(tidx)
		# print_ln("push arr_h[%s]", arr_h.size)

	def pop_l(self, tidx_top):
		arr_l, tours, path = self.arr_l, self.tours, self.path
		if ASSERT:
			runtime_error_if(tidx_top == -1, "pop_l")
		wid = tours[tidx_top][FIELDS.WID]
		top = copy(arr_l[wid])
		# go to the winner leaf and store the path
		path.clear()
		tidx = regint(tidx_top)
		@do_while
		def _():
			path.push(tidx)
			r_win = tours[tidx][FIELDS.R_WIN]
			tidx.update(tours[tidx][r_win])
			return r_win != -1
		# delete the winner
		path.pop()
		@if_e(path.size > 0)
		def _():
			# replace its par with its sib
			tidx_par = path.pop()
			r_win = tours[tidx_par][FIELDS.R_WIN]
			tidx_sib = tours[tidx_par][1 - r_win]
			tours[tidx_par] = tours[tidx_sib]
			wid = regint(tours[tidx_par][FIELDS.WID])
			@while_do(lambda: path.size > 0)
			def _():
				tidx = path.pop()
				tour = tours[tidx]
				r_win, lid = tour[FIELDS.R_WIN], tour[FIELDS.LID]
				if ASSERT:
					tour_sib = tours[tour[1 - r_win]]
					runtime_error_if(tour_sib[FIELDS.WID] != lid, "replay")
				op_win = key_l(arr_l[lid]) < key_l(arr_l[wid])# sbit
				op_win = op_win.reveal()
				add_stat(OFS.Cmp)
				tour[FIELDS.WID], tour[FIELDS.LID] = \
					op_win.cond_swap(wid, lid)
				tour[FIELDS.R_WIN] = r_win.bit_xor(op_win)
				wid.update(tour[FIELDS.WID])
		@else_
		def _():
			tidx_top.update(-1)
		return top

	def pop(self):
		arr_h, size = self.arr_h, self.size
		if ASSERT:
			runtime_error_if(arr_h.size <= 0, "pop1 %s", arr_h.size)
			runtime_error_if(size <= 0, "pop2 %s", size)
		tidx = arr_h.top()
		st_cmp = get_stat(OFS.Cmp)
		top = self.pop_l(tidx)
		en_cmp = get_stat(OFS.Cmp)
		add_stat(OFS.CmpPopL, en_cmp - st_cmp)
		size.iadd(-1)
		st_cmp_ = get_stat(OFS.Cmp)
		@if_e(tidx == -1)# empty
		def _():
			arr_h.pop()
		@else_
		def _():
			arr_h.replace_top(tidx)
		# print_ln("pop arr_h[%s]", arr_h.size)
		en_cmp_ = get_stat(OFS.Cmp)
		add_stat(OFS.CmpPopH, en_cmp_ - st_cmp_)
		return top

	def _print_tours(self):
		tours, arr_l, size_t = self.tours, self.arr_l, self.size_tour
		print_str("tours: ")
		@for_range(size_t)
		def _(i):
			@if_(i % 5 == 0)
			def _():
				print_str("\n%s: ", i)
			tour = copy(tours[i])
			for idx in [FIELDS.WID, FIELDS.LID]:
				tour[idx] = key_l(arr_l[tour[idx]]).reveal()
			print_str("%s, ", tour)
		print_ln("")
	def print(self):
		self.arr_h.print(name="arr_h")
		print_arr(self.arr_l, self.size_l, key=key_l, name="arr_l")
		# print_ln("arr_h: %s", self.arr_h.arr)
		self._print_tours()

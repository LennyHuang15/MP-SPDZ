from Compiler.types import *
from Compiler.library import print_ln, print_str, \
	if_, while_do, for_range, break_loop, runtime_error_if
from util_mpc import maybe_set, cond_swap_arr, add_stat, get_stat, print_stats, OFS

PLAIN = 1

class BaseHeap(object):
	def __len__(self):
		return self.size
	def clear(self):
		self.size.update(0)
	def begin_push(self, src):
		self.st_cmp = get_stat(OFS.Cmp)
	def end_push(self, dist_p=regint(0)):
		en_cmp = get_stat(OFS.Cmp)
		add_stat(OFS.CmpPush, en_cmp - self.st_cmp)
	def begin_pop(self):
		self.st_cmp = get_stat(OFS.Cmp)
	def end_pop(self):
		en_cmp = get_stat(OFS.Cmp)
		add_stat(OFS.CmpPop, en_cmp - self.st_cmp)

def _idx_par(ch, st=0):
	return st + (ch - st - 1) / 2
def _idx_lch(par, st=0):
	return st + (par - st) * 2 + 1

def sift_up(arr, pos, key, st=0):
	@while_do(lambda: pos > st)
	def _():
		par = _idx_par(pos, st)
		higher = key(arr[pos]) < key(arr[par])
		if(type(higher) is sintbit and PLAIN):
			higher = higher.reveal()
			add_stat(OFS.Cmp)
		cond_swap_arr(higher, arr, pos, par)
		# for i in range(arr.sizes[-1]):
		# 	arr[pos][i], arr[par][i] = higher.cond_swap(arr[pos][i], arr[par][i])
		add_stat(OFS.Heap)
		if(PLAIN):
			@if_(higher.bit_not())
			def _():
				break_loop()
		pos.update(par)

def sift_down(arr, par, size, key, st=0):
	en = st + size
	@while_do(lambda: True)
	def _():
		lch = _idx_lch(par, st)
		@if_(lch >= en)
		def _():
			break_loop()
		ch = lch
		@if_(lch < en - 1)
		def _():
			higher_rch = key(arr[lch+1]) < key(arr[lch])
			if(type(higher_rch) is sintbit and PLAIN):
				higher_rch = higher_rch.reveal()
				add_stat(OFS.Cmp)
			maybe_set(ch, higher_rch, lch + 1)
		higher = key(arr[ch]) < key(arr[par])
		if(type(higher) is sintbit and PLAIN):
			higher = higher.reveal()
			add_stat(OFS.Cmp)
		cond_swap_arr(higher, arr, ch, par)
		# for i in range(arr.sizes[-1]):
		# 	arr[ch][i], arr[par][i] = higher.cond_swap(arr[ch][i], arr[par][i])
		add_stat(OFS.Heap)
		if(PLAIN):
			@if_(higher.bit_not())
			def _():
				break_loop()
		par.update(ch)

def heapify(arr, size, key, st=0):
	par = _idx_par(st + size - 1, st)
	st_cmp = get_stat(OFS.Cmp)
	@for_range(par, st - 1, -1)
	def _(i):
		pos = regint(i)
		# print_str("%s: %s", key(arr[pos]), pos)
		# st_cmp1 = get_stat(OFS.Cmp)
		sift_down(arr, pos, size, key, st=st)
		# from util_mpc import print_arr
		# print_arr(arr, size, st, key, 'sift_down')
		# en_cmp1 = get_stat(OFS.Cmp)
		# print_ln("->%s (%s)", pos, en_cmp1 - st_cmp1)
	en_cmp = get_stat(OFS.Cmp)
	add_stat(OFS.CmpHeapify, en_cmp - st_cmp)

def check_heapified(arr, size, key, st=0):
	en = st + size
	last = _idx_par(st + size - 1, st)
	@for_range(st, last + 1)
	def _(par):
		lch = _idx_lch(par, st)
		@if_(lch >= en)
		def _():
			break_loop()
		key_l, key_p = key(arr[lch]), key(arr[par])
		higher = key_l < key_p
		if(type(higher) is sintbit):
			higher = higher.reveal()
		runtime_error_if(higher, "[%s]%s < [%s]%s", \
			lch, key_l, par, key_p)
		rch = lch + 1
		@if_(rch >= en)
		def _():
			break_loop()
		key_r = key(arr[rch])
		higher = key_r < key_p
		if(type(higher) is sintbit):
			higher = higher.reveal()
		runtime_error_if(higher, "[%s]%s < [%s]%s", \
			rch, key_r, par, key_p)


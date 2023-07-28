from Compiler.types import *
from Compiler.library import print_ln, if_, while_do, for_range, break_loop
from util_mpc import maybe_set, add_stat, get_stat, OFS

PLAIN = 1

class BaseHeap(object):
	def __len__(self):
		return self.size
	def begin_push(self, src):
		self.st_cmp = get_stat(OFS.Cmp)
	def end_push(self):
		en_cmp = get_stat(OFS.Cmp)
		add_stat(OFS.CmpPush, en_cmp - self.st_cmp)

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
		for i in range(arr.sizes[-1]):
			arr[pos][i], arr[par][i] = higher.cond_swap(arr[pos][i], arr[par][i])
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
		for i in range(arr.sizes[-1]):
			arr[ch][i], arr[par][i] = higher.cond_swap(arr[ch][i], arr[par][i])
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
	def _(pos):
		sift_down(arr, pos, size, key, st=st)
		# from util_mpc import print_arr
		# print_arr(arr, size, st, key, 'sift_down')
	en_cmp = get_stat(OFS.Cmp)
	add_stat(OFS.CmpHeapify, en_cmp - st_cmp)

## test heapify
# a = [10, 20, 25, 6, 12, 15, 4, 16]
# size = len(a)
# b = range(size)
# arr = sint.Tensor([2, size])
# arr[0].assign(a)
# arr[0] = -arr[0]
# arr[1].assign(b)
# arr = arr.transpose()
# heapify(arr, regint(size), 2, lambda el: el[0])
# arr = arr.transpose()
# print_ln("%s, %s", arr[0].reveal(), arr[1].reveal())

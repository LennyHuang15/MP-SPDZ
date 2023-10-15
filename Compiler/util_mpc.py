from Compiler.types import sint, regint, sintbit, Array
from Compiler.library import print_ln, print_str, public_input
from Compiler.library import for_range, while_do, break_loop, if_, if_e, else_
from Compiler.library import crash, runtime_error_if

N_PARTY = 2
DATA_BOUND = int(1e7)

def sint_tuple(*args):
	return tuple(sint(x) for x in args)
def plain_tuple(*args):
	return tuple(x for x in args)

def copy(a):
	if type(a) is Array:
		b = a.same_shape()
		b.assign(a)
	else:
		b = type(a)(a)
		b.update(a)
	return b
def alloc_arr(capacity, value_type=regint, WIDTH=None):
	if WIDTH is None:
		arr = value_type.Array(capacity)
	else:
		arr = value_type.Tensor([capacity, WIDTH])
	return arr

def maybe_set(var, cond, val):
	var.update(cond.if_else(val, var))
def cond_swap_arr(to_swap, arr, idx1, idx2):
	if type(arr[idx1]) is Array:
		for i in range(arr.sizes[-1]):
			arr[idx1][i], arr[idx2][i] = to_swap.cond_swap(arr[idx1][i], arr[idx2][i])
	else:
		assert type(arr[idx1]) is regint or type(arr[idx1]) is sint
		arr[idx1], arr[idx2] = to_swap.cond_swap(arr[idx1], arr[idx2])

def check_val(var, val):
	if type(var) is sint:
		var = var.reveal()
	runtime_error_if(var != val, "%s != %s", var, val)

def read_ints(fp):
    return [int(x) for x in fp.readline()[:-1].split(" ")]
def input_array(length):
	arr = regint.Array(length)
	@for_range(length)
	def _(i):
		arr[i] = public_input()
	return arr
def input_tensor(dim1, dim2):
	tensor = regint.Tensor([dim1, dim2])
	@for_range(dim1)
	def _(i):
		@for_range(dim2)
		def _(j):
			tensor[i][j] = public_input()
	return tensor
def read_graph(fn):
	import numpy as np
	G_np = np.loadtxt(fn, dtype=int, skiprows=1, delimiter=' ')
	with open(fn, 'r') as fp:
		st = fp.readline()
		NN, NE = [int(x) for x in st.split(' ')]
	return NN, NE, G_np

def print_regvec(vec, name, num):
	print_ln("%s[%d]: "% (name, len(vec)) + "%s " * num, *tuple(list(vec[:num])))
def print_arr(arr, size=None, st=0, key=None, name=''):
	if size is None:
		size = len(arr)
	if key is None:
		key = lambda x: x
	print_str("%s[%s]: ", name, size)
	@for_range(st, st + size)
	def _(i):
		val = key(arr[i])
		if type(val) is sint:
			val = val.reveal()
		print_str("%s ", val)
	print_ln("")

def print_tensor(tensor, size=None, dim=None):
	n, d = tensor.shape
	if size is not None:
		n = size
	if dim is not None:
		d = dim
	print_ln("%s %s", n, dim)
	@for_range(n)
	def _(i):
		@for_range(d)
		def _(j):
			print_str("%s ", tensor[i][j])
		print_ln("")
	
def lin_search(arr, st, en, offset, key):
	pos = regint(-1)
	@for_range(st, en)
	def _(i):
		@if_(arr[i][offset] == key)
		def _():
			pos.update(i)
			break_loop()
	return pos

def insertion_sort(arr, st, en, OFFSET=None, ws=None, ws_st=None):
	# print_ln("arr[%s]: %s", en-st, arr.transpose()[-1].get_part(0, 10).reveal())
	if ws is None:
		key_func = lambda i: arr[i][OFFSET]
	else:
		if ws_st is None:
			ws_st = st
		idx_ws = lambda i: i - st + ws_st
		key_func = lambda i: ws[idx_ws(i)]
		# print_ln("ws[%s]: %s", en-st, ws.get_part(0, 10))
	@for_range(st + 1, en)
	def _(i):
		value = arr[i].same_shape()
		value.assign(arr[i])
		key = key_func(i)
		j = i - 1
		@while_do(lambda: j >= st)
		def _():
			cond = key < key_func(j)
			if type(cond) is sintbit:
				cond = cond.reveal()
			@if_e(cond)
			def _():
				arr[j + 1] = arr[j]
				if ws is not None:
					ws[idx_ws(j+1)] = ws[idx_ws(j)]
				j.iadd(-1)
			@else_
			def _():
				break_loop()
		arr[j + 1] = value
		# print_ln("arr[%s]: %s", en-st, arr.transpose()[-1].get_part(0, 10).reveal())
		if ws is not None:
			ws[idx_ws(j+1)] = key
			# print_ln("ws[%s]: %s", en-st, ws.get_part(0, 10))

def obacktrace_path(S, T, exploreds, dists, N):
	ans, ans_dist, length = regint.Array(N), sint.Array(N), regint(0)
	nid = regint(T)
	@while_do(lambda: True)
	def _():
		ans[length], ans_dist[length] = nid, dists[nid]
		length.iadd(1)
		@if_(nid == S)
		def _():
			break_loop()
		nid.update(exploreds[nid])
	return ans, ans_dist, length

def vec_merge(vec, l, vec_rev, l_rev):
	@for_range(l / 2) # reverse the first half
	def _(i):
		vec[i], vec[l - i - 1] = vec[l - i - 1], vec[i]
	@for_range(l_rev)
	def _(i):
		vec[l + i] = vec_rev[i]
	return vec

from enum import IntEnum
OFS = IntEnum('OFS', ('Explore', 'Search', 'Update', 'Push', 'Pop', \
					'Heap', 'Cmp', 'CmpPush', 'CmpHeapify'), start=0)
stats = regint.Array(len(OFS))

def init_stats():
	stats.assign_all(0)
def add_stat(OFS, val=1):
	stats[OFS.value] += val
def get_stat(OFS):
	return stats[OFS.value]
def set_stat(OFS, val):
	stats[OFS.value] = val
def print_stats(ofs=None):
	ofss = OFS if ofs is None else [ofs]
	for ofs in ofss:
		print_str("%s[%s], ", ofs.name, stats[ofs.value])
	print_ln("")

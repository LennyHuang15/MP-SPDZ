from Compiler.types import sint, regint
from Compiler.library import print_ln, print_str, public_input
from Compiler.library import for_range, while_do, break_loop, if_, if_e, else_
from Compiler.library import crash, runtime_error_if

N_PARTY = 2
DATA_BOUND = int(1e7)

def sint_tuple(*args):
	return tuple(sint(x) for x in args)
def plain_tuple(*args):
	return tuple(x for x in args)

def maybe_set(var, cond, val):
	var.update(cond.if_else(val, var))

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

def lin_search(arr, st, en, offset, key):
	pos = regint(-1)
	@for_range(st, en)
	def _(i):
		@if_(arr[i][offset] == key)
		def _():
			pos.update(i)
			break_loop()
	return pos

def insertion_sort_inplace(arr, st, en, OFFSET=-1):
	@for_range(st + 1, en)
	def _(i):
		value = arr[i].same_shape()
		value.assign(arr[i])
		j = i - 1
		@while_do(lambda: j >= st)
		def _():
			@if_e(value[OFFSET] < arr[j][OFFSET])
			def _():
				arr[j + 1] = arr[j]
				j.iadd(-1)
			@else_
			def _():
				break_loop()
		arr[j + 1] = value
def insertion_sort(arr, st, en, ws, OBLIV=False):
	@for_range(st + 1, en)
	def _(i):
		value = arr[i].same_shape()
		value.assign(arr[i])
		key = ws[i]
		j = i - 1
		@while_do(lambda: j >= st)
		def _():
			cond_ = ws[j] > key
			cond = cond_.reveal() if OBLIV else cond_
			@if_e(cond)
			def _():
				arr[j + 1] = arr[j]
				ws[j + 1] = ws[j]
				j.iadd(-1)
			@else_
			def _():
				break_loop()
		arr[j+1], ws[j+1] = value, key

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

N_STATS = 7
OFS_EXPLORE, OFS_SEARCH, OFS_UPDATE, \
	OFS_PUSH, OFS_POP, OFS_HEAP, OFS_CMP = range(N_STATS)
stats = regint.Array(N_STATS)

def init_stats():
	stats.assign_all(0)
def add_stat(OFS):
	stats[OFS] += 1
def print_stats():
	print_str("explore[%s], ", stats[OFS_EXPLORE])
	print_str("search[%s], ", stats[OFS_SEARCH])
	print_str("update[%s], ", stats[OFS_UPDATE])
	print_str("push[%s], ", stats[OFS_PUSH])
	print_str("pop[%s], ", stats[OFS_POP])
	print_str("heap[%s], ", stats[OFS_HEAP])
	print_str("comp[%s], ", stats[OFS_CMP])
	print_ln("")

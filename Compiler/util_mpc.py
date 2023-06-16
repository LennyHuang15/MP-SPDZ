from Compiler.types import sint, regint
from Compiler.library import print_ln, while_do, break_loop, if_, for_range

N_PARTY = 2
DATA_BOUND = int(1e7)

def sint_tuple(*args):
	return tuple(sint(x) for x in args)

def maybe_set(var, cond, val):
	var.update(cond.if_else(val, var))

def read_ints(fp):
    return [int(x) for x in fp.readline()[:-1].split(" ")]

def print_regvec(vec, name, num):
	print_ln("%s[%d]: "% (name, len(vec)) + "%s " * num, *tuple(list(vec[:num])))

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
		vec[i], vec[l - i] = vec[l - i], vec[i]
	@for_range(l_rev)
	def _(i):
		vec[l + i] = vec_rev[i]
	return vec
	# vec_tot = vec.value_type.Array(size + size_rev)
	# vec_tot.assign_vector(vec.get_reverse_vector())
	# vec_tot.assign_vector(vec_rev, size)
	# return vec_tot

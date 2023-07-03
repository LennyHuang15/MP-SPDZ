from Compiler.types import *
from Compiler.library import for_range, print_ln, public_input, if_
from Compiler.library import crash, runtime_error_if, get_player_id
from Compiler.program import Program
import numpy as np
from util import max, argmax
from util_mpc import N_PARTY, print_regvec

'''Read graph in compile time (slow)'''
def read_graph(fn):
	G_np = np.loadtxt(fn, dtype=int, skiprows=1, delimiter=' ')
	with open(fn, 'r') as fp:
		st = fp.readline()
		NN, NE = [int(x) for x in st.split(' ')]
	return NN, NE, G_np
def save_graph(fn, G_np, NN, NE):
	np.savetxt(fn_g, G_np, fmt="%d", header="%d %d"%(NN, NE), comments="")

def tab2link_graph(NN, NE, G_np, rev=False):
	G_np = np.concatenate((G_np, np.arange(NE)[:, np.newaxis]), axis=-1)
	print(G_np.shape)
	sort_col_idx = 1 if rev else 0
	sort_col = G_np[:, sort_col_idx]
	idxs = sort_col.argsort()
	# print(G_np[idxs])
	link_edges = np.delete(G_np, sort_col_idx, axis=1)[idxs]
	nodes, cnts = np.unique(sort_col, return_counts=True)
	assert (np.diff(nodes) == 1).all()
	# print(nodes, cnts)
	cum = cnts.cumsum()
	assert cum[-1] == NE
	link_index = np.concatenate(([0], cum))
	# print(link_index.shape, link_index)
	link_index, link_edges = link2array(link_index, link_edges)
	return link_index, link_edges
def link2array(link_index_, link_edges_):
	link_index = regint.Array(len(link_index_))
	link_index.assign(link_index_.tolist())
	link_edges = regint.Tensor(link_edges_.shape)
	for i in range(len(link_edges_)):
		link_edges[i] = link_edges_[i].tolist()
	return link_index, link_edges

'''Read graph in runtime (fast but codes long)'''
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
def tensor2link_graph(NN, edges, rev=False):
	degs = regint.Array(NN)
	degs.assign_all(0)
	NE, dim = edges.shape
	# print_ln("tensor2link_graph: %s, %s, %s", NN, NE, dim)
	idx = 1 if rev else 0
	@for_range(NE)
	def _(eid):
		nid = edges[eid][idx]
		degs[nid] += 1
	# print_regvec(degs, "degs", 10)
	link_index = regint.Array(NN + 1)
	link_index[0] = 0
	@for_range(NN)
	def _(nid):
		link_index[nid+1] = link_index[nid] + degs[nid]
	# print_regvec(link_index, "link_index", 10)
	link_edges = regint.Tensor([NE, dim])
	@for_range(NE)
	def _(eid):
		nid = edges[eid][idx]
		pos = link_index[nid + 1] - degs[nid]
		link_edges[pos][0] = edges[eid][1 - idx]
		link_edges[pos][1:-1] = edges[eid][2:]
		link_edges[pos][-1] = eid
		degs[nid] -= 1
	# print_ln("link_edges[%s]: %s", link_edges.shape, link_edges[0])
	return link_index, link_edges
def load_link_graph(NN, NE, dim, offset=False):
	edges = input_tensor(NE, dim)
	if offset:
		@for_range(NE)
		def _(eid):
			edges[eid][:2] -= 1
	link_index, link_edges = tensor2link_graph(NN, edges)
	link_index_rev, link_edges_rev = tensor2link_graph(NN, edges, rev=True)
	return link_index, link_edges, link_index_rev, link_edges_rev

def _load_array_parties(size):
	parties_arr = sint.Matrix(N_PARTY, size)
	for p in range(N_PARTY):
		parties_arr[p].input_from(p)
	personal_arrs = [parties_arr[p].reveal_to(p) for p in range(N_PARTY)]
	return parties_arr, personal_arrs
def load_weights(E):
	parties_weights, parties_ws = _load_array_parties(E)
	# parties_weights = parties_weights.transpose()
	weights = sint.Array(E)
	weights.assign(parties_weights[0][:])
	@for_range(1, N_PARTY)
	def _(p):
		weights[:] += parties_weights[p][:]
	# @for_range(E)
	# def _(eid):
	# 	weights[eid] = sum(parties_weights[eid])# / N_PARTY
	# weights /= N_PARTY
	return weights#, parties_ws
		
class Graph(object):
	def __init__(self):
		self.N, self.E = None, None

	def _load_compile(self, fn):
		NN, NE, G_np = read_graph(fn)
		self.N, self.E = NN, NE
		G_np[:,:2] -= 1
		self.link_index, self.link_edges = tab2link_graph(NN, NE, G_np)
		self.link_index_rev, self.link_edges_rev = tab2link_graph(NN, NE, G_np, rev=True)

	def load(self, fn=None, NN=None, NE=None, dim=None, E_new=None):
		print_ln("Loading graph from %s" % fn)
		if fn is not None:
			self._load_compile(fn)
		else:
			self.N, self.E = NN, NE
			self.link_index, self.link_edges, self.link_index_rev, \
				self.link_edges_rev = load_link_graph(NN, NE, 3, True)
		print_ln("Graph loaded: %d nodes, %d edges" % (self.N, self.E))
		self.weights = load_weights(NE)
		print_ln("Weights loaded: %s", self.weights.shape)

		self.lmemb, self.ch = None, None
		if dim is not None and dim > 0:
			self.dim = dim
			self.lmemb = input_tensor(NN, dim)
			print_ln("Lmemb loaded: %s", self.lmemb.shape)
		if E_new is not None and E_new > 0:
			levels = input_array(NN)
			ch_index, ch_edges, ch_index_rev, \
				ch_edges_rev = load_link_graph(NN, E_new, 4)
			print_ln("CH loaded: %s shortcuts", ch_edges.shape)
			weights_ch = load_weights(E_new)
			print_ln("CH weights loaded: %s", weights_ch.shape)
			self.ch = (levels, ch_index, ch_edges, \
				ch_index_rev, ch_edges_rev, weights_ch)
			# for reordering neighbors and lazy adding
			links, links_rev = [regint.Tensor([E_new, 4]) for _ in range(2)]
			links.assign(ch_edges)
			links_rev.assign(ch_edges_rev)
			pws, ows = regint.Array(E_new), sint.Array(E_new)
			pws_r, ows_r = regint.Array(E_new), sint.Array(E_new)
			poss, poss_r = regint.Array(NN), regint.Array(NN)
			self.chs = (links, pws, ows, poss)
			self.chs_r = (links_rev, pws_r, ows_r, poss_r)

	def _build_ST(self, S, T):
		self.S, self.T = S, T
		NN, dim = self.N, self.dim
		# dist table of (S,v) and (v,T)
		# self._build_static_table(S, T)
		self.static_table = input_tensor(2, NN)
		_, self.dynamic_table = _load_array_parties(2 * NN)
		# dynamic LT embedding
		if dim is not None and dim > 0:
			_, self.parties_emb = _load_array_parties(NN * dim)
		# pre-calculate and store the dist(S,T)
		self.dist_ST = self.dist_est_static(S, T, True)
		self.dist_ST_ps = [self.dist_est_dyn(S, T, p, True) for p in range(N_PARTY)]

	def _build_static_table(self, S, T):
		N = self.N
		from dijk3 import SSSP as SP
		self.static_table = regint.Tensor([2, N])
		for idx in range(2):
			src = S if idx == 0 else T
			link_index = self.link_index if idx == 0 else self.link_index_rev
			link_edges = self.link_edges if idx == 0 else self.link_edges_rev
			ans, ans_dist, size_ans = SP(self, src, static_weights=True, \
				link_index=link_index, link_edges=link_edges)
			crash(size_ans != N)
			@for_range(N)
			def _(i):
				nid, dist = ans[i], ans_dist[i]
				self.static_table[idx][nid] = dist
		print_ln("Static dist table built: %s", self.static_table.shape)
	
	def _dist_est_static_lt(self, S, T):
		max_dist = max(self.lmemb[T][:] - self.lmemb[S][:])
		return max_dist.max(0)
	def _dist_est_dynamic_lt(self, S, T, p):
		lmid = argmax(self.lmemb[T][:] - self.lmemb[S][:])
		dim, emb_p = self.dim, self.parties_emb[p]
		dist = emb_p[T*dim + lmid] - emb_p[S*dim + lmid]
		return max(dist, 0)

	def _dist_est_static_sp(self, S, T, from_S):
		idx, dst = (0, T) if from_S else (1, S)
		return self.static_table[idx][dst]
	def _dist_est_dynamic_sp(self, S, T, p, from_S):
		idx = T if from_S else (self.N + S)
		return self.dynamic_table[p][idx]

	def dist_est_static(self, S, T, from_S=None):
		# return 0
		# return self._dist_est_static_lt(S, T)
		return self._dist_est_static_sp(S, T, from_S)
	def dist_est_dyn(self, S, T, p, from_S=None):
		# return self._dist_est_dynamic_lt(S, T, p)
		return self._dist_est_dynamic_sp(S, T, p, from_S)
	# def dist_est(self, S, T, from_S=None):
	# 	return self.dist_est_static(S, T, from_S)
	# 	return self.dist_est_dyn(S, T, from_S)
		# a = self._dist_est_static_lt(S, T) * N_PARTY
		# b = self._dist_est_dynamic_lt(S, T)
		# print_ln("%s->%s: %s vs %s", S, T, a, b.reveal())
		# b = self._dist_est_static_sp(S, T, from_S)
		# runtime_error_if(a > b, "%s->%s: %s > %s", S, T, a, b)
		# return b
	
	def pot_func_bidir(self, S, T, v, is_for):
		if self.lmemb is None:
			return 0
		return self.pot_func_bidir_static(S, T, v, is_for)
		# return self.pot_func_bidir_dyn(S, T, v, is_for)
	def pot_func_bidir_static(self, S, T, v, is_for):
		pi_f = self.dist_est_static(v, T, False)
		pi_r = self.dist_est_static(S, v, True)
		pi_st = self.dist_ST # self.dist_est(S, T)
		dp = (pi_f - pi_r) if is_for else (pi_r - pi_f)
		return (dp + pi_st) * N_PARTY / 2
	def pot_func_bidir_dyn(self, S, T, v, is_for):
		dists = sint.Array(N_PARTY)
		for p in range(N_PARTY):
			dists[p] = self._pot_func_p(S, T, v, is_for, p)
		return sum(dists)
	def _pot_func_p(self, S, T, v, is_for, p):
		pi_f = self.dist_est_dyn(v, T, p, False)
		pi_r = self.dist_est_dyn(S, v, p, True)
		pi_st = self.dist_ST_ps[p]
		dp = (pi_f - pi_r) if is_for else (pi_r - pi_f)
		return sint((dp + pi_st) / 2)

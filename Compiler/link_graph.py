from Compiler.types import *
from Compiler.library import for_range, while_do, if_, if_e, else_, break_loop
from Compiler.library import print_ln, print_ln_to, crash, runtime_error_if, get_player_id
from Compiler.program import Program
from util import max, argmax
from util_mpc import N_PARTY, print_regvec, input_array, input_tensor, print_tensor

NO_POT = 1
USE_LM = 0
DYN_POT = 0

MAX_DEG = 512# to be used in HT-heap
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
		runtime_error_if(degs[nid] > MAX_DEG, \
			"max_deg %s > %s", degs[nid], MAX_DEG)
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
	weights = sint.Array(E)
	weights.assign(parties_weights[0][:])
	@for_range(1, N_PARTY)
	def _(p):
		weights[:] += parties_weights[p][:]
	return weights#, parties_ws
		
class Graph(object):
	def __init__(self):
		self.N, self.E = None, None

	def load(self, NN=None, NE=None, dim=None, E_new=None):
		self.N, self.E = NN, NE
		self.link_index, self.link_edges, self.link_index_rev, \
			self.link_edges_rev = load_link_graph(NN, NE, 3, True)
		print_ln("Graph loaded: %d nodes, %d edges" % (self.N, self.E))
		self.weights = load_weights(NE)
		print_ln("Weights loaded: %s", self.weights.shape)

		self.lmemb, self.ch = None, None
		# static LT embedding
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
			self.E_new = E_new
			# for reordering neighbors and lazy adding
			links, links_rev = [regint.Tensor([E_new, 4]) for _ in range(2)]
			links.assign(ch_edges)
			links_rev.assign(ch_edges_rev)
			pws, ows = regint.Array(E_new), sint.Array(E_new)
			pws_r, ows_r = regint.Array(E_new), sint.Array(E_new)
			poss, poss_r = regint.Array(NN), regint.Array(NN)
			self.chs = (links, pws, ows, poss)
			self.chs_r = (links_rev, pws_r, ows_r, poss_r)
		# dynamic LT embedding
		if dim is not None and dim > 0:
			_, self.parties_emb = _load_array_parties(NN * dim)

	def _build_ST(self, S, T):
		self.S, self.T = S, T
		NN, dim = self.N, self.dim
		# dist table of (S,v) and (v,T)
		self.static_table = input_tensor(2, NN)
		_, self.dynamic_table = _load_array_parties(2 * NN)
		# pre-calculate and store the dist(S,T)
		self.dist_ST = self.dist_est_static(S, T, True)
		if DYN_POT:
			self.dist_ST_ps = [self.dist_est_dyn(S, T, p, True) for p in range(N_PARTY)]
	
	def build_ch(self, revealing=True):
		NN, NE = self.N, self.E
		link_index, link_edges = self.link_index, self.link_edges
		levels, node_levels = input_array(NN), input_array(NN)
		print_ln("Building CH: %s, %s" % (NN, levels.shape))
		weights = self.weights
		if revealing:
			weights = weights.reveal()

		MAX_CH = NN * 16
		# (src, dst, min, w, pt_next, pt_next_rev)
		ch_edges, sz = regint.Tensor([MAX_CH, 6]), regint(0)
		ws = weights.value_type.Array(MAX_CH)
		pts, pts_rev = [regint.Tensor([NN, 2]) for _ in range(2)]
		pts.assign_all(-1)
		pts_rev.assign_all(-1)
		def _add_pt(pts, nid, nid_, is_rev=0):
			@if_(pts[nid][0] < 0)
			def _():
				pts[nid][0] = sz
			pre_tail = pts[nid][1]
			@if_(pre_tail >= 0)
			def _():
				ch_edges[pre_tail][-2 + is_rev] = sz
			pts[nid][1] = sz
		def add_edge(src, dst, mid, w):
			runtime_error_if(sz >= MAX_CH, "sz %s >= %s", sz, MAX_CH)
			ch_edges[sz] = (src, dst, mid, w, -1, -1)
			ws[sz] = w
			_add_pt(pts, src, dst, is_rev=0)
			_add_pt(pts_rev, dst, src, is_rev=1)
			sz.iadd(1)
		def lin_search(st, en, key, is_rev=0):
			# print_ln("search %s %s %s", st, en, key)
			runtime_error_if(st == -1, "st %s", st)
			# runtime_error_if((en < 0).bit_or(en >= sz), "en %s", en)
			pt = regint(st)
			@while_do(lambda: True)
			def _():
				runtime_error_if(pt < 0, "pt = %s", pt)
				runtime_error_if(pt >= sz, "pt = %s >= %s", pt, sz)
				pt_next = ch_edges[pt][-2 + is_rev]
				@if_(ch_edges[pt][1 - is_rev] == key)
				def _():
					break_loop()
				@if_(pt == en)
				def _():
					pt.update(-1)
					break_loop()
				pt.update(pt_next)
			return pt

		# begin with the origin edges
		@for_range(NN)
		def _(nid):
			@for_range(link_index[nid], link_index[nid+1])
			def _(eid):
				dst, w_p, eid_ = link_edges[eid][:]
				w = weights[eid_]
				if revealing:
					w = w.reveal()
				add_edge(nid, dst, -1, w)
		runtime_error_if(sz != NE, "sz %s != %s", sz, NE)
		# print_ln("pts: %s %s %s", pts[0], pts[1], pts[2])
		# for i in range(10):
		# 	print_ln("%s", ch_edges[i])
		# # pos = lin_search(ch_edges, 2, 2, 2)
		# # print_ln("pos: %s", pos)
		# return

		# contract and add shortcuts
		n_visit, n_sc = [regint(0) for _ in range(2)]
		NSTEP = NN
		STEP, STEP_vs = NN // NSTEP, 20000
		milestone = regint(0)
		@for_range(NN)
		def _(lev):
			# print process
			# @if_(lev % STEP == 0)
			@if_(n_visit >= milestone)
			def _():
				print_ln("%s/%s: %s,%s", lev, NN, n_visit, n_sc)
				milestone.iadd(STEP_vs)
			# begin
			nid = node_levels[lev]
			ieid = pts_rev[nid][0]
			@while_do(lambda: ieid >= 0)
			def _():
				src, dst_, imid, iw_p, _, inext = ch_edges[ieid]
				runtime_error_if(dst_ != nid, "dst_ %s != %s", dst_, nid)
				iw = ws[ieid]
				@if_(levels[src] > lev)
				def _():
					# use the deg before adding shortcuts is enough
					s_st, s_en = pts[src]
					oeid = pts[nid][0]
					@while_do(lambda: oeid >= 0)
					def _():
						src_, dst, omid, ow_p, onext, _ = ch_edges[oeid]
						runtime_error_if(src_ != nid, "src_ %s != %s", src_, nid)
						ow = ws[oeid]
						@if_((src != dst).bit_and(levels[dst] > lev))
						def _():
							# print_ln("visit %s->%s", src, dst)
							n_visit.iadd(1)
							d_st, d_en = pts_rev[dst]
							# add/update shortcut (s, d) = iw + ow
							w_sc = iw + ow
							pos = lin_search(s_st, s_en, dst, 0)
							pos_rev = lin_search(d_st, d_en, src, 1)
							# print_ln("pos: %s, %s", pos, pos_rev)
							runtime_error_if((pos == -1) != (pos_rev == -1))
							@if_e(pos == -1)
							def _():
								add_edge(src, dst, nid, w_sc)
								n_sc.iadd(1)
							@else_
							def _():
								to_update = w_sc < ws[pos]# ch_edges[pos][2]
								if type(to_update) is sintbit:
									to_update = to_update.reveal()
								@if_(to_update)
								def _():
									ch_edges[pos][2:4] = (nid, w_sc)
									ws[pos] = w_sc
						oeid.update(onext)
				ieid.update(inext)
		print_ln("Contraction finished, %s visited", n_visit)
		print_ln("%s shortcuts added, %s->%s", n_sc, NE, sz)
		runtime_error_if(sz != NE + n_sc)
		# output
		print_ln("### CH tensor")
		print_tensor(ch_edges, sz, 4)# s, t, mid

	def _dist_est_static_lt(self, S, T):
		max_dist = max(self.lmemb[T][:] - self.lmemb[S][:])
		return max_dist.max(0)
	def _dist_est_dynamic_lt(self, S, T, p):
		lmid = argmax(self.lmemb[T][:] - self.lmemb[S][:])
		dim, emb_p = self.dim, self.parties_emb[p]
		dist = emb_p[T*dim + lmid] - emb_p[S*dim + lmid]
		return dist
		# return max(dist, 0)

	def _dist_est_static_sp(self, S, T, from_S):
		idx, dst = (0, T) if from_S else (1, S)
		return self.static_table[idx][dst]
	def _dist_est_dynamic_sp(self, S, T, p, from_S):
		idx = T if from_S else (self.N + S)
		return self.dynamic_table[p][idx]

	def dist_est_static(self, S, T, from_S=None):
		if NO_POT:
			return regint(0)
		elif USE_LM:
			return self._dist_est_static_lt(S, T)
		else:
			return self._dist_est_static_sp(S, T, from_S)
	def dist_est_dyn(self, S, T, p, from_S=None):
		if USE_LM:
			return self._dist_est_dynamic_lt(S, T, p)
		else:
			return self._dist_est_dynamic_sp(S, T, p, from_S)
	# def dist_est(self, S, T, from_S=None):
	# 	return self.dist_est_static(S, T, from_S)
	# 	return self.dist_est_dyn(S, T, from_S)
	
	def pot_func_bidir(self, S, T, v, is_for):
		if self.lmemb is None:
			return 0
		elif DYN_POT:
			return self.pot_func_bidir_dyn(S, T, v, is_for)
		else:
			return self.pot_func_bidir_static(S, T, v, is_for)
	def pot_func_bidir_static(self, S, T, v, is_for):
		pi_f = self.dist_est_static(v, T, False)
		pi_r = self.dist_est_static(S, v, True)
		pi_st = self.dist_ST # self.dist_est(S, T)
		dp = (pi_f - pi_r) if is_for else (pi_r - pi_f)
		return (dp + pi_st) * N_PARTY / 2
	def pot_func_bidir_dyn(self, S, T, v, is_for):
		dists = sint.Array(N_PARTY)
		for p in range(N_PARTY):
			dists[p] = sint(self._pot_func_p(S, T, v, is_for, p))
		return sum(dists)
	def _pot_func_p(self, S, T, v, is_for, p):
		pi_f = self.dist_est_dyn(v, T, p, False)
		pi_r = self.dist_est_dyn(S, v, p, True)
		pi_st = self.dist_ST_ps[p]
		dp = (pi_f - pi_r) if is_for else (pi_r - pi_f)
		return (dp + pi_st) // 2

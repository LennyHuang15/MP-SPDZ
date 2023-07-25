from Compiler.types import *
from Compiler.library import print_ln, print_ln_if, if_, if_e, else_
from Compiler.library import for_range, do_while, while_do, break_loop
from util_mpc import *
from link_graph import Graph
from heap import Heap

# TERM_EARLY = 1
LAZY_EDGE = 0
DEBUG = 0
ASSERT = 1

def _explore_node(graph, S, T, min_dist, obest_bridge, \
		expand_s, pq, exploreds, dists, exploreds_op, dists_op, \
		nid, edge, dist):
	levels, weights, lmemb = graph.ch[0], graph.ch[-1], graph.lmemb
	nid_, _, w, wid = edge
	if DEBUG:
		print_ln("exploring %s,%s,%s", nid_, w, dist.reveal())
	@if_(exploreds[nid_] < 0)
	def _():
		up_level = levels[nid] < levels[nid_]
		explored_op = exploreds_op[nid_] >= 0
		@if_(explored_op.bit_or(up_level))
		def _():
			if LAZY_EDGE:
				dist_ = dist + w
				if lmemb is not None:
					pot_dist_ = graph.pot_func_bidir(S, T, nid_, expand_s)
					dist_.iadd(pot_dist_)
				if DEBUG:
					print_ln("add %s, %s, %s", dist_.reveal(), -nid-1, nid_)
				pq.push(sint_tuple(dist_, -nid-1, nid_))
				add_stat(OFS_PUSH)
			else:
				add_stat(OFS_SEARCH)
				dist_ = dist + weights[wid]
				@if_(explored_op)
				def _():
					bi_dist_ = dist_ + dists_op[nid_]
					to_update = (bi_dist_ < min_dist)
					maybe_set(min_dist, to_update, bi_dist_)
					maybe_set(obest_bridge[1 - expand_s], to_update, nid)
					maybe_set(obest_bridge[expand_s], to_update, nid_)
					add_stat(OFS_UPDATE)
				@if_(up_level)
				def _():
					if lmemb is not None:
						pot_dist_ = graph.pot_func_bidir(S, T, nid_, expand_s)
						dist_.iadd(pot_dist_)
					if DEBUG:
						print_ln("add %s, %s, %s", dist_.reveal(), nid, nid_)
					pq.push(sint_tuple(dist_, nid, nid_))
					add_stat(OFS_PUSH)

def _expand_side(graph, S, T, min_dist, obest_bridge, \
		expand_s, pq, link_index, link_edges, \
		exploreds, dists, exploreds_op, dists_op):
	dist, opre_nid, onid = pq.pop()
	add_stat(OFS_POP)
	pre_nid, nid = opre_nid.reveal(), onid.reveal()
	if DEBUG:
		c = 'S' if expand_s else 'T'
		print_ln("top%s[%s]: %s, %s, %s", c, exploreds[nid]>=0, pre_nid, nid, dist.reveal())
	@if_(exploreds[nid] < 0) # to explore
	def _():
		add_stat(OFS_EXPLORE)
		levels, weights, lmemb = graph.ch[0], graph.ch[-1], graph.lmemb
		if lmemb is not None:
			pot_dist = graph.pot_func_bidir(S, T, nid, expand_s)
			dist.iadd(-pot_dist)
		@if_e(pre_nid < 0)
		def _():
			is_lazy = MemValue(LAZY_EDGE)
			if ASSERT:
				crash(is_lazy.bit_not())
			nid_ = regint(nid)
			nid.update(-pre_nid - 1)
			up_level = levels[nid] < levels[nid_]
			explored_op = exploreds_op[nid_] >= 0
			@if_(explored_op.bit_or(up_level))
			def _():
				eid = lin_search(link_edges, link_index[nid], \
					link_index[nid+1], 0, nid_)
				if ASSERT:
					crash(eid == -1)
				add_stat(OFS_SEARCH)
				_, _, w, wid = link_edges[eid]
				w_ = weights[wid]
				# crash((w_ < w).reveal())
				dist_ = dist + w_ - w
				@if_(explored_op)
				def _():
					bi_dist_ = dist_ + dists_op[nid_]
					to_update = (bi_dist_ < min_dist)
					maybe_set(min_dist, to_update, bi_dist_)
					maybe_set(obest_bridge[1 - expand_s], to_update, nid)
					maybe_set(obest_bridge[expand_s], to_update, nid_)
					add_stat(OFS_UPDATE)
				@if_(up_level)
				def _():
					if lmemb is not None:
						pot_dist = graph.pot_func_bidir(S, T, nid_, expand_s)
						dist_.iadd(pot_dist)
					pq.push(sint_tuple(dist_, nid, nid_))
					add_stat(OFS_PUSH)
		@else_
		def _():
			exploreds[nid], dists[nid] = pre_nid, dist
			@for_range(link_index[nid], link_index[nid+1])
			def _(eid):
				_explore_node(graph, S, T, min_dist, obest_bridge, \
					expand_s, pq, exploreds, dists, exploreds_op, dists_op, \
					nid, link_edges[eid], dist)
	
def SPSP(graph, S, T):
	if DEBUG:
		print_ln("SPSP3: %s -> %s", S, T)
	@if_(S == T)
	def _():
		ans, ans_dist = regint.Array(1), sint.Array(1)
		ans[0], ans_dist[0] = S, 0
		return ans, ans_dist, regint(1)
	N, E = graph.N, graph.E
	levels, link_index_for, link_edges_for, \
		link_index_rev, link_edges_rev, weights = graph.ch

	exploreds_s, dists_s = regint.Array(N), sint.Array(N)
	exploreds_t, dists_t = regint.Array(N), sint.Array(N)
	for vec in [exploreds_s, dists_s, exploreds_t, dists_t]:
		vec.assign_all(-1)
	qs, qt = Heap(N, 3), Heap(N, 3)
	p_st = graph.pot_func_bidir(S, T, S, True)
	qs.push(sint_tuple(p_st, N, S))
	qt.push(sint_tuple(p_st, N, T))

	min_dist, obest_bridge = sint(DATA_BOUND), sint_tuple(-1, -1)
	expand_s = MemValue(False)
	@while_do(lambda: True)
	def _():
		dist_top = qs.top()[0] + qt.top()[0] - p_st
		@if_((dist_top >= min_dist).reveal())
		def _():
			datas = [qs.top()[0], qt.top()[0], p_st, dist_top, min_dist]
			if DEBUG:
				print_ln("break, %s,%s,%s, %s>=%s", *[x.reveal() for x in datas])
			break_loop()
		expand_s.write(expand_s.bit_not())
		empty_s, empty_t = (qs.size == 0), (qt.size == 0)
		@if_(empty_s.bit_or(empty_t))
		def _():
			expand_s.write(empty_t)
		@if_e(expand_s)
		def _():
			_expand_side(graph, S, T, min_dist, obest_bridge, \
				True, qs, link_index_for, link_edges_for, \
				exploreds_s, dists_s, exploreds_t, dists_t)
		@else_ # expand t
		def _():
			_expand_side(graph, S, T, min_dist, obest_bridge, \
				False, qt, link_index_rev, link_edges_rev, \
				exploreds_t, dists_t, exploreds_s, dists_s)
	best_s, best_t = [x.reveal() for x in obest_bridge]
	if ASSERT:
		crash((best_s == -1).bit_or(best_t == -1))
	ans_s, ans_dist_s, len_s = obacktrace_path(S, best_s, exploreds_s, dists_s, N)
	ans_t, ans_dist_t, len_t = obacktrace_path(T, best_t, exploreds_t, dists_t, N)
	ans = vec_merge(ans_s, len_s, ans_t, len_t)
	ans_dist_t[:] = min_dist - ans_dist_t[:]
	ans_dist = vec_merge(ans_dist_s, len_s, ans_dist_t, len_t)
	return ans, ans_dist, len_s + len_t

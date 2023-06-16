from Compiler.types import *
from Compiler.library import print_ln, if_, if_e, else_, print_ln_if
from Compiler.library import for_range, do_while, while_do, break_loop
from util_mpc import *
from link_graph import Graph
from heap import Heap

def _expand_side(graph, weights, S, T, min_dist, obest_bridge, \
		expand_s, pq, link_index, link_edges, \
		exploreds, dists, exploreds_op, dists_op):
	# print_ln("pop from %s", pq.size)
	dist, opre_nid, onid = pq.pop()
	pre_nid, nid = opre_nid.reveal(), onid.reveal()
	# print_ln("top: %s, %s, exp%s", pre_nid, nid, exploreds[nid])
	lmemb = graph.lmemb
	if lmemb is not None:
		dist.iadd(-graph.pot_func_bidir(S, T, nid, expand_s))
	@if_(exploreds[nid] < 0) # unexplored, else continue
	def _():
		exploreds[nid], dists[nid] = pre_nid, dist
		# print_ln("exploring %s -> %s", link_index[nid], link_index[nid+1])
		@for_range(link_index[nid], link_index[nid+1])
		def _(eid):
			nid_, w, wid = link_edges[eid]
			# print_ln("add %s", (nid_, w, wid))
			@if_(exploreds[nid_] < 0)
			def _():
				dist_ = dist + weights[wid]
				@if_(exploreds_op[nid_] >= 0)
				def _():
					bi_dist_ = dist_ + dists_op[nid_]
					to_update = (bi_dist_ < min_dist)
					maybe_set(min_dist, to_update, bi_dist_)
					# min_dist = to_update.if_else(bi_dist_, min_dist)
					maybe_set(obest_bridge[1 - expand_s], to_update, nid)
					maybe_set(obest_bridge[expand_s], to_update, nid_)
					# obest_bridge[0] = to_update.if_else(nid, obest_bridge[0])
					# obest_bridge = expand_s.cond_swap(*obest_bridge)
				if lmemb is not None:
					dist.iadd(graph.pot_func_bidir(S, T, nid_, expand_s))
				pq.push(sint_tuple(dist_, nid, nid_))
				# print_ln("push to %s", pq.size)

def SPSP0(graph, S, T):
	print_ln("SPSP0: %s -> %s", S, T)
	@if_(S == T)
	def _():
		ans, ans_dist = regint.Array(1), sint.Array(1)
		ans[0], ans_dist[0] = S, 0
		return ans, ans_dist, regint(1)
	N, E = graph.N, graph.E
	link_index_for, link_edges_for = graph.link_index, graph.link_edges
	link_index_rev, link_edges_rev = graph.link_index_rev, graph.link_edges_rev
	weights = graph.weights

	exploreds_s, dists_s = regint.Array(N), sint.Array(N)
	exploreds_t, dists_t = regint.Array(N), sint.Array(N)
	for vec in [exploreds_s, dists_s, exploreds_t, dists_t]:
		vec.assign_all(-1)
	p_st = graph.pot_func_bidir(S, T, S, True)
	qs, qt = Heap(N, 3), Heap(N, 3)
	qs.push(sint_tuple(p_st, N, S))
	qt.push(sint_tuple(p_st, N, T))

	min_dist, obest_bridge = sint(DATA_BOUND), sint_tuple(-1, -1)
	@while_do(lambda: True)
	def _():
		dist_top = qs.top()[0] + qt.top()[0] - p_st
		@if_((dist_top >= min_dist).reveal())
		def _():
			break_loop()
		expand_s = (qs.size < qt.size)
		@if_e(expand_s)
		def _():
			# print_ln("expand s")
			_expand_side(graph, weights, S, T, min_dist, obest_bridge, \
				1, qs, link_index_for, link_edges_for, \
				exploreds_s, dists_s, exploreds_t, dists_t)
		@else_ # expand t
		def _():
			# print_ln("expand t")
			_expand_side(graph, weights, S, T, min_dist, obest_bridge, \
				0, qt, link_index_rev, link_edges_rev, \
				exploreds_t, dists_t, exploreds_s, dists_s)
	best_s, best_t = [x.reveal() for x in obest_bridge]
	crash((best_s == -1).bit_or(best_t == -1))
	ans_s, ans_dist_s, len_s = obacktrace_path(S, best_s, exploreds_s, dists_s, N)
	ans_t, ans_dist_t, len_t = obacktrace_path(T, best_t, exploreds_t, dists_t, N)
	ans = vec_merge(ans_s, len_s, ans_t, len_t)
	@for_range(len_t)
	def _(i):
		ans_dist_t[i] = min_dist - ans_dist_t[i]
	ans_dist = vec_merge(ans_dist_s, len_s, ans_dist_t, len_t)
	return ans, ans_dist, len_s + len_t

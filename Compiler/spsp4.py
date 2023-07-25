from Compiler.types import *
from Compiler.library import print_ln, if_, if_e, else_, print_ln_if
from Compiler.library import for_range, do_while, while_do, break_loop
from util_mpc import *
from link_graph import Graph
from heap import Heap

# TERM_EARLY = 1
# LAZY_EDGE = 1
DEBUG = 0
ASSERT = 1

def _explore_next_virt(poss, link_index, nid, dists, \
		links, exploreds, exploreds_op, levels, pq):
	pos, en = poss[nid], link_index[nid+1]
	@while_do(lambda: pos < en)
	def _():
		nid_, _, dist_p, wid = links[pos]
		@if_(exploreds[nid_] < 0)
		def _():
			up_level = levels[nid] < levels[nid_]
			explored_op = exploreds_op[nid_] >= 0
			@if_(explored_op.bit_or(up_level))
			def _():
				add_stat(OFS_SEARCH)
				dist_ = dists[nid] + dist_p
				if DEBUG:
					print_ln("add virt: %s,%s,%s", -nid-1, nid_, dist_.reveal())
				pq.push(sint_tuple(dist_, -nid-1, nid_))
				add_stat(OFS_PUSH)
				pos.iadd(1)
				break_loop()
		pos.iadd(1)
	poss[nid] = pos

def _expand_side(graph, S, T, min_dist, obest_bridge, \
		expand_s, pq, link_index, link_edges, chs, \
		exploreds, dists, exploreds_op, dists_op):
	dist, opre_nid, onid = pq.pop()
	pre_nid, nid = opre_nid.reveal(), onid.reveal()
	if DEBUG:
		c = 'S' if expand_s else 'T'
		print_ln("top%s[%s]: %s, %s, %s", c, exploreds[nid]>=0, pre_nid, nid, dist.reveal())
	add_stat(OFS_EXPLORE)
	@if_(exploreds[nid] < 0) # to explore
	def _():
		levels, weights, lmemb = graph.ch[0], graph.ch[-1], graph.lmemb
		links, pws, ows, poss = chs
		# if lmemb is not None:
		# 	pot_dist = graph.pot_func_bidir(S, T, nid, expand_s)
		# 	dist.iadd(-pot_dist)
		@if_e(pre_nid < 0)
		def _():
			if lmemb is not None:
				pot_dist = graph.pot_func_bidir_static(S, T, nid, expand_s)
				dist.iadd(-pot_dist)
			nid_ = regint(nid)
			nid.update(-pre_nid - 1)
			if ASSERT:
				crash(exploreds[nid] < 0)
			up_level = levels[nid] < levels[nid_]
			# crash(up_level.bit_not())
			explored_op = exploreds_op[nid_] >= 0
			@if_(explored_op.bit_or(up_level))
			def _():
				eid = lin_search(link_edges, link_index[nid], \
					link_index[nid+1], 0, nid_)
				if ASSERT:
					crash(eid == -1)
				_, _, w, wid = link_edges[eid]
				# crash((w_ < w).reveal())
				dist_ = dist + weights[wid] - w
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
					if DEBUG:
						print_ln("add real: %s,%s,%s", nid, nid_, dist_.reveal())
					pq.push(sint_tuple(dist_, nid, nid_))
					add_stat(OFS_PUSH)
		@else_ # pre_nid >= 0
		def _():
			if lmemb is not None:
				pot_dist = graph.pot_func_bidir(S, T, nid, expand_s)
				dist.iadd(-pot_dist)
			exploreds[nid], dists[nid] = pre_nid, dist
			# sort the neighbors
			st, en = link_index[nid], link_index[nid+1]
			OFFSET = 2
			@for_range(st, en)
			def _(eid):
				nid_, _, w, wid = link_edges[eid]
				dist_p = regint(w)
				if lmemb is not None:
					pot_dist_ = graph.pot_func_bidir_static(S, T, nid_, expand_s)
					dist_p.iadd(pot_dist_)
				links[eid] = (nid_, -1, dist_p, wid)
			insertion_sort_inplace(links, st, en, OFFSET)
			if DEBUG:
				print_ln("sorted links: ")
				@for_range(st, en)
				def _(eid):
					print_ln("l: %s", links[eid])
			# explore the first child neighbor
			poss[nid] = st
		_explore_next_virt(poss, link_index, nid, dists, \
			links, exploreds, exploreds_op, levels, pq)
	
def SPSP(graph, S, T):
	if DEBUG:
		print_ln("SPSP4: %s -> %s", S, T)
	@if_(S == T)
	def _():
		ans, ans_dist = regint.Array(1), sint.Array(1)
		ans[0], ans_dist[0] = S, 0
		return ans, ans_dist, regint(1)
	N, E = graph.N, graph.E
	levels, link_index_for, link_edges_for, \
		link_index_rev, link_edges_rev, weights = graph.ch
	chs_for, chs_rev = graph.chs, graph.chs_r

	exploreds_s, dists_s = regint.Array(N), sint.Array(N)
	exploreds_t, dists_t = regint.Array(N), sint.Array(N)
	for vec in [exploreds_s, dists_s, exploreds_t, dists_t]:
		vec.assign_all(-1)
	p_st = graph.pot_func_bidir(S, T, S, True)
	qs, qt = Heap(N, 3), Heap(N, 3)
	qs.push(sint_tuple(p_st, N, S))
	qt.push(sint_tuple(p_st, N, T))

	min_dist, obest_bridge = sint(DATA_BOUND), sint_tuple(-1, -1)
	expand_s = MemValue(False)
	@while_do(lambda: True)
	def _():
		dist_top = qs.top()[0] + qt.top()[0] - p_st
		@if_((dist_top >= min_dist).reveal())
		def _():
			break_loop()
		expand_s.write(expand_s.bit_not())
		empty_s, empty_t = (qs.size == 0), (qt.size == 0)
		@if_(empty_s.bit_or(empty_t))
		def _():
			expand_s.write(empty_t)
		@if_e(expand_s)
		def _():
			_expand_side(graph, S, T, min_dist, obest_bridge, \
				True, qs, link_index_for, link_edges_for, chs_for, \
				exploreds_s, dists_s, exploreds_t, dists_t)
		@else_ # expand t
		def _():
			_expand_side(graph, S, T, min_dist, obest_bridge, \
				False, qt, link_index_rev, link_edges_rev, chs_rev, \
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

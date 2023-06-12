from Compiler.types import *
from Compiler.library import print_ln, for_range, while_do, break_loop, if_, if_e, else_
from util_mpc import N_PARTY
from link_graph import Graph
# from util import argmin

def SSSP1(graph, S, num):
	print_ln("SSSP1[%d] from %d"% (num, S))
	N, E = graph.N, graph.E
	link_index, link_edges = graph.link_index, graph.link_edges
	weights = graph.weights
	ans, ans_dist = regint.Array(num), sint.Array(num)
	size_ans, size_q = regint(0), regint(0)
	
	exploreds = regint.Array(N)
	exploreds.assign_all(0)
	table_dst, table_query = regint.Array(N), sint.Array(N)
	invidx = regint.Array(N)
	invidx.assign_all(-1)

	nid, odist = regint(S), sint(0)
	@while_do(lambda: True)
	def _():
		ans[size_ans], ans_dist[size_ans] = nid, odist
		size_ans.iadd(1)
		# print_ln("ans[%s]: %s, %s", size_ans, nid, odist.reveal())
		@if_(size_ans >= num)
		def _():
			break_loop()

		exploreds[nid] = 1
		# add items whose src==nid into query table
		@for_range(link_index[nid], link_index[nid+1])
		def _(eid):
			dst = link_edges[eid][0]
			@if_(exploreds[dst] == 0)
			def _():
				odist_ = odist + weights[eid]
				idx_query = invidx[dst]
				@if_e(idx_query == -1)
				def _():
					table_dst[size_q] = dst
					table_query[size_q] = odist_
					invidx[dst] = size_q
					size_q.iadd(1)
				@else_
				def _():
					table_query[idx_query] = table_query[idx_query].min(odist_)
		omin_idx, omin_val = sint(0), sint(table_query[0])
		# print_ln("table")
		@for_range(1, size_q)
		def _(i):
			# print_ln("%s, %s", table_dst[i], table_query[i].reveal())
			comp = (table_query[i] < omin_val)
			omin_val.update(comp.if_else(table_query[i], omin_val))
			omin_idx.update(comp.if_else(i, omin_idx))
		# omin_idx = argmin(table_query[:size_q])
		min_idx = omin_idx.reveal()
		# print_ln("Min item[%s]: %s", min_idx, omin_val.reveal())

		nid.update(table_dst[min_idx])
		odist.update(table_query[min_idx])
		@for_range(invidx[nid], size_q - 1)
		def _(i):
			dst = table_dst[i] = table_dst[i+1]
			invidx[dst] = i
		invidx[nid] = -1
		size_q.iadd(-1)
	return ans, ans_dist, size_ans

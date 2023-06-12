from Compiler.types import *
from Compiler.library import print_ln, for_range, do_while, while_do, break_loop, if_
from util_mpc import N_PARTY
from link_graph import Graph
from heap import Heap

def SSSP3(graph, S, num):
	print_ln("SSSP3[%d] from %d"% (num, S))
	N, E = graph.N, graph.E
	link_index, link_edges = graph.link_index, graph.link_edges
	weights = graph.weights
	ans, ans_dist = regint.Array(num), sint.Array(num)
	size_ans = regint(0)

	exploreds = regint.Array(N)
	exploreds.assign_all(0)
	q = Heap(N)
	q.push((sint(0), sint(S)))
	@while_do(lambda: True)
	def _():
		nid, odist = regint(0), sint(0)
		@do_while
		def _():
			top = q.pop()
			odist.update(top[0])
			nid.update(top[1].reveal())
			return exploreds[nid]
		exploreds[nid] = 1
		ans[size_ans], ans_dist[size_ans] = nid, odist
		size_ans.iadd(1)
		# print_ln("ans[%s]: %s, %s", size_ans, nid, odist.reveal())
		@if_(size_ans >= num)
		def _():
			break_loop()
		# update min dist table
		@for_range(link_index[nid], link_index[nid+1])
		def _(eid):
			nid_ = link_edges[eid][0]
			@if_(exploreds[nid_] == 0)
			def _():
				odist_ = odist + weights[eid]
				q.push((odist_, sint(nid_)))
	return ans, ans_dist, size_ans

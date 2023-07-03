from Compiler.types import *
from Compiler.library import print_ln, for_range, do_while, while_do, break_loop, if_
from util_mpc import *
from link_graph import Graph
from heap import Heap

def SSSP(graph, S, num=None, \
		static_weights=False, link_index=None, link_edges=None):
	N, E = graph.N, graph.E
	if num is None:
		num = N
	print_ln("SSSP3[%d] from %d"% (num, S))
	if link_index is None:
		assert link_edges is None
		link_index, link_edges = graph.link_index, graph.link_edges
	weights = None if static_weights else graph.weights
	vtype = regint if static_weights else sint
	q_tuple = plain_tuple if static_weights else sint_tuple
	ans, ans_dist = regint.Array(num), vtype.Array(num)
	size_ans = regint(0)

	exploreds = regint.Array(N)
	exploreds.assign_all(0)
	q = Heap(N, 2, vtype)
	q.push(q_tuple(0, S))
	@while_do(lambda: True)
	def _():
		nid, odist = regint(0), vtype(0)
		@do_while
		def _():
			top = q.pop()
			odist.update(top[0])
			nid.update(top[1] if static_weights else top[1].reveal())
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
			nid_, w, owid = link_edges[eid]
			@if_(exploreds[nid_] == 0)
			def _():
				w_ = weights[owid] if weights is not None else w
				odist_ = odist + w_
				q.push(q_tuple(odist_, nid_))
	return ans, ans_dist, size_ans

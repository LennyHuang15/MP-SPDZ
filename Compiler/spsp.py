from Compiler.types import *
from Compiler.library import print_ln, for_range, do_while, while_do, break_loop, if_
from util_mpc import N_PARTY
from link_graph import Graph
from heap import Heap

def SPSP0(graph, S, T):
	print_ln("SPSP0: %d -> %d"% (S, T))
	N, E = graph.N, graph.E
	link_index, link_edges = graph.link_index, graph.link_edges
	weights = graph.weights
	ans, ans_dist = regint.Array(N), sint.Array(N)
	size_ans = regint(0)
	@if_(S == T)
	def _():
		ans[size_ans], ans_dist[size_ans] = S, 0
		size_ans.iadd(1)
		return ans, ans_dist, size_ans

	
	return ans, ans_dist, size_ans

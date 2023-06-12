from Compiler.types import *
from Compiler.library import for_range, print_ln
from Compiler.program import Program
import numpy as np
from tqdm import tqdm

def read_graph(fn):
	G_np = np.loadtxt(fn, dtype=int, skiprows=1, delimiter=' ')
	with open(fn, 'r') as fp:
		st = fp.readline()
		NN, NE = [int(x) for x in st.split(' ')]
	return NN, NE, G_np
def save_graph(fn, G_np, NN, NE):
	np.savetxt(fn_g, G_np, fmt="%d", header="%d %d"%(NN, NE), comments="")

def _compact_edges(nodes_edges, N):
	E = sum([len(out_edges) for out_edges in nodes_edges])
	link_index = regint.Array(N+1)
	link_edges = regint.Tensor([E, 2])
	pos = 0
	for nid in range(N):
		link_index[nid] = pos
		deg = len(nodes_edges[nid])
		for leid in range(deg):
			link_edges[pos + leid] = nodes_edges[nid][leid]
		pos += deg
	link_index[N] = pos
	assert pos == E
	return link_index, link_edges
		
class Graph(object):
	def __init__(self, fn):
		print_ln("Loading graph from %s" % fn)
		
		with open(fn) as f:
			line = f.readline()
			N, E = [int(x) for x in line.strip().split(" ")]
			nodes_edges = [[] for node in range(N)]
			for eid in range(E):
				line = f.readline()
				s, t, w = [int(x) for x in line.strip().split(" ")]
				nodes_edges[s-1].append((t-1, w))
		self.N, self.E = N, E
		self.link_index, self.link_edges = _compact_edges(nodes_edges, N)
		# self.rev_edges()
		print_ln("Graph loaded: %d nodes, %d edges" % (N, E))

	# def rev_edges(self):
	# 	N, E = self.N, self.E
	# 	link_index, link_edges = self.link_index, self.link_edges
	# 	# link_index_rev = regint.Array(N+1)
	# 	nodes_edges = [[] for node in range(N)]
	# 	for nid in range(N):
	# 		for eid in range(link_index[nid], link_index[nid+1]):
	# 			t, w = link_edges[eid]
	# 			nodes_edges[t].append((nid, w))
	# 	self.link_index_rev, self.link_edges_rev = _compact_edges(nodes_edges, N)

	def load_weights(self, N_PARTY):
		E = self.E
		parties_weights = sint.Matrix(N_PARTY, E)
		for p in range(N_PARTY):
			parties_weights[p].input_from(p)
			# print_ln("P%s: %s", p, parties_weights[p][:10].reveal())
		parties_weights = parties_weights.transpose()

		weights = sint.Array(E)
		@for_range(E)
		def _(eid):
			weights[eid] = sum(parties_weights[eid])# / N_PARTY
		self.weights = weights
	# 	with open(fn) as f:
	# 		line = f.readline()
	# 		N, E = [int(x) for x in line[:-1].split(" ")]
	# 		assert N == self.N and E == self.E
	# 		weights = [0 for _ in range(E)]
	# 		for eid in range(E):
	# 			line = f.readline()
	# 			s, t, w = [int(x) for x in line[:-1].split(" ")]
	# 			weights[eid] = w
	# 	print_ln("weights loaded: %d edges" % E)
	# 	return weights

from Compiler.types import *
from Compiler.library import print_ln, print_str, runtime_error_if, \
	if_, if_e, else_, while_do, for_range, break_loop
from util_mpc import copy, add_stat, OFS, ASSERT

from enum import IntEnum
FIELDS = IntEnum('FIELDS', \
	('LIDX', 'RIDX', 'WID', 'LID', 'R_WIN', 'W'), start=0)

def _merge(key, tour1, tour2, tidx1=-1, tidx2=-1):
	wid1, wid2 = tour1[FIELDS.WID], tour2[FIELDS.WID]
	if ASSERT:
		runtime_error_if(wid1 < 0, "wid1 %s", wid1)
		runtime_error_if(wid2 < 0, "wid2 %s", wid2)
	r_win = key(wid2) < key(wid1)# sbit
	r_win = r_win.reveal()
	add_stat(OFS.Cmp)
	wid, lid = r_win.cond_swap(wid1, wid2)
	d1, d2 = tour1[FIELDS.W], tour2[FIELDS.W]
	return (tidx1, tidx2, wid, lid, r_win, d1 + d2)

def shift_arr(arr, src, dst, size):
	@if_e(src < dst)
	def _():
		@for_range(size - 1, -1, -1)
		def _(i):
			arr[dst+i] = arr[src+i]
	@else_
	def _():
		@for_range(size)
		def _(i):
			arr[dst+i] = arr[src+i]

def print_tour(tour_, key=None):
	tour = copy(tour_)
	if key is not None:
		for idx in [FIELDS.WID, FIELDS.LID]:
			tour[idx] = key(tour[idx]).reveal()
	print_str("%s, ", tour)

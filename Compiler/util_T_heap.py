from Compiler.types import *
from Compiler.library import print_ln, print_str, \
	if_, while_do, for_range, break_loop, runtime_error_if
from util_mpc import add_stat, OFS

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

	tour = regint.Array(len(FIELDS))
	tour[:] = (tidx1, tidx2, wid, lid, r_win, d1 + d2)
	return tour


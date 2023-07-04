#!/bin/bash

# prog=tutorial
prog=test_dijk
# prog=test_personal

other=''
# Mod prime / GF2^128
opt=F
# ptcs=(semi hemi temi soho) # Dishonest-Majority
ptcs=(hemi)
## ptcs=(atlas shamir)

# Mod 2^k
# opt=R
# ptcs=(semi2k)

# Bin
# opt=B
# ptcs=(semi-bin) # Dishonest-Majority
## ptcs=(ccd)

# other="-G"
# opt=B
# ptcs=(semi-bmr)
## ptcs=(shamir-bmr)

mix=''
mix=-X # daBits
# mix=-Y # EdaBits

bits=64
compile_opts="$other $mix -$opt $bits"
# ./compile.py $compile_opts $prog

hosts=""
hosts="-HHOSTS"
opts=''
# opts='-v'
# opts="--bucket-size 10"
fin=''
# fin="-IF Player-Data/Dijk/CAL/graph"
run_opts="$fin $opts"
for ptc in ${ptcs[@]}
do
	obj=$ptc-party.x
	# echo $obj
	# make -j8 $obj
	# exec="Scripts/$ptc.sh $prog"
	exec="Scripts/compile-run.py $hosts -E $ptc $prog $compile_opts --"

	$exec $run_opts #> $ptc.out
done
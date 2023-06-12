#!/bin/bash

# prog=tutorial
prog=test_dijk
# prog=test_heap

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
./compile.py $other $mix -$opt $bits $prog

opts=''
# opts="--bucket-size 10"
fin=''
fin="-IF Player-Data/Dijk/CAL/graph"
for ptc in ${ptcs[@]}
do
	obj=$ptc-party.x
	# echo $obj
	# make -j8 $obj
	exec=Scripts/$ptc.sh
	# exec="Scripts/compile-run.py -E $ptc -$opt $bits"

	# $exec $fin $prog #> $ptc.out
done
#!/bin/bash

prog=test_dijk
# prog=build_ch
# prog=test_hashmap

# city="BJ"
fn_cin="./Programs/Public-Input/graph/compile.in"
exec 6< $fn_cin
read NP <&6
# read city <&6
# NP=$(head -n 1 $fn_cin)
# NP=4

hosts=""
hosts="-HHOSTS_"
head -$NP HOSTS > HOSTS_

other=''
# Mod prime / GF2^128
opt=F
# ptcs=(semi hemi temi soho) # Dishonest-Majority
ptcs=(hemi)
## ptcs=(atlas shamir)
ptcs=(temi)

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
mix=-Y # EdaBits
compile_optim=''
# compile_optim='-l'

bits=64
compile_opts="$other $mix -$opt $bits $compile_optim"
# ./compile.py $compile_opts $prog

opts=''
# opts='-F'
# opts='-v'
# opts="--bucket-size 10"
# opts="--batch-size 1000"
fin=''
# fin="-IF Player-Data/Dijk/CAL/graph"
port=20050
# port=10000
pn=""
pn="-pn $port"
run_opts="-N $NP $pn $fin $opts"
if [[ $hosts != '' ]]
then
run_opts="$run_opts > $prog.out 2>&1"
fi
for ptc in ${ptcs[@]}
do
	obj=$ptc-party.x
	echo $obj
	# make -j8 $obj

	exec="Scripts/$ptc.sh $prog"
	# exec="Scripts/$ptc-offline.sh $prog"
	exec="Scripts/compile-run.py $hosts -E $ptc $prog $compile_opts --"

	$exec $run_opts #> $ptc.out
done
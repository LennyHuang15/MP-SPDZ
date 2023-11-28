rsync --update -az --progress --include-from include_rsync.txt -ruv ./ -e 'ssh -p '$2 $1
# rsync --update -az --progress --exclude=.git/ --exclude=.vscode/ --exclude=*.x --exclude=*.out -r -u ./ -e 'ssh -p '$2 $1

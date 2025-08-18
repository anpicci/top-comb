# Configuration makefile to make execution a bit easier

clean:
	# Make sure you don't remove cache files from other projects
	$(shell mkdir -p toremove)
	$(shell find definitions/ -name "*cache*" -exec mv {} toremove/cache_{} \;)  
	$(shell find utils/ -name "*cache*" -exec mv {} toremove/cache_{} \;)  
	$(shell find plotter-tools/ -name "*cache*" -exec mv {} toremove/cache_{} \;)  
setup:
	./scripts/setup.sh

run:
	./scripts/run.sh



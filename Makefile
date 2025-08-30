# Configuration makefile to make execution a bit easier

clean:
	$(shell find plugins/ -name "*\.pcm" -exec rm {} \;)  
	$(shell find plugins/ -name "*\.d" -exec rm {}  \;)  
	$(shell find plugins/ -name "*\.so" -exec rm {} \;)
	$(shell find definitions/ -name "*cache*" -exec rm -rf {}  \;)  
	$(shell find utils/ -name "*cache*" -exec rm -rf {}  \;)  
	$(shell find plotter-tools/ -name "*cache*" -exec rm -rf {}  \;)  
setup:
	./scripts/setup.sh

run:
	./scripts/run.sh



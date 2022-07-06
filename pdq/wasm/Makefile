.PHONY: all check-dependencies build test 
.DEFAULT: all
CWD := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))

all: check-dependencies build test

build: check-dependencies
	@docker pull emscripten/emsdk:3.1.7
	@docker run --rm -v $(CWD)/../..:/src emscripten/emsdk:3.1.7 emmake make wasm --directory=pdq/cpp
	
test:
	@[ -f $(CWD)/../cpp/pdq-photo-hasher.js -a -f $(CWD)/../cpp/pdq-photo-hasher.wasm ] || (echo "Build the web assembly before running test targets"; /bin/false)
	@(cd $(CWD); cp ../cpp/pdq-photo-hasher.* scripts)
	@(cd $(CWD); npm install)
	@(cd $(CWD)/test/WebAssemblySeleniumWebDriver/WebAssemblySeleniumWebDriver; dotnet build)
	@(cd $(CWD); echo "Starting node server.."; nohup node server.js &)
	(cd $(CWD)/test/WebAssemblySeleniumWebDriver/WebAssemblySeleniumWebDriver; dotnet run chrome pdqmd5 $(CWD)/test/TestData/PDQMD5TestData.csv http://localhost:9095)
	@(kill -1 `ps -ef | grep 'node server.js' | grep -v grep | awk '{print $$2}'`)

check-dependencies:	 
	@node -v > /dev/null || (echo "Node is not installed. Exiting..."; /bin/false) 
	@dotnet --version > /dev/null || (echo "dotnet Core 6.0 is not installed. Exiting..."; /bin/false) 
	@docker -v > /dev/null || (echo "Docker is not installed. Exiting..."; /bin/false) 

clean:
	@ab=`docker image ls | grep 'emscripten' | awk '{print $3}'`; if [ -n "$$ab" ]; then docker rmi $$ab; \
	fi
	@rm -rf $(CWD)/../cpp/pdq-photo-hasher.js $(CWD)/../cpp/pdq-photo-hasher.wasm
	@(cd $(CWD); rm -rf scripts/pdq-photo-hasher.wasm scripts/pdq-photo-hasher.js)
	@(cd $(CWD); rm -rf node_modules )
	@(cd $(CWD)/test/WebAssemblySeleniumWebDriver/WebAssemblySeleniumWebDriver; rm -rf bin;)

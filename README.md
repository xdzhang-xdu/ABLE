# Prerequisites
1. A computer powerful enogh for running Apollo+LGSVL. 
(Or two computers: one for Apollo, one for LGSVL)
2. rtamt
3. python3

## Install antlr4 for ABLE
Make sure installation of version antlr-4.8(the latest version is not supported):
[Install By Package](https://www.antlr.org/download/antlr-4.8-complete.jar)


## Install RTAMT for ABLE
Please refer to [the github page](https://github.com/nickovic/rtamt) for installation of RTAMT.

# Step by step

## Run Apollo with LGSVL
Please refer to [the detailed documentation](https://www.svlsimulator.com/docs/system-under-test/apollo-master-instructions/) for co-simulation of Apollo with LGSVL.
Set the LGSVL to API-Only mode.

## Setup our bridge.
1. Download and go to the root. Note that the source code should be downloaded and set up on the computer running Apollo.
	```bash
	git clone https://github.com/researcherzxd/ABLE.git
	cd ABLE-SourceCode
	```
2. Install Python API support for LGSVL.
	```bash
	cd ABLE-SourceCode/bridge/PythonAPImaster
	pip3 install --user -e .  
	##If "pip3 install --user -e ." fail, try the following command:
	python3 -m pip install -r requirements.txt --user .
	```

3. Connect our bridge to the LGSVL and Apollo:
	Go the bridge in the folder:/ABLE-SourceCode/bridge
	```bash
	cd /ABLE/bridge
	```
	Find file: [bridge.py](ABLE-SourceCode/bridge/bridge.py).
	There is class `Server` in [bridge.py](ABLE-SourceCode/bridge/bridge.py). 

	Modify the `SIMULATOR_HOST` and `SIMULATOR_PORT` of `Server` to your IP and port of LGSVL.
	Modify the `BRIDGE_HOST` and `BRIDGE_PORT` of `Server` to your IP and port of Apollo.
	
4. Test the parser:
	If the support for parser is properly installed, we can test it by running:
	```bash
	cd /ABLE
	python3 monitor.py
	```
	If there is no errors and warnings, the parser is correct.


## Run our bridge.
Open a terminal on the computer running Apollo.
```bash
cd /ABLE/bridge
python3 bridge.py
```
Keep it Running.


## Run the Generation Algorithm.
Open another terminal on the computer running Apollo.
```bash
cd /ABLE
python3 GFN_Fuzzing.py
```
If the brige is set properly, you will see the LGSVL and Apollo running. The results will be put into a folder that you set in path_config.py.


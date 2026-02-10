Law_Judgement
========================
Law_Judgement对由scenario_runner.py执行场景生成的轨迹做交规断言，目前支持闯红灯和超速的交规断言

## LawJudgement所需的支持
1. antlr与scenario_runner.py保持一致，安装[version 4.10.1](https://www.antlr.org/download/antlr-4.10.1-complete.jar)
2. rtamt安装[version 0.3](https://github.com/nickovic/rtamt) 

## 安装并执行LawJudgement.
1. 进入Law_Judgement项目所在目录 
	```bash
	cd Law_Judgement/
	```
2. 安装Python API   
	**注意：** rtamt最新版本所需的antlr4-python3-runtime版本为4.5，所以在scenario_runner.py执行场景前需切换回4.10版本
	```bash
	python3 -m pip install -r requirements.txt
	```	
3. 执行Law_Judgement断言过程:
	如果正确安装了对解析器的支持，我们可以通过运行：
	```bash
	python3 law_judgement.py example_trace/your_trace_json_file
	```
	如果没有错误和警告，则结果是正确的。
4. 运行示例如下:
	```bash
	python law_judgement.py example_trace/overspeed_0.json
	```
	```bash
	{'rule38_1': 105.43560191354558, 'rule38_2': 1.0, 'rule38_3': 2.0, 'rule38_3_1': 2.0, 'rule38_3_2': 105.43560191354558, 'rule38': 1.0, 'rule42': 1.0, 'rule44': -4.0, 'rule45': -86.17763543770775, 'rule46_2': 1.0, 'rule46_3': 0.5, 'rule47': 1.0, 'rule50': 1.0, 'rule51_3': 1.0, 'rule51_4': 0.0, 'rule51_5': 2.0, 'rule51_6': 998.0, 'rule51_7': 1.0, 'rule52': 1.0, 'rule53': 1.0, 'rule57': 1.0, 'rule58': 0.5, 'rule59': 5.0, 'rule62': 1.0, 'rule63': -59.382054867560925}
	```




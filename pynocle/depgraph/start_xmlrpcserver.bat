REM Demo XML RPC service launcher.  You should create your own.

SET curdir=%~dp0
python xmlrpcrenderer.py --host localhost --port 8745 --log %curdir%xmlrpcrenderer.log --dot "C:\Program Files (x86)\Graphviz 2.28\bin\dot.exe"
pause
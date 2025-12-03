# UECrashReportServer
A Simple UE crash report server in python using fastapi and uvicorn

# How to use
Configure DefaultEngine.ini to use the URL of the crash server:

[CrashReportClient]

DataRouterUrl="http://127.0.0.1:8888/report"


And run with python:

python ./main.py
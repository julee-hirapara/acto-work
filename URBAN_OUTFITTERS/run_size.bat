@echo off
for /L %%i in (1,1,2) do (
    echo Running iteration %%i...
    "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" size_chart.py
)
pause

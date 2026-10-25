@echo off

set PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe

%PYTHON% D:\Julee\CODE\ConstructionWeekOnline\CODE\db_config_1.py
if errorlevel 1 goto :error

%PYTHON% D:\Julee\CODE\ConstructionWeekOnline\CODE\update_insert_input_table_2.py
if errorlevel 1 goto :error

%PYTHON% D:\Julee\CODE\ConstructionWeekOnline\CODE\search_article_3.py
if errorlevel 1 goto:error

%PYTHON% D:\Julee\CODE\ConstructionWeekOnline\CODE\no_data_msg_4.py

REM no_data_msg.py returns 100 when no data is found
if %ERRORLEVEL%==100 goto :nodata
if errorlevel 1 goto :error

%PYTHON% D:\Julee\CODE\ConstructionWeekOnline\CODE\pdp_data_4.py
if errorlevel 1 goto :error

%PYTHON% D:\Julee\CODE\ConstructionWeekOnline\CODE\create_output_file_5.py
if errorlevel 1 goto :error

echo.
echo All scripts completed successfully.
pause
exit /b 0

:nodata
echo.
echo No data found. Skipping remaining scripts.
pause
exit /b 0

:error
echo.
echo A script failed with exit code %ERRORLEVEL%.
pause
exit /b %ERRORLEVEL%
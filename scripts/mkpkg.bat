python setup.py py2exe
copy scripts\run_testmode.bat canhttpd2
copy scripts\run_production.bat canhttpd2
copy PCANBasic.py canhttpd2
copy PCANBasic.dll canhttpd2
7z a canhttpd2.zip canhttpd2

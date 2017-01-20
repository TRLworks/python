#!/usr/bin/python
import os
import subprocess

# finding who am i
os.system("whoami")

# copying the files from /Users/jselvakumar/pyth/test.py to /Users/jselvakumar/Python_test/test2
os.system("cp /Users/jselvakumar/pyth/test.py /Users/jselvakumar/Python_test/test2")

print "files are copied"
exit()

#!/usr/bin/python
import subprocess
with open("output_py.txt", "w+") as output:
     subprocess.call(["python", "./json2markdown.py"], stdout=output);

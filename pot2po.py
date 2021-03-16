#!/usr/bin/env python

# This helper script creates or updates po files from all available pot files.
# Script expects list of languages - when missing, all available languages will be updated.

# default input directory
potFilesPath = "locales"

# default output directory; used as source for poDeploy.py which will compile and move files from here to the final destination
outputPath = "locales"

import os
import sys
import filecmp
import shutil
import getopt
import subprocess
import re

# defaults, can be overriden using script parameters
interactive = 0
languageList = []

# parse command line
opts, args = getopt.getopt(sys.argv[1:], "i", ["interactive"]) 
for opt, arg in opts:
	if (opt in ('-i','--interactive')):
		interactive = 1
if (len(args) > 0):
	languageList = args

print("--------------------------------------------------")
print("1/5 Checking presence of pot directory...")
print("--------------------------------------------------")
if (not os.path.exists(potFilesPath)):
	print("Pot directory `"+potFilesPath+"` doesn't exists")
	sys.exit(1)
print(" -> done.")

print("--------------------------------------------------")
print("2/5 Searching for pot files...")
print("--------------------------------------------------")
potFiles = []
potDirectoryFiles = os.listdir(potFilesPath)
for fileName in potDirectoryFiles:
	if (fileName.endswith(".pot")):
		potFiles.append(fileName[:-len(".pot")])
if (len(potFiles) == 0):
	print("No pot files found")
	sys.exit(1)
else:			
	for potFile in potFiles:
		print(potFile)
print(" -> done.")

print("--------------------------------------------------")
print("3/5 Enumerating list of languages...")
print("--------------------------------------------------")
if (len(languageList) == 0):
	directories = os.listdir(outputPath)
	for dir in directories:
		if (os.path.isdir(os.path.join(outputPath, dir))):
			if (dir != "pot"):
				languageList.append(dir)
if (len(languageList) == 0):
	print("No language defined")
	sys.exit(1)
else:
	print("Pot files will be applied for following languages:")
	for language in languageList:
		print(language)
print(" -> done.")

print("--------------------------------------------------")
print("4/5 Applying language files... ")
print("--------------------------------------------------")
keepGoing = 1 
if (interactive):
	print("Specified languages will be update with found pot files.")
	strtmp = raw_input("Would you like to continue? [Y,n]: ")
	if ((strtmp == 'y') or (strtmp == "Y") or (strtmp == "")):
		keepGoing = 1
	else:
		keepGoing = 0
directoriesMissingCount = 0
filesNewCount = 0
filesUpdateCount = 0
if (keepGoing):	
	for language in languageList:
		languageDir = os.path.join(outputPath, language, "LC_MESSAGES")
		if (not os.path.exists(languageDir)):
			os.makedirs(languageDir)
			directoriesMissingCount += 1
		for potFile in potFiles:
			poFileName = potFile+".po"
			potFileName = potFile+".pot"
			poLanguageFile = os.path.join(languageDir, poFileName)
			potLanguageFile = os.path.join(potFilesPath, potFileName)
			retval = 0
			if (os.path.exists(poLanguageFile)):
				print("Update "+potLanguageFile+" -> "+poLanguageFile)
				retval = subprocess.call(["msgmerge", "--update", "--backup=off", poLanguageFile, potLanguageFile])
				filesUpdateCount += 1
				if (retval != 0):
					print("Error invoking msgmerge application")
					sys.exit(1)
			else:
				print("New    "+potLanguageFile+" -> "+poLanguageFile)
				old = subprocess.check_output(["msginit", "--no-translator", "-l", language, "-i", potLanguageFile, "-o", "-"])

				# replace charset ASCII for UTF-8 in newly created POT file (DBE 2017-06-14)
				output = open(poLanguageFile, 'w')
				new = re.sub(r'text/plain; charset=ASCII', 'text/plain; charset=UTF-8', old)
				output.write(new)
				output.close()
				
				filesNewCount += 1			
			# print("Stripping POT creation date for better revision control")
			with open(poLanguageFile, "r+") as pof:
				new_f = pof.readlines()
				pof.seek(0)
				for line in new_f:
					if "POT-Creation-Date" not in line:
						pof.write(line)
				pof.truncate()
			# remove all comments referencing the source location and set all messages non-obsolete.
			subprocess.call(["msgattrib", "--no-location", "--clear-obsolete", "-o", poLanguageFile, poLanguageFile])
			#Set all messages non-obsolete.
			#subprocess.call(["msgattrib", "--clear-obsolete", "-o", poLanguageFile, poLanguageFile])
else:
	sys.exit()
print(" -> done.")

print("--------------------------------------------------")
print("5/5 Statistics... ")
print("--------------------------------------------------")
print("Directories created: %d" % (directoriesMissingCount, ))
print("New files: %d" % (filesNewCount, ))
print("Updated files: %d" % (filesUpdateCount, ))
print(" -> done.")
print("Stripped POT creation date from all po files for better revision control.")

print("")
if (interactive):
	raw_input("Press Enter to Exit")

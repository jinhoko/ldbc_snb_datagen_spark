import sys
import discoverparams
import readfactors
import random
import json
import os
import codecs
from timeparameters import *

PERSON_PREFIX = "http://www.ldbc.eu/ldbc_socialnet/1.0/data/pers"
COUNTRY_PREFIX = "http://dbpedia.org/resource/"
SEED = 1

def findNameParameters(names, amount = 100):
	srtd = sorted(names,key=lambda x: -x[1])
	res = []
	hist = {}
	for t in srtd:
		if t[1] not in hist:
			hist[t[1]] = []
		hist[t[1]].append(t[0])
	counts = sorted([i for i in hist.iterkeys()])

	mid = len(counts)/2
	i = mid
	while counts[i] - counts[mid] < 0.1 * counts[mid]:
		res.extend([name for name in hist[counts[i]]])
		i += 1
	i = mid - 1
	while  counts[mid] - counts[i] < 0.1 * counts[mid]:
		res.extend([name for name in hist[counts[i]]])
		i -= 1

	return res

class JSONSerializer:
	def __init__(self):
		self.handlers = []
		self.inputs = []

	def setOutputFile(self, outputFile):
		self.outputFile=outputFile

	def registerHandler(self, handler, inputParams):
		self.handlers.append(handler)
		self.inputs.append(inputParams)

	def writeJSON(self):
		output = codecs.open(self.outputFile, "w", encoding="utf-8")

		if len(self.inputs) == 0:
			return

		for i in range(len(self.inputs[0])):
			# compile a single JSON object from multiple handlers
			jsonDict = {}
			for j in range(len(self.handlers)):
				handler = self.handlers[j]
				data = self.inputs[j][i]
				jsonDict.update(handler(data))
			output.write(json.dumps(jsonDict, ensure_ascii=False))
			output.write("\n")

		output.close()

def handlePersonParam(person):
	return {"PersonID": person, "PersonURI":(PERSON_PREFIX+str("%020d"%person))}

def handleTimeParam(timeParam):
	res={"Date0": "%d-%d-%d"%(timeParam.year, timeParam.month, timeParam.day)}
	if timeParam.duration is not None:
		res["Duration"] = timeParam.duration
	return res

def handlePairCountryParam((Country1, Country2)):
	return {"Country1":Country1, "Country2":Country2, "Country1URI":(COUNTRY_PREFIX + Country1), "Country2URI":(COUNTRY_PREFIX + Country2)}

def handleCountryParam(Country):
	return {"Country":Country, "CountryURI": (COUNTRY_PREFIX + Country)}

def handleTagParam(tag):
	return {"Tag": tag}

def handleTagTypeParam(tagType):
	return {"TagType": tagType}

def handleHSParam((HS0, HS1)):
	return {"HS0":HS0, "HS1":HS1}

def handleFirstNameParam(firstName):
	return {"Name":firstName}

def handlePairPersonParam((person1, person2)):
	return {"Person1ID":person1, "Person2ID":person2, "Person2URI":(PERSON_PREFIX+str(person2)), "Person1URI":(PERSON_PREFIX+str(person1))}

def handleWorkYearParam(timeParam):
	return {"Date0":timeParam}

def main(argv=None):
	if argv is None:
		argv = sys.argv

	if len(argv)< 3:
		print "arguments: <input dir> <output>"
		return 1

	indir = argv[1]+"/"
	factorFiles=[]
	friendsFiles = []
	outdir = argv[2]+"/"
	random.seed(SEED)
	
	for file in os.listdir(indir):
		if file.endswith("factors.txt"):
			factorFiles.append(indir+file)
		if file.startswith("m0friendList"):
			friendsFiles.append(indir+file)

	# read precomputed counts from files	
	(personFactors, countryFactors, tagFactors, tagClassFactors, nameFactors, ts) = readfactors.load(factorFiles, friendsFiles)

	# find person parameters
	print "find parameter bindings for Persons"
	selectedPersonParams = {}
	for i in range(1, 15):
		factors = readfactors.getFactorsForQuery(i, personFactors)
		selectedPersonParams[i] = discoverparams.generate(factors)

	# Queries 13 and 14 take two person parameters each. Generate pairs
	secondPerson = {}
	for i in [13, 14]:
		secondPerson[i] = []
		for person in selectedPersonParams[i]:
			j = 0
			while True:
				j = random.randint(0, len(selectedPersonParams[i])-1)
				if selectedPersonParams[i][j] != person:
					break
			secondPerson[i].append(selectedPersonParams[i][j])

	# find country parameters for Query 3 and 11
	print "find parameter bindings for Countries"
	selectedCountryParams = {}
	for i in [3, 11]:
		factors = readfactors.getCountryFactorsForQuery(i, countryFactors)
		selectedCountryParams[i] = discoverparams.generate(factors, portion=0.1)

		# make sure there are as many country parameters as person parameters
		oldlen = len(selectedCountryParams[i])
		newlen = len(selectedPersonParams[i])
		selectedCountryParams[i].extend([selectedCountryParams[i][random.randint(0, oldlen-1)] for j in range(newlen-oldlen)])

	# Query 3 needs two countries as parameters. Generate the second one:
	secondCountry = []
	for c in selectedCountryParams[3]:
		i=0
		while True:
			i = random.randint(0, len(selectedCountryParams[3])-1)
			if selectedCountryParams[3][i]!=c:
				break
		secondCountry.append(selectedCountryParams[3][i])

	# find tag parameters for Query 6
	print "find parameter bindings for Tags"
	selectedTagParams = {}
	for i in [6]:
		selectedTagParams[i] = discoverparams.generate(tagFactors, portion=0.1)
		# make sure there are as many tag paramters as person parameters
		oldlen = len(selectedTagParams[i])
		newlen = len(selectedPersonParams[i])
		selectedTagParams[i].extend([selectedTagParams[i][random.randint(0, oldlen-1)] for j in range(newlen-oldlen)])

	# generate tag type parameters for Query 12
	selectedTagTypeParams = {}
	for i in [12]:
		selectedTagTypeParams[i] = discoverparams.generate(tagClassFactors, portion=0.1)
		# make sure there are as many tag paramters as person parameters
		oldlen = len(selectedTagTypeParams[i])
		newlen = len(selectedPersonParams[i])
		selectedTagTypeParams[i].extend([selectedTagTypeParams[i][random.randint(0, oldlen-1)] for j in range(newlen-oldlen)])

	# find time parameters for Queries 2,3,4,5,9
	selectedPersons = selectedPersonParams[2] + selectedPersonParams[3]+selectedPersonParams[4]
	selectedPersons += selectedPersonParams[5] + selectedPersonParams[9]

	selectedTimeParams = {}
	timeSelectionInput = {
		2: (selectedPersonParams[2], "f", getTimeParamsBeforeMedian),
		3: (selectedPersonParams[3], "ff", getTimeParamsWithMedian),
		4: (selectedPersonParams[4], "f", getTimeParamsWithMedian),
		5: (selectedPersonParams[5], "ffg", getTimeParamsAfterMedian),
		9: (selectedPersonParams[9], "ff", getTimeParamsBeforeMedian)
		#11: (selectedPersonParams[11], "w", getTimeParamsBeforeMedian) # friends of friends work
	}

	print "find parameter bindings for Timestamps"
	selectedTimeParams = findTimeParams(timeSelectionInput, factorFiles, friendsFiles, ts[1])
	# Query 11 takes WorksFrom timestamp
	selectedTimeParams[11] = [random.randint(ts[2], ts[3]) for j in range(len(selectedPersonParams[11]))]

	# Query 10 additionally needs the HS parameter
	HS = []
	for person in selectedPersonParams[10]:
		HS0 = random.randint(1, 12)
		if HS0 == 12:
			HS1 = 1
		else:
			HS1 = HS0 + 1
		HS.append((HS0, HS1))

	# Query 1 takes first name as a parameter
	nameParams =  findNameParameters(nameFactors)# discoverparams.generate(nameFactors)
	# if there are fewer first names than person parameters, repeat some of the names
	if len(nameParams) < len(selectedPersonParams[2]):
		oldlen = len(nameParams)
		newlen = len(selectedPersonParams[2])
		nameParams.extend([nameParams[random.randint(0, oldlen-1)] for j in range(newlen-oldlen)])

	# serialize all the parameters as JSON
	jsonWriters = {}
	# all the queries have Person as parameter
	for i in range(1,15):
		jsonWriter = JSONSerializer()
		jsonWriter.setOutputFile(outdir+"query_%d_param.txt"%(i))
		if i != 13 and i != 14: # these three queries take two Persons as parameters
			jsonWriter.registerHandler(handlePersonParam, selectedPersonParams[i])
		jsonWriters[i] = jsonWriter

	# add output for Time parameter
	for i in timeSelectionInput:
		jsonWriters[i].registerHandler(handleTimeParam, selectedTimeParams[i])

	# other, query-specific parameters
	jsonWriters[1].registerHandler(handleFirstNameParam, nameParams)
	jsonWriters[3].registerHandler(handlePairCountryParam, zip(selectedCountryParams[3],secondCountry))
	jsonWriters[6].registerHandler(handleTagParam, selectedTagParams[6])
	jsonWriters[10].registerHandler(handleHSParam, HS)
	jsonWriters[11].registerHandler(handleCountryParam, selectedCountryParams[11])
	jsonWriters[11].registerHandler(handleWorkYearParam, selectedTimeParams[11])
	jsonWriters[12].registerHandler(handleTagTypeParam, selectedTagTypeParams[12])
	jsonWriters[13].registerHandler(handlePairPersonParam, zip(selectedPersonParams[13], secondPerson[13]))
	jsonWriters[14].registerHandler(handlePairPersonParam, zip(selectedPersonParams[14], secondPerson[14]))


	for j in jsonWriters:
		jsonWriters[j].writeJSON()
	
if __name__ == "__main__":
	sys.exit(main())
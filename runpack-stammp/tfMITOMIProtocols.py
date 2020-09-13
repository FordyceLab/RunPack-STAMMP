# title             : tfMITOMIprotocols.py
# description       : tf-MITOMI-specific protocols for experimental acquisition notebook
# authors           : Daniel Mokhtari, Arjun Aditham, Nicole DelRosso
# credits           : Scott Longwell
# date              : 201711015
# version update    : 20200913
# version           : v0.1
# python_version    : 2.7

from runpack import valvecontrol as vc
from runpack import imagingcontrol as ic
from runpack.io import ExperimentalHarness as eh
from Queue import Queue
import numpy as np

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

import time



def flowOligoStartAssay(deviceName, substrateInput, bufferInput, KineticAcquisition, equilibrationTime = 600, treeFlushTime = 20, bindingTime = 1800, washoutTime = 600, postEquilibImageChanExp = {'5cy5':[30]}, postWashImageChanExp = {'5cy5':[30], '4egfp':[500]}, performImaging = True):

	"""
	Description of assay here



	"""

	eh.scriptlogger.info('>> Flowing oligo, starting assay ' + 'for device ' + deviceName + ' in lines ' + str(substrateInput))
	
	# Flush the inlet tree
	eh.scriptlogger.info('The inlet tree wash started for oligo in ' + str(substrateInput))
	vc.returnToSafeState([deviceName])
	vc.openValves([deviceName], [substrateInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	eh.scriptlogger.info('The inlet tree wash done for oligo in ' + str(substrateInput))


	#Expose chip to oligo, equilibrate for equilibrationTime
	eh.scriptlogger.info('Chip equilibration started for substrate in ' + str(substrateInput))
	vc.closeValves([deviceName], ['w'])
	vc.openValves([deviceName], ['in', 'out', 's1', 's2'])
	time.sleep(equilibrationTime)
	eh.scriptlogger.info('Chip equilibration done for substrate in ' + str(substrateInput))


	#Close things to prep for assay, and open buttons
	vc.closeValves([deviceName], [substrateInput[:-1], 'in', 'out', 's1', 's2'])
	time.sleep(0.5)
	vc.openValves([deviceName], ['b1', 'b2'])
	#Start the assay
	if performImaging:
		eh.scriptlogger.info('Binding oligo to buttons, starting kinetic acquisition' + str(substrateInput))
		KineticAcquisition.startAssay(eh.rootPath, eh.posLists[deviceName], scanQueueFlag = sendToQueue)
	else:
		eh.scriptlogger.info('Binding oligo to buttons, no kinetics' + str(substrateInput))
		time.sleep(bindingTime)

	# Obtain pre-wash Cy5 no matter what
	ic.scan(eh.rootPath, postEquilibImageChanExp, deviceName, KineticAcquisition.note.replace(" ", "_")+'_PreWash_Quant', eh.posLists[deviceName], wrappingFolder = True)

	#Close things to prep for assay, and open buttons
	eh.scriptlogger.info('The inlet tree wash started for buffer in ' + str(bufferInput))
	vc.returnToSafeState([deviceName])
	vc.openValves([deviceName], [bufferInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	eh.scriptlogger.info('The inlet tree wash done for buffer in ' + str(bufferInput))

	# Flow buffer through chip
	vc.closeValves([deviceName], ['w'])
	vc.closeValves([deviceName], ['b1', 'b2'])
	time.sleep(0.5)
	vc.openValves([deviceName], ['in', 'out', 's1', 's2'])
	time.sleep(washoutTime)
	

	vc.closeValves([deviceName], [bufferInput[:-1], 'in', 's1', 's2', 'out'])
	ic.scan(eh.rootPath, postWashImageChanExp, deviceName, KineticAcquisition.note.replace(" ", "_")+'_PostWash_Quant', eh.posLists[deviceName], wrappingFolder = True)





def flowOligoStartAssaysConcurrent(deviceNames, substrateInputs, bufferInputs, notes, equilibrationTime = 600, treeFlushTime = 20, bindingTime = 1800, 
			washoutTime = 600, postEquilibImageChanExp = {'5cy5':[80]}, postWashImageChanExp = {'5cy5':[1500], '4egfp':[500]}):

	"""
	Performs binding assay for a single oligo concentration.

	Procedure:
	1) Flush inlet tree
	2) Flow oligo onto device
	3) Close sandwiches, open buttons, wait 30 min
	4) Prewash Cy5 imaging
	5) Close buttons, wash 10 min
	6) Postwash Cy5 and eGFP imaging


	Arguments
		(list) deviceNames: list of the name of devices
		(list) substrate inputs: list of input for DNA on each device
		(list) buffer inputs: PBS inlets for both devices
		(list) notes: oligo identities, in order of device name
		equilibrationTime: time (sec) for equilibration of protein and DNA (in seconds), standard is 30 minutes
		treeFlushTime: time (sec) for flushing inlet tree of oligo before introducing onto device
		bindingTime: time (sec) for equilibrating TF-DNA interaction
		washoutTime: time (sec) for washing through buffer post binding measurement. 
		postEquilibImageChanExp: prewash Cy5 image channel and exposure settings
		postWashImageChanExp: channels and exposures for postwash eGFP and Cy5 imaging

	"""

	eh.scriptlogger.info('>> Flowing oligo, starting assay for device {} in lines {}'.format(str(deviceNames), str(substrateInputs)))
	
	# Flush the inlet tree
	eh.scriptlogger.info('The inlet tree wash started for oligo in {}'.format(str(substrateInputs)))
	vc.returnToSafeState(deviceNames)


	for device, substrateInput in list(zip(deviceNames, substrateInputs)):
		vc.openValves([device], [substrateInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	eh.scriptlogger.info('The inlet tree wash done for oligo in ' + str(substrateInput))


	#Flow oligo onto device, equilibrate for equilibrationTime
	eh.scriptlogger.info('Chip equilibration started for substrate in ' + str(substrateInputs))
	vc.closeValves(deviceNames, ['w'])
	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	time.sleep(equilibrationTime)
	eh.scriptlogger.info('Chip equilibration done for substrate in ' + str(substrateInputs))


	#Close things to prep for assay, and open buttons
	for device, substrateInput in list(zip(deviceNames, substrateInputs)):
		vc.closeValves([device], [substrateInput[:-1], 'in', 'out', 's1', 's2'])
	time.sleep(1)
	vc.openValves(deviceNames, ['b1', 'b2'])
  

	eh.scriptlogger.info('Binding oligo to buttons, no kinetics' + str(substrateInputs))
	time.sleep(bindingTime)

	# Obtain pre-wash Cy5 no matter what
	for device, note in list(zip(deviceNames, notes)):
		ic.scan(eh.rootPath, postEquilibImageChanExp, device, note.replace(" ", "_")+'_PreWash_Quant', eh.posLists[device], wrappingFolder = True)

	#Close things to prep for assay, and open buttons


	eh.scriptlogger.info('The inlet tree wash started for buffers in ' + str(bufferInputs))
	vc.returnToSafeState(deviceNames)

	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.openValves([device], [bufferInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	eh.scriptlogger.info('The inlet tree wash done for buffer in ' + str(bufferInputs))


	# Flow buffer through chip
	eh.scriptlogger.info('Started flowing buffer through devices for washout ' + str(bufferInputs))
	vc.closeValves(deviceNames, ['w'])
	vc.closeValves(deviceNames, ['b1', 'b2'])
	time.sleep(0.5)
	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	time.sleep(washoutTime)
	eh.scriptlogger.info('Done flowing buffer through devices for washout ' + str(bufferInputs))
   

	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.closeValves([device], [bufferInput[:-1], 'in', 'out'])

	for device, note in list(zip(deviceNames, notes)):
		ic.scan(eh.rootPath, postWashImageChanExp, device, note.replace(" ", "_")+'_PostWash_Quant', eh.posLists[device], wrappingFolder = True)

	vc.returnToSafeState(deviceNames)



def trypsinDigest(deviceNames, bufferInputs, trypInputs, bBSAInputs, assayBufferInputs, washoutTime = 600, treeFlushTime=30, trypsinWashTime = 900):
	"""
	Trypsin digest post protein-binding

	Procedure:
		1. Flow buffer
		2. Flow trypsin 15 min
		3. Wash buffer for 10 min
		4. Flow bBSA for 15 minutes
		5. Wash buffer for 10 minutes


	Arguments:
		(list) deviceNames: list of device names ()
		(list) bufferInputs: list of buffer inputs
		(list) trypInputs: list of trypsin inputs
		(list) bBSAInputs: list of bBSA inputs
		(int) washoutTime: time (seconds) buffer flowed through
		(int) treeFlushTime: time (seconds) reagent flushed to waste to remove air
		(int) trypsinWashTime: time (seconds) of flowing trypsin and bBSA in device

	Returns:
		None

	"""

	#enforce safe state (everything shut)
	vc.returnToSafeState(deviceNames)

	# Flow buffer through chip
	eh.scriptlogger.info('Trypsin Digest')

	# open buffer lines to waste
	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.openValves([device], [bufferInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])

	eh.scriptlogger.info('Started flowing buffer through devices for washout ' + str(bufferInputs))
	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	time.sleep(washoutTime)
	eh.scriptlogger.info('Done flowing buffer through devices for washout ' + str(bufferInputs))
	vc.closeValves(deviceNames, ['in'])
	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.closeValves([device], [bufferInput[:-1], 'w'])


	#flow trypsin through device
	eh.scriptlogger.info('Started flowing trypsin to waste')
	for device, bufferInput in list(zip(deviceNames, trypInputs)):
		vc.openValves([device], [bufferInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])

	eh.scriptlogger.info('Started flowing trypsin through devices for protein cleaning ' + str(trypInputs))
	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	time.sleep(trypsinWashTime)
	eh.scriptlogger.info('Done flowing trypsin through devices ' + str(trypInputs))
	vc.closeValves(deviceNames, ['in'])

	for device, bufferInput in list(zip(deviceNames, trypInputs)):
		vc.closeValves([device], [bufferInput[:-1], 'w'])

	#wash trypsin away
	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.openValves([device], [bufferInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])

	eh.scriptlogger.info('Started flowing buffer through devices for washout ' + str(bufferInputs))
	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	time.sleep(washoutTime)
	eh.scriptlogger.info('Done flowing buffer through devices for washout ' + str(bufferInputs))
	vc.closeValves(deviceNames, ['in'])

	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.closeValves([device], [bufferInput[:-1]])

	#wash bBSA in device
	eh.scriptlogger.info('Started bBSA to waste')
	for device, bBSAInput in list(zip(deviceNames, bBSAInputs)):
		vc.openValves([device], [bBSAInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])

	eh.scriptlogger.info('Started flowing bBSA through devices for surface regeneration ' + str(bBSAInputs))
	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	time.sleep(trypsinWashTime)
	eh.scriptlogger.info('Done flowing bBSA through devices ' + str(bBSAInputs))
	vc.closeValves(deviceNames, ['in'])

	for device, bufferInput in list(zip(deviceNames, bBSAInputs)):
		vc.closeValves([device], [bufferInput[:-1], 'w'])

	#flow buffer through to wash away bBSA
	# for device, bufferInput in list(zip(deviceNames, bufferInputs)):
	# 	vc.openValves([device], [bufferInput[:-1], 'w'])
	# time.sleep(treeFlushTime)
	# vc.closeValves(deviceNames, ['w'])

	# eh.scriptlogger.info('Started flowing buffer through devices for washout ' + str(bufferInputs))
	# vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	# time.sleep(washoutTime)
	# eh.scriptlogger.info('Done flowing buffer through devices for washout ' + str(bufferInputs))
	# vc.closeValves(deviceNames, ['in'])

	# for device, bufferInput in list(zip(deviceNames, bufferInputs)):
	# 	vc.closeValves([device], [bufferInput[:-1], 'w'])

	#let protein sit in assay buffer
	eh.scriptlogger.info('Started assay buffer')
	for device, bufferInput in list(zip(deviceNames, assayBufferInputs)):
		vc.openValves([device], [bufferInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])

	eh.scriptlogger.info('Started flowing assay buffer through devices for equilibration ' + str(assayBufferInputs))
	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	time.sleep(trypsinWashTime)
	eh.scriptlogger.info('Done flowing assay buffer through devices ' + str(assayBufferInputs))
	vc.closeValves(deviceNames, ['in'])

	for device, bufferInput in list(zip(deviceNames, assayBufferInputs)):
		vc.closeValves([device], [bufferInput[:-1], 'w'])


	vc.returnToSafeState(deviceNames)




def removeOligo(deviceNames, bufferInputs, openTime = 120, washoutTime = 300, treeFlushTime=20, washoutSteps = 2):
	"""
	Refreshes a device following an oligo titration series.

	Procedure:
		1. Flow buffer
		2. Shut sandwiches, open buttons (wait 2 min)
		3. Shut buttons, open sandwiches (wait 2 min)
		4. Flow buffer 5 min and repeat 2-3


	Arguments:
		(list) deviceNames: list of device names ()
		(list) bufferInputs: list of buffer inputs
		(int) openTimes: time (seconds) buttons remain open during oligo release step
		(int) washoutTime: time (seconds) buffer flowed through to remove oligo
		(int) treeFlushTime: time (seconds) reagent flushed to waste to remove air
		(int) washoutSteps: number of times to run Procedure

	Returns:
		None

	"""

	#enforce safe state (everything shut)
	vc.returnToSafeState(deviceNames)

	# Flow buffer through chip
	eh.scriptlogger.info('Oligo removal/protein refresh')

	# open buffer lines to waste
	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.openValves([device], [bufferInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])

	eh.scriptlogger.info('Started flowing buffer through devices for washout ' + str(bufferInputs))
	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	time.sleep(300)
	eh.scriptlogger.info('Done flowing buffer through devices for washout ' + str(bufferInputs))

	for i in range(washoutSteps):
		eh.scriptlogger.info('Started washout step {} of {}'.format(i+1, washoutSteps))
		vc.closeValves(deviceNames, ['s1','s2']) #close sandwiches
		time.sleep(5)
		vc.openValves(deviceNames, ['b1','b2']) #open buttons
		eh.scriptlogger.info('Closed sandwiches and opened buttons' + str(deviceNames))
		time.sleep(openTime)

		vc.closeValves(deviceNames, ['b1', 'b2'])
		time.sleep(5)
		vc.openValves(deviceNames, ['s1','s2'])
		eh.scriptlogger.info('Closed buttons and opened sandwiches {} for {}s'.format(str(deviceNames), washoutTime))
		time.sleep(washoutTime)
	
	time.sleep(washoutTime)
	eh.scriptlogger.info('Finished additional washout ' + str(bufferInputs))
	eh.scriptlogger.info('Finished Oligo Removal/Protein refresh')
	vc.returnToSafeState(deviceNames)


def dissociationConcurrent(deviceNames, bufferInputs, notes, points=20, dutyCycle = 1, washoutTime = 600, exposures = {'5cy5':[1500], '4egfp': [500]}):
	"""
	Performs dissociation for oligo post binding assay.

	Procedure:
	1) Flow buffer onto device
	2) shut sandwich values (wait 5 seconds)
	3) open buttons (wait for duty cycle duration)
	4) shut buttons
	5) wash device
	6) Cy5 and eGFP imaging

	Arguments:
		(list) deviceNames: list of the name of devices
		(list) bufferInputs: list of the input for wash buffer on each device
		(list) notes: oligo identities, in order of device name
		points: number of measurements to be taken
		dutyCycle: time (sec) button should remain open
		washoutTime: time (sec) buffer is flowed onto device
		exposures: channels and exposure for kinetic acquisition

	"""
	eh.scriptlogger.info('>> Beginning dissociation curves for device {} with duty cycle {} seconds'.format(str(deviceNames), str(dutyCycle)))
	vc.returnToSafeState(deviceNames)

	#open in and out valves
	vc.openValves(deviceNames,['in','out'])

	for x in xrange(0, points):
		eh.scriptlogger.info('>> Beginning time point {} of {}'.format(str(x+1),str(points)))

		eh.scriptlogger.info('Shutting sandwich valves')
		vc.closeValves(deviceNames,['s1','s2'])
		time.sleep(5)

		eh.scriptlogger.info('Opening button valves')
		vc.openValves(deviceNames,['b1','b2'])
		time.sleep(dutyCycle)
		vc.closeValves(deviceNames,['b1','b2'])
		eh.scriptlogger.info('Shut button valves')
		time.sleep(5)

		eh.scriptlogger.info('Opening sandiwch valves for wash')
		vc.openValves(deviceNames, ['s1','s2'])

		time.sleep(5)

		eh.scriptlogger.info('Started flowing buffer through devices for washout ' + str(bufferInputs))

		for device, bufferInput in list(zip(deviceNames, bufferInputs)):
			vc.openValves([device], [bufferInput[:-1]])

		time.sleep(washoutTime)

		for device, bufferInput in list(zip(deviceNames, bufferInputs)):
			vc.closeValves([device], [bufferInput[:-1]])

		eh.scriptlogger.info('Finished flowing buffer through devices for washout ' + str(bufferInputs))

		for device, note in list(zip(deviceNames, notes)):
			ic.scan(eh.rootPath, exposures, device, note.replace(" ", "_")+'_KineticAcquisition_Point_'+str(x), eh.posLists[device], wrappingFolder = True)

	vc.returnToSafeState(deviceNames)


def continuousImagingbyRaster(deviceNames, notes, exposures = {'5cy5': [100], '4egfp': [500]}, incubationTime = 5400):
	"""
	Raster over devices and take images with given exposures until incubation time is reached

	returns dictionary of scan record dataframes
	"""

	eh.scriptlogger.info('Imaging continuously by rastering across device(s) during DNA incubation')

	startTime = time.time()

	count = 0
	scan_records = {}
	timeElapsed = 0
	while timeElapsed < incubationTime:
		for device, note in list(zip(deviceNames, notes)):
			scan_records[(count, device)] = ic.scan(eh.rootPath, exposures, device, note.replace(" ", "_")+'_BindingRate_Point_'+str(count), eh.posLists[device], wrappingFolder = True)
		count += 1
		timeElapsed = time.time() - startTime

	return scan_records

def flowProteinandDNA(deviceNames, bufferInputs, DNAInputs, proteinInputs, proteinFlowTime=1800, washoutTime=600, treeFlushTime=20, incubationTime=3600):
	"""
	intended for BET-seq.
	following surface chemistry, flow protein for 30 mins.
	then wash out with PBS for 10 mins.
	then flow DNA for 10 mins.
	then allow DNA to bind for 60 mins.
	close buttons.
	"""
	#enforce safe state (everything shut)
	vc.returnToSafeState(deviceNames)

	#flow protein to waste, then over chip
	for device, proteinInput in list(zip(deviceNames, proteinInputs)):
		vc.openValves([device], [proteinInput[:-1], 'w'])
	eh.scriptlogger.info('Started flowing protein through devices ' + str(proteinInputs))
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])

	vc.openValves(deviceNames, ['in', 'out', 's1', 's2', 'b1', 'b2'])
	time.sleep(proteinFlowTime)

	for device, proteinInput in list(zip(deviceNames, proteinInputs)):
		vc.closeValves([device], [proteinInput[:-1]])
	vc.closeValves(deviceNames, ['in', 'out'])
	eh.scriptlogger.info('Finished flowing protein through devices ' + str(proteinInputs))

	# open buffer lines to waste
	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.openValves([device], [bufferInput[:-1], 'w'])
	eh.scriptlogger.info('Started flowing buffer through devices for washout ' + str(bufferInputs))
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])

	vc.openValves(deviceNames, ['in', 'out'])
	time.sleep(washoutTime)

	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.closeValves([device], [bufferInput[:-1]])
	vc.closeValves(deviceNames, ['in', 'out'])
	eh.scriptlogger.info('Finished flowing buffer through devices for washout ' + str(bufferInputs))

	# open DNA lines to waste
	for device, DNAInput in list(zip(deviceNames, DNAInputs)):
		vc.openValves([device], [DNAInput[:-1], 'w'])
	eh.scriptlogger.info('Started flowing DNA through devices for binding ' + str(DNAInputs))
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])

	vc.openValves(deviceNames, ['in', 'out'])
	time.sleep(washoutTime)

	for device, DNAInput in list(zip(deviceNames, DNAInputs)):
		vc.closeValves([device], [DNAInput[:-1]])
	vc.closeValves(deviceNames, ['in', 'out'])
	eh.scriptlogger.info('Finished flowing DNA through devices for binding ' + str(DNAInputs))

	eh.scriptlogger.info('Allowing DNA to bind for %.1f minutes' % (incubationTime/60.0))
	time.sleep(incubationTime)

	vc.returnToSafeState(deviceNames)

def BETseqElute(deviceNames, bufferInputs, treeFlushTime=20):
	"""
	actuate buttons 300 times with 3 second button cycles under constant PBS flow
	"""
	#enforce safe state (everything shut)
	vc.returnToSafeState(deviceNames)

	# Flow buffer through chip
	eh.scriptlogger.info('Elute bound DNA')

	# open buffer lines to waste
	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.openValves([device], [bufferInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])

	eh.scriptlogger.info('Started flowing buffer through devices for washout ' + str(bufferInputs))
	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
    
	# begin button actuations to elute DNA from device
	dutyCycle = 3
	numCycles = 300
	for cycle in range(numCycles):
		eh.scriptlogger.info('Cycle number ' + str(cycle+1))
		vc.openValves(deviceNames,['b1','b2'])
		time.sleep(dutyCycle)
		vc.closeValves(deviceNames,['b1','b2'])
		time.sleep(5)
            
	vc.returnToSafeState(deviceNames)


def runAssaywithKinetics(deviceNames, notes, bufferInputs, competitorInputs, points, dutyCycle, washoutTime=600, prewashExposures={'5cy5':[200, 250]}, postwashExposures={'4egfp':[500],'5cy5':[3000]}, treeFlushTime=20, incubationTime=5400):
	"""
	start this script after letting DNA solubilize in reaction chamber
	open buttons and begin imaging (low exposure times)
	image continuously for 90 mins
	close necks
	take prewash image
	close buttons
	flow PBS for 10 min
	take postwash images
	flow competitor oligo, 10 min
	run kinetics
	"""

	eh.scriptlogger.info('>> Starting TF-DNA binding assay')
	# just to be safe, close everything (only necks should be open at this point)
	vc.returnToSafeState(deviceNames)

	# open buttons to begin binding and reopen necks
	vc.openValves(deviceNames,['b1','b2','neck'])
# 	vc.openValves(deviceNames,['b1','b2'])
	# image continuously for 90 mins (or specified incubation time)
	### still working on this
	# scan_records = continuousImagingbyRaster(deviceNames, notes, exposures=bindingExposures, incubationTime=incubationTime)
	eh.scriptlogger.info('Letting oligo bind for %.1f minutes' % (incubationTime/60.0))
	time.sleep(incubationTime)

	# close neck valves and take prewash image
	vc.closeValves(deviceNames,['neck'])
	eh.scriptlogger.info('Finished binding, taking prewash images')

	for device, note in list(zip(deviceNames, notes)):
		prewash_note = note+'_PreWash'
		ic.scan(eh.rootPath, prewashExposures, device, prewash_note, eh.posLists[device], wrappingFolder=True)

	# close buttons, wash, and take postwash images
	vc.closeValves(deviceNames,['b1','b2'])
	# open buffer lines to waste
	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.openValves([device], [bufferInput[:-1], 'w'])
	eh.scriptlogger.info('Started flowing buffer through devices for washout ' + str(bufferInputs))
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])

	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	time.sleep(washoutTime)

	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.closeValves([device], [bufferInput[:-1]])
	vc.closeValves(deviceNames, ['out','in'])
	eh.scriptlogger.info('Finished flowing buffer through devices for washout ' + str(bufferInputs))

	eh.scriptlogger.info('>> Taking postwash images')
	for device, note in list(zip(deviceNames, notes)):
		postwash_note = note+'_PostWash'
		ic.scan(eh.rootPath, postwashExposures, device, postwash_note, eh.posLists[device], wrappingFolder=True)

	for device, competitorInput in list(zip(deviceNames, competitorInputs)):
		vc.openValves([device], [competitorInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])
	vc.openValves(deviceNames, ['in', 'out'])
	eh.scriptlogger.info('Started flowing dark competitor through devices for washout ' + str(competitorInputs))
	time.sleep(washoutTime)

	for device, competitorInput in list(zip(deviceNames, competitorInputs)):
		vc.closeValves([device], [competitorInput[:-1]])
	vc.closeValves(deviceNames, ['in', 'out', 's1', 's2'])
	eh.scriptlogger.info('Finished flowing dark competitor through devices for washout ' + str(competitorInputs))

	dissociationConcurrent(deviceNames, competitorInputs, notes, points, dutyCycle, washoutTime, postwashExposures)

def runAssaywithOnOffRates(deviceNames, notes, bufferInputs, competitorInputs, points, dutyCycle, washoutTime=600, prewashExposures={'5cy5':[200, 250]}, postwashExposures={'4egfp':[500],'5cy5':[3000]}, bindingExposures={'4egfp':[500],'5cy5':[200,250]}, treeFlushTime=20, incubationTime=5400, associationCycle=2, associationPoints=30):
	"""
	start this script after letting DNA solubilize in reaction chamber
	open buttons and begin imaging (low exposure times)
	image continuously for 90 mins
	close necks
	take prewash image
	close buttons
	flow PBS for 10 min
	take postwash images
	flow competitor oligo, 10 min
	run kinetics
	"""

	eh.scriptlogger.info('>> Starting TF-DNA binding assay')
	# just to be safe, close everything (only necks should be open at this point)
	vc.returnToSafeState(deviceNames)

	# open and close buttons repeatedly to record on rate
	vc.openValves(deviceNames,['b1','b2','neck'])
	for i in range(associationPoints):
		time.sleep(associationCycle)
		vc.closeValves(deviceNames,['b1','b2'])
		eh.scriptlogger.info('Taking image of TF-DNA association rate @ %d sec' % (associationCycle*(i+1)))
		for device, note in list(zip(deviceNames, notes)):
			associationrate_note = note+'_AssociationKinetics_'+str(i)
			ic.scan(eh.rootPath, bindingExposures, device, associationrate_note, eh.posLists[device], wrappingFolder=True)
		vc.openValves(deviceNames,['b1','b2'])

	remainingTime = incubationTime - associationCycle*associationPoints
	eh.scriptlogger.info('Letting oligo bind for %.1f minutes' % (remainingTime/60.0))
	time.sleep(remainingTime)

	# close neck valves and take prewash image
	vc.closeValves(deviceNames,['neck'])
	eh.scriptlogger.info('Finished binding, taking prewash images')

	for device, note in list(zip(deviceNames, notes)):
		prewash_note = note+'_PreWash'
		ic.scan(eh.rootPath, prewashExposures, device, prewash_note, eh.posLists[device], wrappingFolder=True)

	# close buttons, wash, and take postwash images
	vc.closeValves(deviceNames,['b1','b2'])
	# open buffer lines to waste
	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.openValves([device], [bufferInput[:-1], 'w'])
	eh.scriptlogger.info('Started flowing buffer through devices for washout ' + str(bufferInputs))
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])

	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	time.sleep(washoutTime)

	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.closeValves([device], [bufferInput[:-1]])
	vc.closeValves(deviceNames, ['in', 'out', 's1', 's2'])
	eh.scriptlogger.info('Finished flowing buffer through devices for washout ' + str(bufferInputs))

	eh.scriptlogger.info('>> Taking postwash images')
	for device, note in list(zip(deviceNames, notes)):
		postwash_note = note+'_PostWash'
		ic.scan(eh.rootPath, postwashExposures, device, postwash_note, eh.posLists[device], wrappingFolder=True)

	for device, competitorInput in list(zip(deviceNames, competitorInputs)):
		vc.openValves([device], [competitorInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	vc.closeValves(deviceNames, ['w'])
	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	eh.scriptlogger.info('Started flowing dark competitor through devices for washout ' + str(competitorInputs))
	time.sleep(washoutTime)

	for device, competitorInput in list(zip(deviceNames, competitorInputs)):
		vc.closeValves([device], [competitorInput[:-1]])
	vc.closeValves(deviceNames, ['in', 'out', 's1', 's2'])
	eh.scriptlogger.info('Finished flowing dark competitor through devices for washout ' + str(competitorInputs))

	dissociationConcurrent(deviceNames, competitorInputs, notes, points, dutyCycle, washoutTime, postwashExposures)



## nicole's scripts:
def flowProteinStartAssaysConcurrent(deviceNames, substrateInputs, bufferInputs, notes, equilibrationTime = 600, treeFlushTime = 20, bindingTime = 1800, 
			washoutTime = 600, postEquilibImageChanExp = {'6mCherry':[80]}, postWashImageChanExp = {'6mCherry':[1500], '4egfp':[500]}):

	"""
	Performs binding assay for a single protein dilution series.

	Procedure:
	1) Flush inlet tree
	2) Flow protein onto device
	3) Close sandwiches, open buttons, wait 30 min
	4) Prewash mCherry imaging
	5) Close buttons, wash 10 min
	6) Postwash mCherry and eGFP imaging


	Arguments
		(list) deviceNames: list of the name of devices
		(list) substrate inputs: list of input for DNA on each device
		(list) buffer inputs: PBS inlets for both devices
		(list) notes: oligo identities, in order of device name
		equilibrationTime: time (sec) for equilibration of protein and protein (in seconds), standard is 30 minutes
		treeFlushTime: time (sec) for flushing inlet tree of oligo before introducing onto device
		bindingTime: time (sec) for equilibrating TF-DNA interaction
		washoutTime: time (sec) for washing through buffer post binding measurement. 
		postEquilibImageChanExp: prewash Cy5 image channel and exposure settings
		postWashImageChanExp: channels and exposures for postwash eGFP and Cy5 imaging

	"""

	eh.scriptlogger.info('>> Flowing protein, starting assay for device {} in lines {}'.format(str(deviceNames), str(substrateInputs)))
	
	# Flush the inlet tree
	eh.scriptlogger.info('The inlet tree wash started for protein in {}'.format(str(substrateInputs)))
	vc.returnToSafeState(deviceNames)


	for device, substrateInput in list(zip(deviceNames, substrateInputs)):
		vc.openValves([device], [substrateInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	eh.scriptlogger.info('The inlet tree wash done for protein in ' + str(substrateInput))


	#Flow protein onto device, equilibrate for equilibrationTime
	eh.scriptlogger.info('Chip equilibration started for substrate in ' + str(substrateInputs))
	vc.closeValves(deviceNames, ['w'])
	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	time.sleep(equilibrationTime)
	eh.scriptlogger.info('Chip equilibration done for substrate in ' + str(substrateInputs))


	#Close things to prep for assay, and open buttons
	for device, substrateInput in list(zip(deviceNames, substrateInputs)):
		vc.closeValves([device], [substrateInput[:-1], 'in', 'out', 's1', 's2'])
	time.sleep(1)
	vc.openValves(deviceNames, ['b1', 'b2'])
  

	eh.scriptlogger.info('Binding protein to buttons, no kinetics' + str(substrateInputs))
	time.sleep(bindingTime)

	# Obtain pre-wash mCherry no matter what
	for device, note in list(zip(deviceNames, notes)):
		ic.scan(eh.rootPath, postEquilibImageChanExp, device, note.replace(" ", "_")+'_PreWash_Quant', eh.posLists[device], wrappingFolder = True)

	#Close things to prep for assay, and open buttons


	eh.scriptlogger.info('The inlet tree wash started for buffers in ' + str(bufferInputs))
	vc.returnToSafeState(deviceNames)

	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.openValves([device], [bufferInput[:-1], 'w'])
	time.sleep(treeFlushTime)
	eh.scriptlogger.info('The inlet tree wash done for buffer in ' + str(bufferInputs))


	# Flow buffer through chip
	eh.scriptlogger.info('Started flowing buffer through devices for washout ' + str(bufferInputs))
	vc.closeValves(deviceNames, ['w'])
	vc.closeValves(deviceNames, ['b1', 'b2'])
	time.sleep(0.5)
	vc.openValves(deviceNames, ['in', 'out', 's1', 's2'])
	time.sleep(washoutTime)
	eh.scriptlogger.info('Done flowing buffer through devices for washout ' + str(bufferInputs))
   

	for device, bufferInput in list(zip(deviceNames, bufferInputs)):
		vc.closeValves([device], [bufferInput[:-1], 'in', 'out'])

	for device, note in list(zip(deviceNames, notes)):
		ic.scan(eh.rootPath, postWashImageChanExp, device, note.replace(" ", "_")+'_PostWash_Quant', eh.posLists[device], wrappingFolder = True)

	vc.returnToSafeState(deviceNames)


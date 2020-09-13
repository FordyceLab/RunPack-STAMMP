# description       : STAMMP protocols for experimental acquisition
# authors           : Daniel Mokhtari, Arjun Aditham
# date              : 20180520
# version update    : 20200913
# version           : 0.1.1
# python_version    : 2.7


import time
from Queue import Queue

import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

from runpack import valvecontrol as vc
from runpack import imagingcontrol as ic
from runpack.io import HardwareInterface as hi
from runpack.io import ExperimentalHarness as eh


################################################################################


def patternDevices(devices, inletNames = None, blocknames = None):
    """Performs device surface patterning

    Performs patterning on passed list of devices assuming standard input line 
    configuration (bBSA in 'bb', NeutrAvidin in 'NA', antibody in 'pHis', and 
    PBS in 'Hepes'). Be sure to attach a "waste tail" to the device, and open 
    all lines to pressure before executing.

    Custom inlet names should be of the form {'na': [na_renamed], 'ph': 
    [ph_renamed], 'bb': [bb_renamed], 'hep': [bb_renamed], 'w': [w_renamed]}
    
    Custom blocknames should be of the form ['bn1', 'bn2', 'bn3',..., 'bnn']
    Blocks opening/closing will occur with inlet opening/closing

    Args:
        devices (list): list of devices to be patterned, lowercase (e.g. 
            ['d1', 'd2', and 'd3'])
        inletNames (dict): remapped inlet names containing precisely {'w':[
            w_renamed], 'na': [na_renamed], 'ph': [ph_renamed], 
            'bb': [bb_renamed], 'hep': [bb_renamed]}. Should not contain trailing index.
        blocknames (list): block control valve names of the form ['c1', 'c2', ..., 'c3']. 
            Valvenames should not containing trailing device index.

    Returns:
        None
    """
    
    wasteValve = ['w']
    buttonValves = ['b1', 'b2']
    sandwichValves = ['s1', 's2']
    inletValve = ['in']
    outlet = ['out']
    wasteValve = ['w']
    naValve = ['na']
    antibodyValve = ['ph']
    bbsaValve = ['bb']
    bufferValve = ['hep']
    if inletNames:
        wasteValve = inletNames['w']
        naValve = inletNames['na']
        antibodyValve = inletNames['ph']
        bbsaValve = inletNames['bb']
        bufferValve = inletNames['hep']
    if blocknames:
        inletValve = inletValve + blocknames


    vc.returnToSafeState(devices) # Closing all valves

    eh.scriptlogger.info('>> 1/18. Starting Device Patterning for devices {}. \
        Starting with all valves closed. NOTE: flow of non-biotinylated BSA \
        should have already been done'.format(devices))
    eh.scriptlogger.info('2/18. Opening sandwiches, outlet, bBSA inlet, and waste. \
        Flushing bBSA through inlet tree to waste for 30s')
    vc.openValves(devices, sandwichValves + outlet + bbsaValve + wasteValve)
    time.sleep(30)

    eh.scriptlogger.info('3/18. Done Flushing bBSA to waste. Flushing bBSA through \
        devices with buttons closed for 5min')
    vc.closeValves(devices, wasteValve)
    vc.openValves(devices, inletValve)
    time.sleep(300)

    eh.scriptlogger.info('4/18. Opened buttons with bBSA flowing through devices to waste for 35min')
    vc.openValves(devices, buttonValves)
    time.sleep(2100)

    eh.scriptlogger.info('5/18. Done Flowing bBSA through devices and closed inlet. \
        Flushing PBS through inlet tree to waste for 30s')
    vc.closeValves(devices, bbsaValve + inletValve)
    vc.openValves(devices, bufferValve + wasteValve)
    time.sleep(30)

    eh.scriptlogger.info('6/18. Done flowing PBS to waste. Flushing PBS through device \
        with  buttons open for 10min')
    vc.closeValves(devices,  wasteValve)
    vc.openValves(devices, inletValve)
    time.sleep(600)

    eh.scriptlogger.info('7/18. Done flushing PBS through devices. \
        Flowing neutravidin through inlet tree to waste for 30s')
    vc.closeValves(devices, bufferValve + inletValve)
    vc.openValves(devices, naValve + wasteValve)
    time.sleep(30)

    eh.scriptlogger.info('8/18. Done flushing Neutravidin to waste. \
        Flowing Neutravidin through devices with buttons open for 30min')
    vc.closeValves(devices, wasteValve)
    vc.openValves(devices, inletValve)
    time.sleep(1800)

    eh.scriptlogger.info('9/18. Done flowing Neutravidin through devices. \
        Flowing PBS through devices with buttons open for 10min')
    vc.closeValves(devices, naValve)
    vc.openValves(devices, bufferValve)
    time.sleep(600)

    eh.scriptlogger.info('10/18. Done flowing PBS through devices and closed buttons. \
        Flowing bBSA through the device for another 35min (quench walls only)')
    vc.closeValves(devices, bufferValve + buttonValves)
    vc.openValves(devices, bbsaValve)   
    time.sleep(2100)

    eh.scriptlogger.info('11/18. Done flowing bBSA through devices. \
        Flowing PBS through the device for 10min. **NEXT STEP IS ANTIBODY FLOWING**')
    vc.closeValves(devices, bbsaValve)
    vc.openValves(devices, bufferValve)
    time.sleep(600)

    eh.scriptlogger.info('12/18. Done flowing PBS through devices and closed inlet. \
        Flowing Antibody through inlet tree to waste for 30s')
    vc.closeValves(devices, bufferValve + inletValve)
    vc.openValves(devices, antibodyValve + wasteValve)
    time.sleep(30)
            
    eh.scriptlogger.info('13/18. Done flowing Antibody through inlet tree. Flowing \
        Antibody through device for 2min')
    vc.closeValves(devices, wasteValve)
    vc.openValves(devices, inletValve)
    time.sleep(120)

    eh.scriptlogger.info('14/18. While flowing Antibody through devices, opened buttons. \
        Flowing for 13.3min')
    vc.openValves(devices, buttonValves)
    time.sleep(800)

    eh.scriptlogger.info('15/18. Closed buttons while flowing Antibody through device for 30s')
    vc.closeValves(devices, buttonValves)
    time.sleep(30)

    eh.scriptlogger.info('16/18. Done flowing Antibody through device. Flowing PBS through \
        inlet tree to waste for 30s')
    vc.closeValves(devices, antibodyValve + inletValve)
    vc.openValves(devices, bufferValve + wasteValve)
    time.sleep(30)      

    eh.scriptlogger.info('17/18. Done flowing PBS to waste. Flowing PBS through device for 10min')
    vc.closeValves(devices, wasteValve)
    vc.openValves(devices, inletValve)
    time.sleep(600)

    eh.scriptlogger.info('18/18. Closed the outlets')
    vc.closeValves(devices, outlet)
    
    eh.scriptlogger.info('>> Done with device patterning')



def flowSubstrateStartAssay(deviceName, substrateInput, KineticAcquisition, 
    equilibrationTime = 600, treeFlushTime = 20, postEquilibrationImaging = False, 
    performImaging = True, postEquilibImageChanExp = {'4egfp':[500]}, scanQueueFlag = False):
    """Performs a standard enzyme turnover assay. 

    Flows substrate, exposes buttons and closes sandwiches, 
    performs imaging at specified timesteps
    Rev. 102817, DM
    
    Args:
        substrateInput (str): valve name of input
        deviceName (str): name of device
        equilibrationTime (int): time to flush device before assay
        
    Returns:
        None
    """   

    sendToQueue = scanQueueFlag  
    inputValve =  substrateInput[:-1]

    eh.scriptlogger.info('>> Flowing substrate, starting assay for \
        device {} in lines {}'.format(deviceName, str(substrateInput)))
    deviceNumber = str(deviceName[-1])
    
    #Flush the inlet tree
    eh.scriptlogger.info('The inlet tree wash started for substrate in ' + str(substrateInput))
    vc.returnToSafeState([deviceName])
    vc.openValves([deviceName], [inputValve, 'w'])
    time.sleep(treeFlushTime)
    eh.scriptlogger.info('The inlet tree wash done for substrate in ' + str(substrateInput))
    
    #Expose chip to substrate, equilibrate for equilibrationTime
    eh.scriptlogger.info('Chip equilibration started for substrate in ' + str(substrateInput))
    if inputValve == 'w': #For the instance where the waste line is the input
        pass
    else:
        vc.closeValves([deviceName], ['w'])
    vc.openValves([deviceName], ['in', 'out', 's1', 's2'])
    time.sleep(equilibrationTime)
    eh.scriptlogger.info('Chip equilibration done for substrate in ' + str(substrateInput))


    if postEquilibrationImaging:
        if sendToQueue == True:
            args = [eh.rootPath, 
                    postEquilibImageChanExp, 
                    deviceName, 
                    KineticAcquisition.note.replace(" ", "_")+'_PreAssay_ButtonQuant', 
                    eh.posLists[deviceName]]
            kwargs = {wrappingFolder: True}
            ic.hardwareQueue.put((args, kwargs))
        else:
            ic.scan(eh.rootPath, 
                postEquilibImageChanExp, 
                deviceName, 
                KineticAcquisition.note.replace(" ", "_")+'_PreAssay_ButtonQuant', 
                eh.posLists[deviceName], 
                wrappingFolder = True)

    #Close things to prep for assay, and open buttons
    vc.closeValves([deviceName], [substrateInput[:-1], 'in', 'out', 's1', 's2'])
    time.sleep(0.5)
    vc.openValves([deviceName], ['b1', 'b2'])
  
    #Start the assay
    if performImaging: 
        KineticAcquisition.startAssay(eh.rootPath, 
                                        eh.posLists[deviceName], 
                                        scanQueueFlag = sendToQueue)



def makeAssayTimings(numLinearPoints = 5, totalPoints = 15, scanTime = 90, totalTime = 3600):
    """


    """
    logPoints = totalPoints - numLinearPoints
    baseTimes = []
    pointDensity = 1
    pointDenistyIncremener = 0.002

    while sum(baseTimes) < totalTime:
        pointDensity += pointDenistyIncremener
        baseTimes = [scanTime] * numLinearPoints
        logTimings = list(np.logspace(np.log10(scanTime), 
                                        np.log10(float(scanTime)**pointDensity), 
                                        num=logPoints, 
                                        dtype=int))
        baseTimes.extend(logTimings)
    
    baseTimes = [scanTime] * numLinearPoints
    logTimings = list(np.logspace(np.log10(scanTime), 
                                    np.log10(float(scanTime)**(pointDensity-pointDenistyIncremener)), 
                                    num=logPoints, 
                                    dtype=int))
    baseTimes.extend(logTimings)
    return baseTimes


def flushInletTree(deviceNames, inputInlet, vacantInlets, flushTime):
    """


    """
    
    # Close all the inlets AND the tree inlet (make no assumptions)
    allInputs = ['hep', 'prot', 'ext2', 'ext1', 'ph', 'na', 'bb', 'w']
    vc.closeValves(deviceNames, allInputs + ['in'])

    indexes = range(len(allInputs))
    indexesInputs = dict(zip(allInputs, indexes))

    inputIndex = indexesInputs[inputInlet]

    # Get the distance from the inputInlet to the vacantInlet mapped to the vacantInlet ID
    vacantInletsOrganized = {}
    for inlet in vacantInlets:
        vacantInletsOrganized[abs(indexesInputs[inlet] - inputIndex)] = [inlet] # distance->port

    vc.openValves(deviceNames, [inputInlet])
    # Now from close to far, open the valve and wash for the flushTime
    for inlet in sorted(vacantInletsOrganized.keys()):
        vc.openValves(deviceNames, vacantInletsOrganized[inlet])
        time.sleep(flushTime)
        vc.closeValves(deviceNames, vacantInletsOrganized[inlet])

    # Close all the inlets AND the tree inlet (again, make no assumptions)
    vc.closeValves(deviceNames, [inputInlet])


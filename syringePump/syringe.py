#!/usr/bin/python
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor, Adafruit_StepperMotor

import time
import atexit

mh = Adafruit_MotorHAT()
#in ml 
total_vol = 60
bolus = 0

#Necessary for autho-shutdown of motor on Pi shutdown
def turnOffMotors():
    mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)

atexit.register(turnOffMotors)

#200 Steps for Stepper motor (Nema-17)
myStepper= mh.getStepper(200,1)
#Set Speed of Nema-17 Motor
myStepper.setSpeed(30)
while True:
    myStepper.step(100, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.SINGLE)

#Interleaved, single coil, double coil or micro steps?
def dispenseLiquid():
    signalReceived = 0
    return 1
while(true):
    if signalReceived:
        dispenseLiquid()
    
#!/usr/bin/python3
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO! Did you run as root?")

import pexpect
from pexpect.fdpexpect import fdspawn

import argparse
import time
import subprocess
import logging
import sys
import random

VBUS_PIN = 21
RESET_PIN = 24

def slow_send(console, s):
    for c in s:
        console.send(c)
        time.sleep(0.1)

def reset_fpga():
    global RESET_PIN

    GPIO.output(RESET_PIN, 0)
    time.sleep(0.1)
    GPIO.output(RESET_PIN, 1)

def power_off():
    global VBUS_PIN
    GPIO.output(VBUS_PIN, 0)

def power_on():
    global VBUS_PIN
    GPIO.output(VBUS_PIN, 1)
        
def main():
    global VBUS_PIN, RESET_PIN
    
    parser = argparse.ArgumentParser(description="Suspend/resume stress test")
    parser.add_argument(
        "-d", "--debug", help="turn on debugging spew", default=False, action="store_true"
    )
    args = parser.parse_args()
    if args.debug:
       logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    ps = subprocess.check_output(['ps', 'aux']).decode('utf-8')
    found_screen = False
    for line in ps.split('\n'):
        if 'screen' in line.lower():
            if '/dev/ttyS0' in line:
                print(line)
                found_screen = True
    if found_screen:
        print("Screen processes found occupying /dev/ttyS0, aborting.")
        exit(0)
       
    # ensure we can talk to /dev/ttyS0 without having to be sudo. pip doesn't install the dependencies in sudo env
    perms = subprocess.check_output(['sudo', 'usermod', '-a', '-G', 'dialout', 'pi'])

    # open a serial terminal
    import serial
    ser = serial.Serial()
    ser.baudrate = 115200
    ser.port="/dev/ttyS0"
    ser.stopbits=serial.STOPBITS_ONE
    ser.xonxoff=0
    try:
        ser.open()
    except:
        print("couldn't open serial port")
        exit(1)
    console = fdspawn(ser)

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup((VBUS_PIN, RESET_PIN), GPIO.OUT)

    for i in range(10):
        print("****iteration {}".format(i))
        print("powering off")
        power_off()
        try:
            print("suspending")
            slow_send(console, "sleep\r")
            print("waiting for suspend feedback")
            console.expect_exact("INFO:susres: PID", 10)
        except Exception as e:
            log = console.before.decode('utf-8')
            for line in log.split('\n'):
                print(line)
            print('problem putting device to sleep {}'.format(str(e)))
            GPIO.cleanup()
            exit(0)
        sleep_duration = random.randrange(20,90) / 10.0
        print("waiting {}s to resume...".format(sleep_duration))
        time.sleep(sleep_duration)
        print("resuming/powering on")
        power_on()
        try:
            console.expect_exact("Jumping to loader", 15)
        except Exception as e:
            log = console.before.decode('utf-8')
            for line in log.split('\n'):
                print(line)
            print("didn't resume, {}".format(str(e)))
            GPIO.cleanup()
            exit(0)
        time.sleep(5) # wait for boot

    GPIO.cleanup()
    
if __name__ == "__main__":
    main()

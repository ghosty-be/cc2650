#!/usr/bin/env python
# part of the connection code is based on sensortag_test.py from
# Michael Saunby. April 2013   
#
# Ghosty - v0.1
# 
# Read sensors from the CC2650 SensorTag
# It's a BLE (Bluetooth low energy) device so using gatttool to
# read and write values. 
#
# Usage.
# sensortag_list.py BLUETOOTH_ADR
#
# To find the address of your SensorTag run 'sudo hcitool lescan'
# You'll need to press the side button to enable discovery.
#
# Notes.
# pexpect uses regular expression so characters that have special meaning
# in regular expressions, e.g. [ and ] must be escaped with a backslash.
#

import pexpect
import sys
import time

def floatfromhex(h):
    t = float.fromhex(h)
    if t > float.fromhex('7FFF'):
        t = -(float.fromhex('FFFF') - t)
        pass
    return t


def die(child,line):
    print child.before
#    print child.before.splitlines()[line]
    child.terminate()
    exit(1)

def activate_sensor(child,code):
    child.sendline('char-write-cmd 0x'+str(code)+' 01')
    child.expect('\[LE\]>')

def read_hex(child,code):
    child.sendline('char-read-hnd 0x'+str(code))
    child.expect('descriptor: .*')
    start=": "
    end=" \r\n"
    bytestring=((child.after.split(start))[1].split(end)[0]).split()
    return bytestring

def read_hex_str(child,code):
    bytestring = read_hex(child,code)
    hex_string = '' .join(bytestring)
    return hex_string

def read_ascii(child,code):
     asciistring = read_hex_str(child,code).decode("hex")
     return asciistring

bluetooth_adr = sys.argv[1]
tool = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' --interactive')
tool.timeout=5
tool.expect('\[LE\]>')
print "Preparing to connect. You might need to press the side button..."
tool.sendline('connect')
# test for success of connect
try:
  tool.expect('Connection successful')
except pexpect.TIMEOUT:
  die(tool,2)

tool.expect('\[LE\]>')
print "name: "+ read_ascii(tool,'3') 
print "system id: "+ read_hex_str(tool,'E')
print "model: "+ read_ascii(tool,'10')
print "serial: "+ read_ascii(tool,'12')
print "firmware revision: "+ read_ascii(tool,'14')
print "hardware revision: "+ read_ascii(tool,'16')
print "software revision: "+ read_ascii(tool,'18')
print "manufacturer: "+ read_ascii(tool,'1A')
print "IEEE 11073-20601 Regulatory Certification Data List: "+ read_ascii(tool,'1C')

## activate sensors
#activate temp sensor
activate_sensor(tool,'24')
#activate humidity sensor
activate_sensor(tool,'2C')
#activate barometer sensor
activate_sensor(tool,'34')
#activate light sensor
activate_sensor(tool,'44')

# when I read too fast it looks like the sensors still show 0
# so lets wait 5 seconds for all sensors to settle
time.sleep(5)

## read sensors
tval = read_hex(tool,'21')
hval = read_hex(tool,'29')
bval = read_hex(tool,'31')
lval = read_hex(tool,'41')

#light requires some complex bitshifting
lumm = int(lval[1]+lval[0],16) & 0x0FFF
lume = (int(lval[1]+lval[0],16) & 0xF000) >> 12
lum = lumm * (0.01 * pow(2.0,lume))

atc = float.fromhex(tval[3]+tval[2])/4*0.03125
print "Ambient temperature: " + str('%.1f' % atc) + "C"
itc = float.fromhex(tval[1]+tval[0])/4*0.03125
print "IR temperature: " + str('%.1f' % itc) + "C"
htc = float.fromhex(hval[1]+hval[0])/65536*165-40
print "hum temperature: " + str('%.1f' % htc) + "C"
#hum = float.fromhex(hval[3]+hval[2])/65536*165-40
hum = float.fromhex(hval[3]+hval[2])/65536*100
print "humidity: " + str('%.1f' % hum) + "%rH"
btc = float.fromhex(bval[2]+bval[1]+bval[0])/100
print "bar temperature: " + str('%.1f' % btc) + "C"
bar = float.fromhex(bval[5]+bval[4]+bval[3])/100
print "barometer: " + str('%.1f' % bar) + "mBar"
# right now I don't know how to interpret this data so raw output
print "light: " + str('%.1f' % lum) + "Lux"

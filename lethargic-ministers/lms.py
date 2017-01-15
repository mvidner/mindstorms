#!/usr/bin/env python

from __future__ import print_function
import bluetooth

def make_lc(n):
    if -32 < n < 32:
        return [n & 0x3f]
    if -128 < n < 128:
        return [0x81, n & 0xff]
    if -32768 < n < 32768:
        return [0x82, n & 0xff, (n >> 8) & 0xff]
    return [0x83, n & 0xff, (n >> 8) & 0xff, (n >> 16) & 0xff, (n >> 24) & 0xff]

class Instruction:        
    def primpar(self, n):
        if type(n) is int:
            return "".join([chr(x) for x in make_lc(n)])
        elif type(n) is str:
            return "\x80" + n + "\x00"
        else:
            raise "Unknown type"

    def beep(self):
        return self.tone(2, 880, 500)
    
    def tone(self, volume, frequency, duration_ms):
        return self.sound_tone(volume, frequency, duration_ms)

    def sound_break(self):
        return "\x94" + self.primpar(0)

    def sound_tone(self, volume, frequency, duration_ms):
        return "\x94" + self.primpar(1) + \
            self.primpar(volume) + \
            self.primpar(frequency) + \
            self.primpar(duration_ms)

    def sound_play(self, volume, filename):
        return "\x94" + self.primpar(2) + \
            self.primpar(volume) + \
            self.primpar(filename)

    def sound_repeat(self, volume, filename):
        return "\x94" + self.primpar(3) + \
            self.primpar(volume) + \
            self.primpar(filename)

    def sound_ready(self):
        return "\x96"
    
    def output_step_speed(self, layer = 0, nos = 0, speed = 0,
                          step_begin = 0, step_do = 0, step_end = 0, brake = 0):
        return "\xae" + \
            self.primpar(layer) + \
            self.primpar(nos) + \
            self.primpar(speed) + \
            self.primpar(step_begin) + \
            self.primpar(step_do) + \
            self.primpar(step_end) + \
            self.primpar(brake)

    def output_step_sync(self, layer = 0, nos = 0, speed = 0,
                         turn = 0, step = 0, brake = 0):
        return "\xb0" + \
            self.primpar(layer) + \
            self.primpar(nos) + \
            self.primpar(speed) + \
            self.primpar(turn) + \
            self.primpar(step) + \
            self.primpar(brake)

    def output_ready(self, layer = 0, nos = 0):
        return "\xaa" + \
            self.primpar(layer) + \
            self.primpar(nos)

    def output_start(self, layer = 0, nos = 0):
        return "\xa6" + \
            self.primpar(layer) + \
            self.primpar(nos)

class MessageSender:
    def __init__(self, socket):
        self.counter = 0
        self.socket = socket

    def msgid(self):
        self.counter += 1
        return self.counter

    def u16(self, n):
        return chr(n & 0xff) + chr((n >> 8) & 0xff)
    
    def direct_command(self, instr_bytes):
        bytes = self.u16(self.msgid()) + "\x80" + "\x00\x00" + instr_bytes

        packet = self.u16(len(bytes)) + bytes
        print("->")
        print(repr(packet))
        self.socket.send(packet)
    
    def direct_command_with_reply(self, instr_bytes):
        bytes = self.u16(self.msgid()) + "\x00" + "\x00\x00" + instr_bytes

        packet = self.u16(len(bytes)) + bytes
        print("->", repr(packet), sep="")
        self.socket.send(packet)
        
        reply = self.socket.recv(1024)
        print("<-", repr(reply), sep="")

host = "00:16:53:53:EE:8C" # "KRALICEK"
port = 1                   # the rfcomm port ev3 uses
sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.connect((host, port))

ins = Instruction()
ms = MessageSender(sock)

MOTOR_B = 2
MOTOR_C = 4

instrs = [
    ins.tone(2, 1760, 500),
    ins.sound_ready(),

    ins.output_step_speed(nos = MOTOR_B | MOTOR_C,
                          speed = 50,
                          step_do = 1080),
    ins.output_ready(nos = MOTOR_B | MOTOR_C),
    
    ins.tone(2, 1760, 500),
    ins.sound_ready(),

    ins.output_step_sync(nos = MOTOR_B | MOTOR_C,
                         speed = +30,
                         turn = 200,
                         step = 1000),
    ins.output_ready(nos = MOTOR_B | MOTOR_C),
    
    ins.tone(2, 1760, 500),
    ins.sound_ready(),

    ins.output_step_speed(nos = MOTOR_B | MOTOR_C,
                          speed = 50,
                          step_do = 1080),
    ins.output_ready(nos = MOTOR_B | MOTOR_C),

    ins.beep(),
    ins.sound_ready(),
]

def fwbk(step):
    ins = Instruction()
    return "".join([
        ins.output_step_sync(nos = MOTOR_B | MOTOR_C,
                             speed = 50,
                             turn = 0,
                             step = step),
        ins.output_ready(nos = MOTOR_B | MOTOR_C),
        ins.output_step_sync(nos = MOTOR_B | MOTOR_C,
                             speed = 50,
                             turn = 0,
                             step = -step),
        ins.output_ready(nos = MOTOR_B | MOTOR_C),
    ])

turnstep = 450
while True:
    print("(ts={0}) > ".format(turnstep), end = '')
    cmd = raw_input()
    if cmd == "q":
        break
    elif cmd == "k":
        instr = ins.output_step_speed(nos = MOTOR_B | MOTOR_C,
                                      speed = 75,
                                      step_begin = 180,
                                      step_do = 360,
                                      step_end = 180)
    elif cmd == "z":
        instr = ins.output_step_speed(nos = MOTOR_B | MOTOR_C,
                                      speed = -75,
                                      step_begin = 180,
                                      step_do = 360,
                                      step_end = 180)
    elif cmd == "l":
        instr = ins.output_step_sync(nos = MOTOR_B | MOTOR_C,
                                     speed = +30,
                                     turn = -200,
                                     step = turnstep)
    elif cmd == "r":
        instr = ins.output_step_sync(nos = MOTOR_B | MOTOR_C,
                                     speed = +30,
                                     turn = +200,
                                     step = turnstep)
    elif cmd == "+":
        turnstep += 50
        continue
    elif cmd == "-":
        turnstep -= 50
        continue
    elif cmd == "f":
        instr = ins.output_step_speed(nos = MOTOR_B | MOTOR_C,
                                      speed = 50,
                                      step_begin = 30,
                                      step_do = 30,
                                      step_end = 30)
    elif cmd == "b":
        instr = ins.output_step_speed(nos = MOTOR_B | MOTOR_C,
                                      speed = -50,
                                      step_begin = 30,
                                      step_do = 30,
                                      step_end = 30)
    elif cmd == "p":
        instr = ins.sound_repeat(2, "../prjs/tracker/idle")

    elif cmd == "s":
        instr = ins.sound_break()

    else:
        print("?")
        
    ms.direct_command_with_reply(instr)
    instr = ins.output_ready(nos = MOTOR_B | MOTOR_C)
    ms.direct_command_with_reply(instr)

sock.close()

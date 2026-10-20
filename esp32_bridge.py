import os
import time
import serial

PORT = "COM3"
FILE = "result.txt"

# open the port without toggling DTR/RTS, which would reset the board
board = serial.Serial()
board.port = PORT
board.baudrate = 115200
board.dtr = False
board.rts = False
board.open()
time.sleep(2)            # give the board a moment to start

print("Watching", FILE, "- leave this window open")

last_seen = None
while True:
    if os.path.exists(FILE):
        stamp = os.path.getmtime(FILE)        # when the file last changed
        if stamp != last_seen:
            bits = open(FILE).read().strip()  # like "00001100"
            try:
                number = int(bits, 2)         # read it as binary: 00001100 -> 12
                board.write(bytes([number]))  # send one byte to the ESP32
                last_seen = stamp
                print("sent", bits, "=", number)
            except ValueError:
                pass                          # file was half-written, try again
    time.sleep(0.1)
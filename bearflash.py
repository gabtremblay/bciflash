# Uniden Bearcat flash utility
#
# Tested on BCi96D
#
# Use only with deobfuscated firmware files (See Bearmock)
#
# This tool can brick your radio.

import sys
from serial import Serial
from serial.serialutil import SerialException, portNotOpenError

_TIMEOUT = 3

def read_response(port):
    """
    Reads the buffer, expecting a \r as EOL
    """
    read_buffer = ""
    while True:
        in_byte = port.read()
        if len(in_byte) > 0:
            if in_byte == "\r":
                break
            else:
                read_buffer += in_byte

    print "Received: " + repr(read_buffer)
    return read_buffer


def write_port(port, content, echo=True):
    """
    Write data to serial port.
    """
    if echo:
        print "Sending: " + repr(content)
    port.write(content)


def get_port(port_name, speed):
    try:
        port = Serial(port_name.upper(), speed, timeout=_TIMEOUT, bytesize=8,
                      parity='N', stopbits=1, dsrdtr=True)
        return port
    except SerialException:
        print "\tError: Unable to open port."
        exit()


# Entry point
print "\nBearflash - Uniden bearcat flasher for BCi96D"

if len(sys.argv) < 3:
    print "\n\tUsage: " + sys.argv[0] + " firmware_file com_port\n\n"
    exit()

firmware_filename = sys.argv[1]
port_name = sys.argv[2]
port = get_port(port_name, 9600)  # initial speed before negociation

# Upload firmware
try:
    with open(firmware_filename) as firmware_file:
        try:
            print "Loading firmware file"
            firmware_content = firmware_file.read()
            firmware_lines = firmware_content.split("\n")
            print "Firmware loaded: " + str(len(firmware_lines)) + " lines."

            print "Negotiating with scanner"
            # Get initial unknown command
            write_port(port, "\r")
            response = read_response(port)

            write_port(port, "*MOD 1\r")
            response = read_response(port)

            write_port(port, "*PGL 1100000\r")
            response = read_response(port)

            write_port(port, "*ULE\r")
            response = read_response(port)

            write_port(port, "*PRG\r")
            response = read_response(port)

            print "Sending firmware, don't turn off your radio!"
            step_size = (len(firmware_lines) / 10)
            current_step = 0
            for line_num in range(0, len(firmware_lines) - 1):
                if line_num == current_step:
                    percent = int(round((100.0 / len(firmware_lines) *
                                         current_step)))
                    print str(percent) + "% ",
                    current_step += step_size

                current_line = firmware_lines[line_num]
                if current_line != "":
                    write_port(port, current_line + "\r", echo=False)
                    #response = read_response(port)
                    #if response == 'NG\r':
                        #write_port(port, 'port')
            print "100%"

            # Get program end and checksum
            response = read_response(port)
            response = read_response(port)
            write_port(port, "*PGL 1100000\r")
            response = read_response(port)

            print "Firmware flash done."

        except portNotOpenError:
            print "\tError: Port was closed"

except IOError:
    print "\tError: Firmware file not found"

# Close port
port.close()

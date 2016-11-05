import serial
import re
import struct


serial_pattern = r"T: (\d+\.\d*)\n";
serial_port = '/dev/ttyUSB1';
#serial_bauds = 115200;
serial_bauds = 9600;

def open_serial_port(binary_mode):
    try:
        s = serial.Serial(serial_port, serial_bauds);
    except:
        print("Error: Wrong port or already open")
        exit(1)
    if not binary_mode:
        line = s.readline();
    #print (line);
    return s;

def serial_read(s):

    line = s.readline();
    return (line)

def serial_read_binary (s):
    #while 1:
    while 1:
        bytesToRead = s.inWaiting()
        if (bytesToRead >= 16):
            break;

    bin_sample_x = s.read(4)
    bin_sample_y = s.read(4)
    bin_sample_z = s.read(4)
    sync = s.read(4)

    if not sync.decode('ascii') == 'UUUU':
        print 'error byte of sync'



    #print  struct.unpack("<L", bin_sample_x)[0], struct.unpack("<L", bin_sample_y)[0], struct.unpack("<L", bin_sample_z)[0], sync.decode('ascii')

    return struct.unpack("<L", bin_sample_x)[0], struct.unpack("<L", bin_sample_y)[0], struct.unpack("<L", bin_sample_z)[0]

def serial_write(s, message):
    s.write(message)


def read_temperature(s):
    line = s.readline();
    m = re.match(serial_pattern, line);
    return float(m.group(1))
#
#s = open_serial_port();
#while 1:
#    line = serial_read(s);
#    print (line);

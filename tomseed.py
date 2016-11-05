import numpy
from obspy import UTCDateTime, read, Trace, Stream
from arduinoCOM import *

import Queue
from threading import Thread
import os.path
import subprocess

import socket
import Server
import signal
import sys

#----Choose type of connection----
serial_mode = True
socket_mode = False
# In serial_COM connection choose the type of data ASCII or binary
binary_mode = True


triaxial_mode = True
resample_mode = False

sps= 259
resps = 259 #216 # resps 0 -> no resample
#datapoints = 100
smoothing = 1	#this controls how much the values are smoothed, 1 is none , >1 is more smoothing

#this is how after how many samples a block is saved
block_length=259 #224 120

#directories for data
mseed_directory = '/home/pi/digital/mseed/'
jitter_directory = '/home/pi/digital/jitter/'

#declare the q from library
queue = Queue.Queue()

file_rawsample = open(jitter_directory + 'Rawsample' + '.txt', "w")
file_packetsample = open(jitter_directory + 'Packetsample' + '.txt', "w")

packetsinqueue = 0

if(resample_mode):
    encoding = 'FLOAT64'
else:
    encoding = 'INT32'
    #encoding = 'FLOAT64'

def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        server.close_connection()
        print('socket closed!')
        sys.exit(0)

def get_first(iterable, default=None):
    if iterable:
        for item in iterable:
            return item
    return default

def read_data():
    #value = 0
    global packetsinqueue
    sample = 0
    first_read = 0

    if(serial_mode):
        print("serial mode on")
        s = open_serial_port(binary_mode);
    if(socket_mode):
        print("socket mode on")
        server = Server.Server("127.0.0.1", 8888)
        client = server.create_connection()

        #init comunication in binary
        if(serial_mode and binary_mode):
            serial_write(s, '1')

    while True:
        # this array is for sample & sample_time

        packet = [0, 0]
        #sample = adc.readADCDifferential23(256, sps) * 1000

        #Read data through serial port
        if(serial_mode):
            if binary_mode:
                #read data in binary. Sample format: array (x,7,z)
                sample = serial_read_binary(s)
            else:
                raw_sample = serial_read(s)

        #Read data through socket
        if(socket_mode):
            #print("read socket sample")
            signal.signal(signal.SIGINT, signal_handler)
            raw_sample = server.receive_data(client)

        #split data from str z,x,y to array (x,y,z)
        if not binary_mode:
            sample = raw_sample.split(',', 2)
            print 'entrou no split'


        #---------------TESTE--------------
        #print sample
        #continue;
        ###################################


        #print("sample")
        #print (sample)
        #print (sample[0])
        #print(sample[1])
        #print (len(sample))
        #raw_sample = re.findall('\d+', raw_sample)

        #file_rawsample.write(str(raw_sample))
        #raw_sample = raw_sample.replace("\r\n","")

        #sample = raw_sample
        '''
        sample = get_first(raw_sample)
        if (sample == None):
            print ("None")
            continue
        if (isinstance(sample, (int, long))):
            print("not int")
            continue
        '''

        if (first_read < 500):
            print("Waiting for 5s of samples:", first_read)
            first_read += 1
            continue
        timenow = UTCDateTime()

        # this smooths the value, removing high freq

        #value += (sample - value) / smoothing

        packet[0] = sample
        packet[1] = timenow


        # print sample,timenow

        queue.put(packet)
        #file_packetsample.write(str(packet))
        #file_packetsample.write("\n")
        #packetsinqueue = packetsinqueue + 1;


# this is the worker thread
def save_data():
    global packetsinqueue
    total_avg = 0
    count = 0
    while True:

        if queue.qsize() >= block_length:
            '''
            packetsinqueue = 0
            file_rawsample.write("------------------------------")
            file_rawsample.write("queue size: ")
            file_rawsample.write(str(queue.qsize()))
            file_rawsample.write("packets in queue: ")
            file_rawsample.write(str(packetsinqueue))

            file_packetsample.write("------------------------------")
            file_packetsample.write("queue size: ")
            file_packetsample.write(str(queue.qsize()))
            file_packetsample.write("packets in queue: ")
            file_packetsample.write(str(packetsinqueue))
            '''
            # two arrays for reading samples & jitter into
            data_1 = numpy.zeros([block_length], dtype=numpy.int32) #numpy.int32 # FORMATO NORMAL EM PORTA COM E int32

            if (triaxial_mode):
                data_2 = numpy.zeros([block_length], dtype=numpy.int32) #numpy.int32 # FORMATO NORMAL EM PORTA COM E int32
                data_3 = numpy.zeros([block_length], dtype=numpy.int32)  #numpy.int32 # FORMATO NORMAL EM PORTA COM E int32
            # note jitter uses float32 - decimals
            jitter = numpy.zeros([block_length], dtype=numpy.float32)

            totaltime = 0
            sample_time = 0
            sample_difference = 0

            # this is the loop without storing jitter value and calcs
            packet = queue.get()
            data_1[0] = packet[0][0]
            starttime = packet[1]

            if(triaxial_mode):
                data_2[0] = packet[0][1]
                data_3[0] = packet[0][2]


            previous_sample = packet[1]
            queue.task_done()

            for x in range(1, block_length):
                packet = queue.get()
                data_1[x] = packet[0][0]

                if(triaxial_mode):
                    data_2[x] = packet[0][1]
                    data_3[x] = packet[0][2]

                sample_time = packet[1]
                sample_difference = sample_time - previous_sample

                # as sps is a rate, and s.d. is time, its 1 over sps
                jitter[x] = sample_difference - (1 / sps)

                # previos_sample is used to get the difference in the next loop
                previous_sample = packet[1]

                totaltime = totaltime + sample_difference
                queue.task_done()

            # a.s.r. is a rate, and t.t is time so its 1 over
            avg_samplingrate = 1 / (totaltime / block_length)
            print(avg_samplingrate)
            #----------------------TESTE----------------
            '''print ('Total time')
            print (totaltime)
            count = count + 1
            total_avg = (total_avg + avg_samplingrate)
            print ('total_avg')
            print ((total_avg /count))'''
            #-------------------------------------

            stats_1 = {'network': 'PT', 'station': 'RASPI', 'location': '00',
                     'channel': 'BHZ', 'npts': block_length, 'sampling_rate': resps,
                     'mseed': {'dataquality': 'D'}, 'starttime': starttime}

            sample_stream = Stream([Trace(data=data_1, header=stats_1)])

            if(triaxial_mode):
                stats_2 = {'network': 'PT', 'station': 'RASPI', 'location': '00',
                         'channel': 'BHE', 'npts': block_length, 'sampling_rate': resps,
                         'mseed': {'dataquality': 'D'}, 'starttime': starttime}

                sample_stream_BHE = Stream([Trace(data=data_2, header=stats_2)])

                stats_3 = {'network': 'PT', 'station': 'RASPI', 'location': '00',
                         'channel': 'BHN', 'npts': block_length, 'sampling_rate': resps,
                         'mseed': {'dataquality': 'D'}, 'starttime': starttime}

                sample_stream_BHN = Stream([Trace(data=data_3, header=stats_3)])
            #print (sample_stream)
            #print(sample_stream[0].data)
            #print(sample_stream[0].data.dtype)

            #----------------Decimate---------------
            #sample_stream.decimate(factor=2, no_filter=True, strict_length=False)
            #sample_stream.decimate(factor=2, strict_length=False)
            #print(sample_stream[0].data.dtype)
            #----------------Interpolate-----------
            #sample_stream.interpolate(sampling_rate = 150)
            #print(sample_stream[0].data.dtype)
            #-----------------get gaps-------------
            #sample_stream.get_gaps()
            #sample_stream.print_gaps()

            #-----------------Merge--------------
            #sample_stream.merge()
            #-----------------Resample-------------

            if(resample_mode):
                print('Stream Len')
                print(len(sample_stream[0].data))
                sample_stream.resample(resps) #no_filter=True


                if(triaxial_mode):
                    sample_stream_BHE.resample(resps)
                    sample_stream_BHN.resample(resps)

            #sample_stream.get_gaps()
            #sample_stream.print_gaps()

            #print(sample_stream[0].data.dtype)
            #print(len(sample_stream[0]))

            #print (sample_stream)

            ##Descomentar se quiser jitter
            #jitter_stream = Stream([Trace(data=jitter)])

            # write sample data

            #sample_stream.print_gaps()

            File = mseed_directory + str(sample_stream[0].stats.starttime.date) + '_BHZ' + '.mseed'
            temp_file = mseed_directory + ".temp_bhz.tmp"

            if(triaxial_mode):
                File_BHE = mseed_directory + str(sample_stream_BHE[0].stats.starttime.date) + '_BHE' + '.mseed'
                temp_file_BHE = mseed_directory + ".temp_bhe.tmp"

                File_BHN = mseed_directory + str(sample_stream_BHN[0].stats.starttime.date) + '_BHN' + '.mseed'
                temp_file_BHN = mseed_directory + ".temp_bhn.tmp"




            if os.path.isfile(File):
                # writes temp file, then merges it with the whole file, then removes file after
                sample_stream.write(temp_file, format='MSEED', encoding=encoding, reclen=512) #INT32 (sem resample) FLOAT64(C/ resample)
                subprocess.call("cat " + temp_file + " >> " + File, shell=True)
                subprocess.call(["rm", temp_file])
            else:
                # if this is the first block of day
                sample_stream.write(File, format='MSEED', encoding=encoding, reclen=512) #INT32 (sem resample) FLOAT64(C/ resample)


            if(triaxial_mode):
                if os.path.isfile(File_BHE):
                    sample_stream_BHE.write(temp_file_BHE, format='MSEED', encoding=encoding, reclen=512) #INT32 (sem resample) FLOAT64(C/ resample)
                    subprocess.call("cat " + temp_file_BHE + " >> " + File_BHE, shell=True)
                    subprocess.call(["rm", temp_file_BHE])
                else:
                    sample_stream_BHE.write(File_BHE, format='MSEED', encoding=encoding, reclen=512) #INT32 (sem resample) FLOAT64(C/ resample)

                if os.path.isfile(File_BHN):
                    sample_stream_BHN.write(temp_file_BHN, format='MSEED', encoding=encoding, reclen=512) #INT32 (sem resample) FLOAT64(C/ resample)
                    subprocess.call("cat " + temp_file_BHN + " >> " + File_BHN, shell=True)
                    subprocess.call(["rm", temp_file_BHN])
                else:
                    sample_stream_BHN.write(File_BHN, format='MSEED', encoding=encoding, reclen=512) #INT32 (sem resample) FLOAT64(C/ resample)

            ##Descomentar se quiser jitter
            '''
            # write jitter data
            File = jitter_directory + str(jitter_stream[0].stats.starttime.date) + '.mseed'
            temp_file = jitter_directory + ".temp.tmp"

            if os.path.isfile(File):
                # writes temp file, then merges it with the whole file, then removes file after
                jitter_stream.write(temp_file, format='MSEED', encoding='FLOAT32', reclen=512)
                subprocess.call("cat " + temp_file + " >> " + File, shell=True)
                subprocess.call(["rm", temp_file])
            else:
                # if this is the first block of day
                jitter_stream.write(File, format='MSEED', encoding='FLOAT32', reclen=512)
'''

worker_sample = Thread(target=save_data)
worker_sample.start()

read_data()




'''

def get_first(iterable, default=None):
    if iterable:
        for item in iterable:
            return item
    return default


# Convert to NumPy character array
data=numpy.zeros([datapoints], dtype=numpy.int32)
#data = np.fromstring(weather, dtype='|S1')




starttime=UTCDateTime();
s= open_serial_port();

for x in range (datapoints):
    sample = 0;
    sample = serial_read(s);
    print (sample)
    new = re.findall('\d+', sample)
    print (new)
    sample = get_first(new);
	#sample = adc.readADCDiffereial23(256, sps)*1000
    print(sample)
    if (sample == None):
        print ("None")
        continue;
    print ("Depois do sample")
    data[x] = sample;
    timenow = UTCDateTime()
    print (sample, timenow);


stats= {'network': 'PT',
  'station': 'RASPI',
  'location': '00',
  'channel': 'BHZ',
  'npts': datapoints,
  'sampling_rate': '20',
  'mseed' : {'dataquality' : 'D'},
  'starttime': starttime}

stream =Stream([Trace(data=data, header=stats)])

stream.write('test.mseed',format='MSEED',encoding='INT16',reclen=512) #encoding='STEIM1'
  #'starttime': starttime}



stream.plot()

'''

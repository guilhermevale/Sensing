from __future__ import print_function

import numpy as np
from obspy import UTCDateTime, read, Trace, Stream
from arduinoCOM import *

encoding = 'INT32'

mseed_directory = '/home/pi/digital/mseed/'

s = open_serial_port();
count = 0
block_length = 232

while(True):
    packet = [0, 0]
    #sample = adc.readADCDifferential23(256, sps) * 1000

    raw_sample = serial_read(s)
    sample = raw_sample.split(',', 2)

    packet[0] = sample
    packet[1] = UTCDateTime()
    #aqui---------------
    data_1 = numpy.zeros([block_length], dtype=numpy.int32)


    data_1[0] = packet[0][0]

    if(count == block_length):

        for x in range(1, block_length):
            sample_time = packet[1]
            sample_difference = sample_time - previous_sample
            previous_sample = packet[1]
            totaltime = totaltime + sample_difference

        avg_samplingrate = 1 / (totaltime / block_length)
        print(avg_samplingrate)

        starttime =  UTCDateTime()
        stats_1 = {'network': 'PT', 'station': 'RASPI', 'location': '00',
        'channel': 'BHZ', 'npts': block_length, 'sampling_rate': resps,
        'mseed': {'dataquality': 'D'}, 'starttime': starttime}

        sample_stream = Stream([Trace(data=data_1, header=stats_1)])


        File = mseed_directory + str(sample_stream[0].stats.starttime.date) + '_BHZ' + '.mseed'
        temp_file = mseed_directory + ".temp_bhz.tmp"

        if os.path.isfile(File):
            # writes temp file, then merges it with the whole file, then removes file after
            sample_stream.write(temp_file, format='MSEED', encoding=encoding, reclen=512) #INT32 (sem resample) FLOAT64(C/ resample)
            subprocess.call("cat " + temp_file + " >> " + File, shell=True)
            subprocess.call(["rm", temp_file])
        else:
            # if this is the first block of day
            sample_stream.write(File, format='MSEED', encoding=encoding, reclen=512) #INT32 (sem resample) FLOAT64(C/ resample)

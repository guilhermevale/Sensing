---------------------install------------------
python 2.7
obspy: https://github.com/obspy/obspy/wiki/Installation-on-Linux-via-Apt-Repository
sudo apt-get install pip
pip install --upgrade
pip install pyserial
pip install pyusb
pip install numpy
pip install queuelib
pip install pathlib

#criar os seguintes directorios para guardar os ficheiros Mseed
 '/home/pi/digital/mseed/'
 '/home/pi/digital/jitter/'

------------------Configuration--------------

****Serial_Port*****

--->ficheiro: arduinoCOM.py

serial_port =  '/dev/ttyACM0'; # Mudar conforme a porta COM ligada ao arduino

serial_bauds = 38400; #Baud rate da porta COM

****Data Configuration****

--->Ficheiro: tomseed.py

triaxial_mode = True # True converte os 3 eixos para mseed. False converte apenas o primeiro  eixo
serial_mode = True  # True caso a informação seja recebida na aplicação via serial port.
socket_mode = False # True caso a informação seja recebida na aplicação via socket TCP.
resample_mode = False # True para fazer resample das amostras para uma frequencia de amostragem diferente.

#sps, samples/second que a aplicação recebe.
sps= 259
#resps, samples/second das amostras após resample.  Caso o resample esteja desligado, usar o mesmo valor no sps e resps (sps = resps)
resps = 259

#block_length Numero de samples guardadas no ficheiro mseed
block_length=259

-----------------Run-------------------------
#Ao correr a aplicação irá fazer descart das primeiras 500 amostras. Após o descart das 500 amostras o programa irá começar a escrever os ficheiros mseed e
imprime na consola a frequencia de amostragem (samples/second) das samples recebidas do arduino.

sudo python tomseed.py # Comando para correr o programa

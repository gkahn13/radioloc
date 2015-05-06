#############################
# Imports used by all files #
#############################

from __future__ import division

import serial
import numpy as np
from collections import defaultdict
import Queue
import time
import threading
import matplotlib.pyplot as plt

from rtlsdr import RtlSdr, librtlsdr, helpers
import pyaudio

####################
# Useful functions #
####################

# function to compute average power spectrum
def avgPS( x, N=256, fs=1):
    M = np.floor(len(x)/N)
    x_ = np.reshape(x[:M*N],(M,N)) * np.hamming(N)[None,:]
    X = np.fft.fftshift(np.fft.fft(x_,axis=1),axes=1)
    return np.r_[-N/2.0:N/2.0]/N*fs, np.mean(abs(X**2),axis=0)

def maxPower(x, N=256, fs=1, M=None):
    M = np.floor(len(x)/N)
    x_ = np.reshape(x[:M*N],(M,N)) * np.hamming(N)[None,:]
    X = np.fft.fftshift(np.fft.fft(x_,axis=1),axes=1)
    return abs(X**2).T.max(axis=0)
    
def avgPower(x, N=256, fs=1, M=None):
    M = np.floor(len(x)/N)
    x_ = np.reshape(x[:M*N],(M,N)) * np.hamming(N)[None,:]
    X = np.fft.fftshift(np.fft.fft(x_,axis=1),axes=1)
    return abs(X**2).T.mean(axis=0)

def smoothMaxPower(mp, M):
    if M % 2 == 0:
        M -= 1
    w = np.hanning(M)
    mp_smooth = np.convolve(np.hstack((mp[:M/2],mp,mp[-M/2:])), w/w.sum(), 'valid')
    if len(mp) != len(mp_smooth):
        print('WARNING: len(mp) = {0} but len(mp_smooth) = {1}'.format(len(mp), len(mp_smooth)))
    return mp_smooth

# Plot an image of the spectrogram y, with the axis labeled with time tl,
# and frequency fl
#
# t_range -- time axis label, nt samples
# f_range -- frequency axis label, nf samples
# y -- spectrogram, nf by nt array
# dbf -- Dynamic range of the spect

def sg_plot( t_range, f_range, y, dbf = 60) :
    eps = 1e-3
    
    # find maximum
    y_max = abs(y).max()
    
    # compute 20*log magnitude, scaled to the max
    y_log = 20.0 * np.log10( abs( y ) / y_max + eps )
    
    fig=plt.figure(figsize=(15,6))
    
    plt.imshow( np.flipud( 64.0*(y_log + dbf)/dbf ), extent= t_range  + f_range ,cmap=plt.cm.gray, aspect='auto')
    plt.xlabel('Time, s')
    plt.ylabel('Frequency, Hz')
    plt.tight_layout()


def myspectrogram_hann_ovlp(x, m, fs, fc,dbf = 60):
    # Plot the spectrogram of x.
    # First take the original signal x and split it into blocks of length m
    # This corresponds to using a rectangular window %
    isreal_bool = np.isreal(x).all()
    
    # pad x up to a multiple of m 
    lx = len(x);
    nt = (lx + m - 1) // m
    x = np.append(x,np.zeros(-lx+nt*m))
    x = x.reshape((m/2,nt*2), order='F')
    x = np.concatenate((x,x),axis=0)
    x = x.reshape((m*nt*2,1),order='F')
    x = x[np.r_[m//2:len(x),np.ones(m//2)*(len(x)-1)].astype(int)].reshape((m,nt*2),order='F')
    
    
    xmw = x * np.hanning(m)[:,None];
    
    
    # frequency index
    t_range = [0.0, lx / fs]
    
    if isreal_bool:
        f_range = [ fc, fs / 2.0 + fc]
        xmf = np.fft.fft(xmw,len(xmw),axis=0)
        sg_plot(t_range, f_range, xmf[0:m/2,:],dbf=dbf)
        print 1
    else:
        f_range = [-fs / 2.0 + fc, fs / 2.0 + fc]
        xmf = np.fft.fftshift( np.fft.fft( xmw ,len(xmw),axis=0), axes=0 )
        sg_plot(t_range, f_range, xmf,dbf = dbf)
    
    return t_range, f_range, xmf
    
def subsample_fixed_length(x, length):
    skip = len(x) // length
    return x[::skip]
    
def play_audio( Q, p, fs , dev, ser="", keydelay=0, chunk=128, repeat=False):
    # play_audio plays audio with sampling rate = fs
    # Q - A queue object from which to play
    # p   - pyAudio object
    # fs  - sampling rate
    # dev - device number
    # ser - pyserial device to key the radio
    # keydelay - delay after keying the radio
    
    # Example:
    # fs = 44100
    # p = pyaudio.PyAudio() #instantiate PyAudio
    # Q = Queue.queue()
    # Q.put(data)
    # Q.put("EOT") # when function gets EOT it will quit
    # play_audio( Q, p, fs,1 ) # play audio
    # p.terminate() # terminate pyAudio
    
    # open output stream
    ostream = p.open(format=pyaudio.paFloat32, channels=1, rate=int(fs),output=True,output_device_index=dev,
                    frames_per_buffer=chunk)
    # play audio
    last_audio = None
    while (1):
        if repeat and Q.empty() and last_audio is not None:
            data = last_audio
        else:
            data = Q.get()
        if data=="EOT"  :
            break
        elif (data=="KEYOFF"  and ser!=""):
            ser.setDTR(0)
            #print("keyoff\n")
        elif (data=="KEYON" and ser!=""):
            ser.setDTR(1)  # key PTT
            #print("keyon\n")
            time.sleep(keydelay) # wait 200ms (default) to let the power amp to ramp up
            
        else:
            try:
                last_audio = data
                ostream.write( data.astype(np.float32).tostring() )
            except:
                print("Exception")
                break
            
def record_audio( queue, p, fs ,dev,chunk=128):
    # record_audio records audio with sampling rate = fs
    # queue - output data queue
    # p     - pyAudio object
    # fs    - sampling rate
    # dev   - device number 
    # chunk - chunks of samples at a time default 1024
    #
    # Example:
    # fs = 44100
    # Q = Queue.queue()
    # p = pyaudio.PyAudio() #instantiate PyAudio
    # record_audio( Q, p, fs, 1) # 
    # p.terminate() # terminate pyAudio
    
   
    istream = p.open(format=pyaudio.paFloat32, channels=1, rate=int(fs),input=True,input_device_index=dev,
                     frames_per_buffer=chunk)

    # record audio in chunks and append to frames
    frames = [];
    while (1):
        try:  # when the pyaudio object is distroyed stops
            data_str = istream.read(chunk) # read a chunk of data
        except:
            break
        data_flt = np.fromstring( data_str, 'float32' ) # convert string to float
        queue.put( data_flt ) # append to list

def printDevNumbers(p):
    N = p.get_device_count()
    for n in range(0,N):
        name = p.get_device_info_by_index(n).get('name')
        print n, name
        
def getSdrDevNumber(p):
    N = p.get_device_count()
    for n in xrange(0,N):
        name = p.get_device_info_by_index(n).get('name')
        if 'pnp' in name.lower():
            return n
    return -1
    
def play_pure_tone(p, s, freq, duration, mag=0.5):
    """
    p: pyaudio object
    s: serial object
    freq: frequency in Hz
    duration: time in sec
    """
    s.setDTR(0)

    # creates a queue
    Qout = Queue.Queue()
   
    dusb_out =  getSdrDevNumber(p)
    assert(dusb_out >= 0)

    t = np.r_[0:duration*44100.0]/44100.0
    sig = mag*np.sin(2*np.pi*freq*t)
    t_play = threading.Thread(target = play_audio,   args = (Qout,   p, 44100, dusb_out, s, 0.2 ))

    # play audio from Queue 
    t_play.start()

    Qout.put("KEYON")
    Qout.put(sig)
    Qout.put("KEYOFF")
    Qout.put("EOT")
    
def play_pure_tone_continuously(p, s, freq, mag=0.5):
    """
    p: pyaudio object
    s: serial object
    freq: frequency in Hz
    duration: time in sec
    """
    s.setDTR(0)

    # creates a queue
    Qout = Queue.Queue()
   
    dusb_out =  getSdrDevNumber(p)
    assert(dusb_out >= 0)

    t = np.r_[0:1*44100.0]/44100.0
    sig = mag*np.sin(2*np.pi*freq*t)
    t_play = threading.Thread(target = play_audio,   args = (Qout,   p, 44100, dusb_out, s, 0.2, 128, True))

    # play audio from Queue 
    t_play.start()

    Qout.put("KEYON")
    Qout.put(sig)

    return Qout
    

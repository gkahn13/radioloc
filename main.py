from utils import *
from servos import *
from sdrs import *
from servos_sdrs import *

num_antennas = 3
fc = 145.6e6

##########################
# Create servos and sdrs #
##########################
servos = Servos(num_antennas, '/dev/ttyACM0')

dev_cnt = librtlsdr.rtlsdr_get_device_count()
rtlsdr_devs = [i if i < dev_cnt else None for i in xrange(num_antennas)]
sdrs = SDRs(rtlsdr_devs, fc)

servos_sdrs = ServosSDRs(servos, sdrs)

ham = serial.Serial('/dev/ttyUSB1')

###################################
# Continuously plot incoming data #
###################################

f, axes = plt.subplots(num_antennas)
plt.ion()
plt.draw()
plt.pause(0.01)

def plot_step():
    for i in xrange(num_antennas):
        angles_and_maxpowers = servos_sdrs.get_angles_and_maxpowers(i)
        if angles_and_maxpowers is not None:
            print('# {0} received #'.format(i))
            angles, mp = angles_and_maxpowers
            
            angles = angles[::-1] # did b/c want right to be positive
            mp_smooth = smoothMaxPower(mp, sdrs.fs)
            prob = 1 - mp_smooth/mp_smooth.sum()
            
            assert(len(angles) == len(mp))
            assert(len(mp) == len(mp_smooth))
            
            axes[i].cla()
                         
            L = 1000
            x = subsample_fixed_length(angles, L)
            y = subsample_fixed_length(prob, L)
            axes[i].plot(x, y, 'r--', linewidth=2.0)
            
            plt.draw()
        else:
            print('{0} not received'.format(i))
            
    print('')
    plt.pause(0.5)
    

servos_sdrs.start(speed=np.pi/2.5, run_on_stop_read=plot_step)
ham.setDTR(1)

try:
    while True:
        plt.pause(1.)
except KeyboardInterrupt:
    print('Exited')

servos_sdrs.stop()
ham.setDTR(0)


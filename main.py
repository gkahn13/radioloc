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
servos_sdrs.start(speed=np.pi/3.)
ham.setDTR(1)

f, axes = plt.subplots(num_antennas, 2)
plt.ion()
plt.draw()
plt.pause(0.01)
try:
    while True:
        for i in xrange(num_antennas):
            angles_and_maxpowers = servos_sdrs.get_angles_and_maxpowers(i)
            if angles_and_maxpowers is not None:
                print('# {0} received #'.format(i))
                angles, mp = angles_and_maxpowers
                
                angles = angles[::-1] # TODO: necessary?
                mp_smooth = smoothMaxPower(mp, sdrs.fs)
                
                assert(len(angles) == len(mp))
                assert(len(mp) == len(mp_smooth))
                
                for j in xrange(2):
                    axes[i,j].cla()
                
                axes[i,0].plot(angles, mp)
                axes[i,0].plot(angles, mp_smooth, 'r--', linewidth=2.0)
                axes[i,1].plot(angles, 1 - mp/mp.sum())
                axes[i,1].plot(angles, 1 - mp_smooth/mp_smooth.sum(), 'r--', linewidth=2.0)
                
                plt.draw()
            else:
                print('{0} not received'.format(i))
                
        print('')
        plt.pause(1.)
except KeyboardInterrupt:
    print('Exited')
#except Exception as e:
#    print('Exception: {0}'.format(e))

servos_sdrs.stop()
ham.setDTR(0)


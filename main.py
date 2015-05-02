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
rtlsdrs = init_rtlsdrs(num_antennas)
sdrs = SDRs(rtlsdrs, fc)
servos_sdrs = ServosSDRs(servos, sdrs)
ham = serial.Serial('/dev/ttyUSB1')

###################################
# Continuously plot incoming data #
###################################
servos_sdrs.start()
ham.setDTR(1)

f, axes = plt.subplots(num_antennas, 1)
axes[0].plot([0],[0])
plt.ion()
plt.draw()
plt.pause(0.01)
try:
    while True:
        for i in xrange(num_antennas):
            angles_and_samples = servos_sdrs.get_angles_and_samples(i)
            if angles_and_samples is not None:
                print('# {0} received #'.format(i))
                angles, samples = angles_and_samples
                
                mp = maxPower(samples)
                mp_smooth = smoothMaxPower(mp, sdrs.fs)
                
                angles = np.linspace(angles[0], angles[-1], len(mp))
                axes[i].cla()
                axes[i].plot(angles, mp)
                axes[i].plot(angles, mp_smooth, 'r--')
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


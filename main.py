from utils import *
from servos import *
from sdrs import *
from servos_sdrs import *

num_antennas = 3
fc = 145.6e6

##########################
# Create servos and sdrs #
##########################
servos = Servos(num_antennas, '/dev/ttyACM1')
rtlsdrs = init_rtlsdrs(num_antennas)
sdrs = SDRs(rtlsdrs, fc)
servos_sdrs = ServosSDRs(servos, sdrs)

###################################
# Continuously plot incoming data #
###################################
servos_sdrs.start()
f, axes = plt.subplots(num_antennas, 1)
try:
    while True:
        for i in xrange(num_antennas):
            angles_and_samples = servos_sdrs.get_angles_and_samples(i)
            if angles_and_samples is not None:
                print('# {0} received #'.format(i))
                angles, samples = angles_and_samples
                mp = maxPower(samples)
                angles = np.linspace(angles[0], angles[-1], len(mp))
                axes[i].cla()
                axes[i].plot(angles, mp)
                plt.show(block=False)
            else:
                print('{0} not received'.format(i))
                
        print('')
        time.sleep(1.)
except KeyboardInterrupt:
    print('Exited')
servos_sdrs.stop()


from utils import *
from servos import *
from sdrs import *
from servos_sdrs import *
from map_probability import *

num_antennas = 3
fc = 910e6 # 145.6e6
antennas = [0, 1]

grid_size = 20
locs = np.array([[10, 5], [10, 10], [10, 15]])
orientations = np.array([0, 0, 0])

##########################
# Create servos and sdrs #
##########################
servos = Servos(num_antennas, '/dev/ttyACM0')

dev_cnt = librtlsdr.rtlsdr_get_device_count()
rtlsdr_devs = [i if i < dev_cnt else None for i in xrange(num_antennas)]
sdrs = SDRs(rtlsdr_devs, fc)

servos_sdrs = ServosSDRs(servos, sdrs)

# ham = serial.Serial('/dev/ttyUSB0')
# ham.setDTR(0)

map_prob = MapProbability(locs, orientations, grid_size)


###################
# Initializations #
###################
sdrs.set_gains(0.1)
# ham.setDTR(0)
# p = pyaudio.PyAudio()

###################################
# Continuously plot incoming data #
###################################

#f, axes = plt.subplots(num_antennas)
#plt.ion()
#plt.draw()
#plt.pause(0.01)
#plot_lock = threading.RLock()

def plot_step(ith):
    angles_and_maxpowers = servos_sdrs.get_angles_and_maxpowers(ith)
    if angles_and_maxpowers is not None:
        print('# {0} received #'.format(ith))
        angles, mp = angles_and_maxpowers
        
        angles = angles[::-1] # did b/c want right to be positive
        #mp_smooth = smoothMaxPower(mp, 100) # sdrs.fs)
        #prob = mp_smooth/mp_smooth.sum()
        #prob0 = (mp_smooth - mp_smooth.min())/((mp_smooth-mp_smooth.min()).sum())
        #prob1 = abs(np.convolve(mp_smooth, [-1, 1], 'valid'))
        #prob1 /= prob1.sum()
        
        
        assert(len(angles) == len(mp))
        #assert(len(mp) == len(mp_smooth))
                     
        L = 100
        a = subsample_fixed_length(angles, L)
        #x = subsample_fixed_length(prob, L)
        #x0 = subsample_fixed_length(prob0, L)
        #x1 = subsample_fixed_length(prob1, L)
        y = subsample_fixed_length(mp, L)
        #z = subsample_fixed_length(mp_smooth, L)
        
        map_prob.update_probability(ith, angles, mp/mp.sum())
        map_prob.draw_map(ith)
        map_prob.draw_map()
        
        #with plot_lock:
        #    axes[i].cla()
        #    axes[i].plot(a, y, 'g--', linewidth=2.0)   
        #    plt.draw()
    else:
        print('{0} not received'.format(ith))
        
    print('')
    plt.pause(0.01)
    

# Qout = play_pure_tone_continuously(p, ham, 3000., mag=0.5)
#for ith in antennas:
    # servos_sdrs.start(ith, speed=np.pi/5., run_on_stop_read=lambda: plot_step(ith))
servos_sdrs.start(0, speed=np.pi/5., run_on_stop_read=lambda: plot_step(0))
servos_sdrs.start(1, speed=np.pi/5., run_on_stop_read=lambda: plot_step(1))

try:
    while True:
        plt.pause(1.)
except KeyboardInterrupt:
    print('Exited')

for ith in antennas:
    servos_sdrs.stop(ith)
# ham.setDTR(0)


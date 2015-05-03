from utils import *

class ServosSDRs:
    """
    Command servos and read from SDRs
    """
    def __init__(self, servos, sdrs):
        self.servos = servos
        self.sdrs = sdrs
        
        self.speed = np.pi/3.
        self.run_flag = False
        self.is_stopped = False
        self.angles_and_maxpowers = [Queue.Queue() for _ in xrange(self.servos.num_servos)]
        
    def start(self, speed=None):
        if self.run_flag:
            return
        
        if speed is not None:
            self.speed = speed
        
        for q in self.angles_and_maxpowers:
            with q.mutex:
                q.queue.clear()
        
        self.run_flag = True
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread.start()                 
    
    def stop(self):
        if not self.run_flag:
            return
        
        self.run_flag = False
        
        while not self.is_stopped:
            time.sleep(0.2)
        self.is_stopped = False
        
    def run(self, fs=200.):
        num_exceptions = 0
        self.servos.set_angles([self.servos.max_angle]*self.servos.num_servos, speed=self.speed, fs=fs)
        
        start_angle, end_angle = self.servos.max_angle, self.servos.min_angle
        while self.run_flag:
            try:
                # record, command servos, compute angles/power
                for i in xrange(self.servos.num_servos):
                    self.sdrs.start_read(i)
                self.servos.set_angles([end_angle]*self.servos.num_servos, speed=self.speed, fs=fs)
                for i in xrange(self.servos.num_servos):
                    time.sleep(0.2) # TODO: why necessary?
                    mp = self.sdrs.stop_read(i)
                    if mp is not None:
                        angles = np.linspace(start_angle, end_angle, len(mp))
                        self.angles_and_maxpowers[i].put([angles, mp])
                start_angle, end_angle = end_angle, start_angle
            except Exception as e:
                num_exceptions += 1
                print('ServosSdr.run exception: {0}'.format(e))
                
                if num_exceptions > 5:
                    break
            
        self.is_stopped = True
        
    def get_angles_and_maxpowers(self, ith):
        """ For ith sdr, return oldest angle/sample if exists, else None """
        if not self.angles_and_maxpowers[ith].empty():
            return self.angles_and_maxpowers[ith].get()
            
########
# TEST #
########
if __name__ == '__main__':            
    from servos import *
    from sdrs import *
    
    servos = Servos(3, '/dev/ttyACM0')
    
    num_sdrs = 3
    rtlsdrs = [None]*num_sdrs
    for i in xrange(librtlsdr.rtlsdr_get_device_count()):
        try:
            rtlsdrs[i] = RtlSdr(i)
        except:
            rtlsdrs[i].close()
            rtlsdrs[i] = RtlSdr(i)
            
    fc = 145.6e6
    sdrs = SDRs(rtlsdrs, fc)
    
    servos_sdrs = ServosSDRs(servos, sdrs)


    ham = serial.Serial('/dev/ttyUSB1')
    ham.setDTR(1)
    time.sleep(0.5)

    servos_sdrs.start()
    print('Press enter to stop')
    raw_input()
    servos_sdrs.stop()        

    ham.setDTR(0)
    
    num_rots = 0
    q = servos_sdrs.angles_and_samples[0]
    while not q.empty():
        angles, samples = q.get()
        mp = maxPower(samples)
        angles = np.linspace(angles[0], angles[-1], len(mp))
        f = plt.figure()
        plt.plot(angles, mp)
        num_rots += 1
    print('num_rots: {0}'.format(num_rots))
    
    plt.show(block=False)
    print('Press enter to exit')
    raw_input()
    
    

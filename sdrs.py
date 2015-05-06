from utils import *

class SDRs:
    """
    Functionality for multiple SDRs (non-blocking)
    """
    def __init__(self, rtlsdr_devs, fc, fs=2.4e5, gain=1.0):
        self.rtlsdr_devs = rtlsdr_devs
        self.rtlsdrs = [None]*len(self.rtlsdr_devs)
        
        self.fc = fc
        self.fs = fs
        self.gain = gain
            
        # for asynchronous reads
        self.read_queues = [Queue.Queue() for _ in self.rtlsdr_devs]
        self.read_run_flags = [False]*len(self.rtlsdr_devs)
        self.read_is_stoppeds = [False]*len(self.rtlsdr_devs)
        self.read_threads = [None]*len(self.rtlsdr_devs)
        
        for ith, rtlsdr_dev in enumerate(self.rtlsdr_devs):
            if rtlsdr_dev is None:
                continue
            
            self.rtlsdrs[ith] = RtlSdr(rtlsdr_dev)
            self.rtlsdrs[ith].sample_rate = self.fs
            self.rtlsdrs[ith].center_freq = self.fc
            self.rtlsdrs[ith].gain = self.gain

            self.read_threads[ith] = threading.Thread(target=self.run, args=(ith,))
            self.read_threads[ith].daemon = True
            self.read_threads[ith].start()
            
    def set_gains(self, gain):
        self.gain = gain
        for rtlsdr in self.rtlsdrs:
            if rtlsdr is not None:
                rtlsdr.gain = self.gain
    
    def start_read(self, ith):
        if self.read_run_flags[ith] or \
            self.rtlsdr_devs[ith] is None or \
            self.read_is_stoppeds[ith]:
            return False
        
        self.read_run_flags[ith] = True
        return True
        
    def stop_read(self, ith):
        """ Returns maxPower of samples gathered """
        if not self.read_run_flags[ith] or self.rtlsdr_devs[ith] is None:
            return None
        
        self.read_run_flags[ith] = False
        
        x = np.array([])
        while not self.read_queues[ith].empty():
            x = np.append(x, self.read_queues[ith].get())
        return np.array(x)
    
    def run(self, ith, M=32*1024): # 64 * 1024
        def read_cb(samples, q):
            if self.read_run_flags[ith]:
                try:
                    q.put(maxPower(samples, N=4*1024))
                    #q.put(maxPower(samples - samples.mean(), N=4*1024))
                    #q.put((samples - samples.mean()))
                    #q.put(samples)
                except Exception as e:
                    print('read_cb exception: {0}'.format(e))
            
        try:
            self.rtlsdrs[ith].read_samples_async(read_cb, M, context=self.read_queues[ith])
        except Exception as e:
            print(e)
        self.read_is_stoppeds[ith] = True

########
# TEST #
########
if __name__ == '__main__':
    num_antennas = 3
    fc = 910e6 # 145.6e6

    dev_cnt = librtlsdr.rtlsdr_get_device_count()
    rtlsdr_devs = [i if i < dev_cnt else None for i in xrange(num_antennas)]
    sdrs = SDRs(rtlsdr_devs, fc)

    sdrs.start_read(0)
    sdrs.start_read(1)
    time.sleep(4)
    x0 = sdrs.stop_read(0)
    x1 = sdrs.stop_read(1)
    
    print('len(x0): {0}'.format(len(x0)))
    print('len(x1): {0}'.format(len(x1)))  
        

from utils import *

class SDRs:
    """
    Functionality for multiple SDRs (non-blocking)
    """
    def __init__(self, rtlsdr_devs, fc, fs=2.4e6, gain=0.1):
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
    
    def run(self, ith, M=8*1024):
        def read_cb(samples, q):
            if self.read_run_flags[ith]:
                try:
                    q.put(maxPower(samples))
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
    
    print('Start reading')
    sdrs.start_read(0)
    print('Sleeping...')
    time.sleep(1)
    print('Stop reading')
    x = np.array([])
    x = sdrs.stop_read(0)
    print('len(x): {0}'.format(len(x)))

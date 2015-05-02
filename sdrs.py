from utils import *

def init_rtlsdrs(num_sdrs):
    rtlsdrs = [None]*num_sdrs
    for i in xrange(librtlsdr.rtlsdr_get_device_count()):
        rtlsdrs[i] = RtlSdr(i)
            
    return rtlsdrs 

class SDRs:
    """
    Functionality for multiple SDRs (non-blocking)
    """
    def __init__(self, rtlsdrs, fc, fs=2.4e6, gain=0.1):
        self.rtlsdrs = rtlsdrs
        for rtlsdr in self.rtlsdrs:
            if rtlsdr is None:
                continue
            rtlsdr.sample_rate = fs
            rtlsdr.center_freq = fc
            rtlsdr.gain = gain
            
        self.fs = fs
            
        # for asynchronous reads
        self.read_queues = [Queue.Queue() for _ in self.rtlsdrs]
        self.read_run_flags = [False]*len(self.rtlsdrs)
        self.read_is_stoppeds = [False]*len(self.rtlsdrs)
        self.read_threads = [None]*len(self.rtlsdrs)
        
    
    def start_read(self, ith):
        if self.read_run_flags[ith] or self.rtlsdrs[ith] is None:
            return
        
        self.read_run_flags[ith] = True
        self.read_threads[ith] = threading.Thread(target=self.run, args=(ith,))
        self.read_threads[ith].daemon = True
        self.read_threads[ith].start()                 
    
    def stop_read(self, ith):
        if not self.read_run_flags[ith] or self.rtlsdrs[ith] is None:
            return

        self.read_run_flags[ith] = False
        
        while not self.read_is_stoppeds[ith]:
            time.sleep(0.2)
        self.read_is_stoppeds[ith] = False
        
        x = []
        while not self.read_queues[ith].empty():
            x += self.read_queues[ith].get()
        return np.array(x)
    
    def run(self, ith, read_slice=0.1):
        num_samples = 256 * ((read_slice * self.fs) // 256)
        
        while self.read_run_flags[ith]:
            samples = self.rtlsdrs[ith].read_samples(num_samples)
            self.read_queues[ith].put(list(samples))
            
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

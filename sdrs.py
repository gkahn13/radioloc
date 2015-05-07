from utils import *

class SDRs:
    """
    Functionality for multiple SDRs (non-blocking)
    """
    def __init__(self, rtlsdr_devs, fcs, fs=2.4e5, gain=1.0):
        """
        rtlsdr_devs: device numbers for sdrs (indexes match servos)
        fcs: frequencies to listen on
        """
        self.rtlsdr_devs = rtlsdr_devs
        self.fcs = fcs
        self.rtlsdrs = [None]*len(self.rtlsdr_devs)
        
        self.fc = np.mean(fcs)
        self.fs = fs
        self.gain = gain
            
        # for asynchronous reads
        self.read_queues = [[Queue.Queue() for _ in self.fcs] for _ in self.rtlsdr_devs]
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
        """
        Returns list of maxPower of samples gathered
        for each frequency in self.fcs
        """
        if not self.read_run_flags[ith] or self.rtlsdr_devs[ith] is None:
            return None
        
        self.read_run_flags[ith] = False
        
        xs = []
        for q in self.read_queues[ith]:
            x = np.array([])
            while not q.empty():
                x = np.append(x, q.get())
            xs.append(np.array(x))
        return xs
    
    def run(self, ith, M=32*1024): # 64 * 1024
        def read_cb(samples, qs):
            lp_len = 1024
            lp_cutoff = 10e3
            lp = signal.firwin(lp_len, lp_cutoff, nyq=self.fs/2.)
            
            if self.read_run_flags[ith]:
                for q, fc in zip(qs, self.fcs):
                    try:
                        fc_centered = fc - self.fc
                        bp = np.exp(1j*2*np.pi*fc_centered*np.r_[0:len(lp)]/self.fs)*lp
                        samples_bp = np.convolve(samples, bp, 'same')
                        q.put(maxPower(samples_bp, N=4*1024))
                        
                        #q.put(maxPower(samples, N=4*1024))
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
        

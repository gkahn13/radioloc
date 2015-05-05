from utils import *

class ServosSDRs:
    """
    Command servos and read from SDRs
    """
    def __init__(self, servos, sdrs):
        self.servos = servos
        self.sdrs = sdrs
        
        self.default_speed = np.pi/3.
        
        self.run_flags = [False]*self.servos.num_servos
        self.is_stoppeds = [False]*self.servos.num_servos
        self.threads = [None]*self.servos.num_servos
        
        self.angles_and_maxpowers = [Queue.Queue() for _ in xrange(self.servos.num_servos)]
        
    def start(self, ith, speed=None, run_on_stop_read=lambda:None):
        if self.run_flags[ith]:
            return
        
        q = self.angles_and_maxpowers[ith]
        with q.mutex:
            q.queue.clear()
        
        self.run_flags[ith] = True
        self.threads[ith] = threading.Thread(target=self.run, args=(ith,speed,run_on_stop_read,))
        self.threads[ith].daemon = True
        self.threads[ith].start()                 
    
    def stop(self, ith):
        if not self.run_flags[ith]:
            return
        
        self.run_flags[ith] = False
        
        while not self.is_stoppeds[ith]:
            time.sleep(0.2)
        self.is_stoppeds[ith] = False
        
    def run(self, ith, speed=None, run_on_stop_read=lambda:None):
        """ run_on_stop_read for things like plotting """
        speed = self.default_speed if speed is None else speed
        num_exceptions = 0
        
        curr_angle = self.servos.min_angle
        self.servos.set_angle(ith, curr_angle, speed)
        des_angle = self.servos.max_angle
        
        while self.run_flags[ith]:
            try:
                self.sdrs.start_read(ith)
                angle, t = self.servos.set_angle(ith, des_angle, speed)
                mp = self.sdrs.stop_read(ith)
                
                if mp is not None:
                    angles = np.linspace(curr_angle, des_angle, len(mp))
                    self.angles_and_maxpowers[ith].put([angles, mp])
                
                curr_angle, des_angle = des_angle, curr_angle
                run_on_stop_read()
            except Exception as e:
                num_exceptions += 1
                print('ServosSdr.run exception: {0}'.format(e))
        
                if num_exceptions > 1:
                    break
        
        self.is_stoppeds[ith] = True
        self.servos.set_angle(ith, 0, 0, block=False)
        
    def get_angles_and_maxpowers(self, ith):
        """ For ith sdr, return oldest angle/sample if exists, else None """
        if not self.angles_and_maxpowers[ith].empty():
            return self.angles_and_maxpowers[ith].get()
            

########
# TEST #
########
if __name__ == '__main__':            
    pass

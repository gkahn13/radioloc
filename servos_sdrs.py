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
        
        self.angles_and_maxpowers = [[Queue.Queue() for _ in self.sdrs.fcs] for _ in xrange(self.servos.num_servos)]
        
    def start(self, ith, speed=None, run_on_stop_read=lambda:None):
        if self.run_flags[ith]:
            return
        
        qs = self.angles_and_maxpowers[ith]
        for q in qs:
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
        print('ServosSdrs: run {0}th'.format(ith))
        speed = self.default_speed if speed is None else speed
        num_exceptions = 0
        
        curr_angle = self.servos.min_angle
        self.servos.set_angle(ith, curr_angle, speed)
        des_angle = self.servos.max_angle
        
        while self.run_flags[ith]:
            #try:
            self.sdrs.start_read(ith)
            angle, t = self.servos.set_angle(ith, des_angle, speed)
            mps = self.sdrs.stop_read(ith)
            
            print('ServosSdrs: type mps {0}'.format(type(mps)))
            print('ServosSdrs: len(mps) {0}'.format(len(mps)))
            if mps is not None:
                for fc_index, mp in enumerate(mps):
                    print('ServosSdrs: len(mp) {0}'.format(len(mp)))
                    angles = np.linspace(curr_angle, des_angle, len(mp))
                    self.angles_and_maxpowers[ith][fc_index].put([angles, mp])

            curr_angle, des_angle = des_angle, curr_angle
            #print('ServosSdrs: run_on_stop_read {0}ith'.format(ith))
            run_on_stop_read()
            #except Exception as e:
            #    num_exceptions += 1
            #    print('ServosSdr.run exception: {0}'.format(e))
            #        
            #    if num_exceptions > 1:
            #        break
        
        self.is_stoppeds[ith] = True
        self.servos.set_angle(ith, 0, speed, block=False)
        
        print('ServosSdrs: stopping {0}th'.format(ith))
        
    def get_angles_and_maxpowers(self, ith, fc_index):
        """ For ith sdr, return oldest angle/sample if exists, else None """
        if not self.angles_and_maxpowers[ith][fc_index].empty():
            return self.angles_and_maxpowers[ith][fc_index].get()

########
# TEST #
########
if __name__ == '__main__':            
    pass

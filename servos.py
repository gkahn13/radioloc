from utils import *

class Servos:
    """
    Commands servos via serial port
    """
    
    def __init__(self, num_servos, port, baudrate=115200):
        self.num_servos = num_servos
        self.lock_serial = threading.RLock()
        self.serial = serial.Serial(port, baudrate=baudrate, timeout=1.)
        
        self.min_angle = -np.pi/4.
        self.max_angle = np.pi/4.
        
        self.read_queues = [Queue.Queue() for _ in xrange(self.num_servos)]
        self.read_stop = False
        self.read_serial_thread = threading.Thread(target=self.read_serial_run, args=())
        self.read_serial_thread.daemon = True
        self.read_serial_thread.start()
    
    def set_angle(self, ith, angle, speed, block=True):
        s = '{0} {1:.3f} {2:.3f}\n'.format(ith, angle, speed)
        with self.lock_serial:
            for char in s:
                self.serial.write(char)
                time.sleep(0.001)
            
        if block:
            q = self.read_queues[ith]
            with q.mutex:
                q.queue.clear()
            return self.get_angle_and_time(ith)
        
    def read_serial_run(self):
        while not self.read_stop:
            try:
                line = self.serial.readline()
            except Exception:
                time.sleep(0.001)
                continue
            if len(line) == 0:
                continue
            servo_num, angle, t = line.split('_')

            servo_num = int(servo_num)
            angle = float(angle)
            t = float(t)

            #print('servo_num: {0}'.format(servo_num))
            #print('angle: {0}'.format(angle))
            #print('t: {0}\n'.format(t))
            self.read_queues[servo_num].put((angle, t))
            
    def get_angle_and_time(self, ith):
        return self.read_queues[ith].get()
    

########
# TEST #
########
if __name__ == '__main__':
    pass

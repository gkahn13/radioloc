from utils import *

class Servos:
    """
    Commands servos via serial port
    """
    
    def __init__(self, num_servos, port, baudrate=115200, offset=0.0):
        self.offset = offset
        self.min_angle = -np.pi/4.
        self.max_angle = np.pi/4.
        
        self.num_servos = num_servos
        self.serial = serial.Serial(port, baudrate=baudrate)
        self.curr_angles = [0]*self.num_servos
        self.set_angles(self.curr_angles)
    
    def is_valid_angles(self, angles):
        is_valid = len(angles) == self.num_servos
        for angle in angles:
            is_valid = is_valid and (self.min_angle <= angle <= self.max_angle)
            if not is_valid:
                print('WARNING: angle {0} not in [{1},{2}]'.format(angle, self.min_angle, self.max_angle))
        return is_valid
    
    def get_angles(self):
        return list(self.curr_angles)
        
    def set_angles(self, des_angles, speed=None, fs=100.):
        """
        :param des_angle: desired angles (radians). None means don't move
        :param speed: if None, go as fast as possible. Else rad/s
        :param fs: if speed is not None, command discretization
        """
        des_angles = list(des_angles)
        for i, des_angle in enumerate(des_angles):
            if des_angle is None:
                des_angles[i] = self.curr_angles[i]
        
        if speed is None:
            self.write(des_angles)
        else:
            angle_trajs = list()
            # create trajectories
            for curr_angle, des_angle in zip(self.curr_angles, des_angles):
                sign = 1 if des_angle > curr_angle else -1
                angle_traj = [curr_angle] + list(np.r_[curr_angle:des_angle:sign*speed/fs])
                angle_trajs.append(angle_traj)
            
            # make them all the same length
            max_angle_traj_len = max(len(traj) for traj in angle_trajs)
            for i, traj in enumerate(angle_trajs):
                pad_len = max_angle_traj_len - len(traj)
                if pad_len > 0:
                    angle_trajs[i] = np.pad(np.array(traj), (1, pad_len-1), 'edge')
                
            angle_trajs = np.array(angle_trajs).T
            for angles in angle_trajs:
                self.write(angles, fs)
            
    def write(self, angles, fs=100.):
        """
        :param angles: list of desired angles
        :param fs: how long to sleep between writes
        """
        if not self.is_valid_angles(angles):
            return
        
        write_str = ''
        for i, angle in enumerate(angles):
            if angle is None:
                angle = self.curr_angles[i]
            write_str = '{0}{1:.2f}\n'.format(i, self.offset+angle)
            self.serial.write(write_str)
            time.sleep(1/(self.num_servos*fs))
            self.curr_angles[i] = angle
        
########
# TEST #
########
if __name__ == '__main__':
    servos = Servos(3, '/dev/ttyACM1')
    
    curr_angles = servos.get_angles()
    des_angles = [0., 0., 0.]
    speed = 0.5
    expected_time = abs(des_angles[0] - curr_angles[0])/speed

    start = time.time()
    servos.set_angles(des_angles, speed=speed)
    end = time.time()

    print('Expected time: {0}'.format(expected_time))
    print('Elapsed: {0}'.format(end - start))
    

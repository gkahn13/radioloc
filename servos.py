from utils import *

class Servos:
    """
    Commands servos via serial port
    """
    
    def __init__(self, num_servos, port, baudrate=115200, offset=0.0):
        self.offset = offset
        self.min_angle = -np.pi/3
        self.max_angle = np.pi/3
        
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
        
    def set_angles(self, des_angles, speed=None, fs=200.):
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
            def is_done(start, curr, des):
                if (start <= des) and (curr >= des):
                    return True
                if (start >= des) and (curr <= des):
                    return True
                return False
            
            def pos(start, des, speed, elapsed):
                sign = 1 if des > start else -1
                return start + sign*speed*elapsed
            
            start_angles = list(self.curr_angles)
            des_angles = list(des_angles)
            start_time = time.time()
            while True:
                is_all_done = True
                write_angles = list()
                for start, curr, des in zip(start_angles, self.curr_angles, des_angles):
                    done = is_done(start, curr, des)
                    is_all_done = is_all_done and done
                    
                    if not done:
                        write_angles.append(pos(start, des, speed, time.time()-start_time))
                    else:
                        write_angles.append(des)
                        
                self.write(write_angles, fs=fs)
                    
                if is_all_done:
                    break
            
    def write(self, angles, fs=100.):
        """
        :param angles: list of desired angles
        :param fs: how long to sleep between writes
        """
        #if not self.is_valid_angles(angles):
        #    return
        angles = np.clip(angles, self.min_angle, self.max_angle)
        
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
    servos = Servos(3, '/dev/ttyACM0')
    curr_angles = servos.get_angles()
    des_angles = [0.5, 0., 0.]
    speed = 0.5
    expected_time = abs(des_angles[0] - curr_angles[0])/speed

    start = time.time()
    servos.set_angles(des_angles, speed=speed)
    end = time.time()

    print('Expected time: {0}'.format(expected_time))
    print('Elapsed: {0}'.format(end - start))
    

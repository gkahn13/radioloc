from utils import *

class MapProbability:
    
    def __init__(self, locs, orientations, grid_size):
        """
        locs: list of locations
        orientations: list of orientations
        """
        self.locs = locs
        self.orientations = orientations
        self.grid_size = grid_size
        self.grid = None
        
        self.fig, self.ax = plt.subplots()
        plt.xticks(np.r_[0:grid_size])
        plt.yticks(np.r_[0:grid_size])
        self.ax.grid(which='major', axis='x', linewidth=0.75, linestyle='-', color='0.5')
        self.ax.grid(which='major', axis='y', linewidth=0.75, linestyle='-', color='0.5')
        self.imshow_obj = plt.imshow(np.zeros((self.grid_size, self.grid_size)), origin='lower', interpolation='nearest')
        self.cb = plt.colorbar()
        plt.ion()
        plt.draw()
        plt.pause(0.01)
    
    def update_probability(self, ith, angle, prob):
        """
        update internal probability distribution for ith sdr given angle/prob
        """
        grid = MapProbability.rotate_spec(angle, prob, self.grid_size, self.locs[ith], self.orientations[ith])
        if self.grid is None:
            self.grid = np.array(grid)
        else:
            self.grid = np.multiply(self.grid, grid)
    
    
    def get_probabililty(self):
        return self.grid
    
    @staticmethod
    def rotate_spec(angle, prob_dist, grid_size, loc, offset):
        grid = [[0 for x in np.r_[0:grid_size]] for x in np.r_[0:grid_size]] 
        for i in np.r_[0:grid_size]:  #row
            for j in np.r_[0:grid_size]: #column
                if j == loc[1]:
                    if i < loc[0]:
                        cell_angle = -np.pi/2
                    else:
                        cell_angle = np.pi/2
                else:
                    cell_angle = np.arctan(float((i-loc[0]))/float((j-loc[1])))
                    if (i<loc[0]) and (j<loc[1]):
                        cell_angle = cell_angle - np.pi
                    if (i> loc[0]) and (j< loc[1]):
                        cell_angle = cell_angle

                cell_angle = cell_angle + offset

                if cell_angle > np.pi:
                    cell_angle = cell_angle - 2*np.pi
                elif cell_angle < -np.pi:
                    cell_angle = cell_angle + 2*np.pi

                # finding the closest point in angle
                index = np.argmin(abs(angle-cell_angle))

                if min(angle) <= cell_angle <= max(angle):
                    grid[i][j] = prob_dist[index]
                else:
                    grid[i][j] = 0

        return grid
        
    def draw_map(self):
        plt.sca(self.ax)
        self.imshow_obj.set_data(self.grid)
        self.cb.set_clim(vmin=self.grid.min(),vmax=self.grid.max())
        self.cb.draw_all() 
        plt.draw()
        plt.pause(0.1)
    

if __name__ == '__main__':
    grid_size = 100
    locs = np.array([[50, 50], [50, 25], [50, 75]])
    orientations = np.array([np.pi/2., 0, 0])

    map_prob = MapProbability(locs, orientations, grid_size)
    
    ith = 0
    angle = np.linspace(-np.pi/4., np.pi/4., 100)
    prob = np.ones(len(angle)) / len(angle)
    map_prob.update_probability(ith, angle, prob)
    map_prob.draw_map()
    
    print('Press enter to exit')
    raw_input()

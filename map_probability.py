from utils import *

class MapProbability:
    
    def __init__(self, physical_locs, orientations, discretization, grid_physical_size, hist_len=5):
        """
        physical_locs: list of locations in m
        orientations: list of orientations
        discretization: m/grid
        physical_grid_size: max length of grid in m
        """
        self.locs = list(map(lambda k: (int(k[0]/discretization),
                                        int(k[1]/discretization)), physical_locs))
        self.orientations = orientations
        self.discretization = discretization
        self.grid_size = int(grid_physical_size / float(discretization))
        
        uniform = np.ones((self.grid_size,self.grid_size),dtype=float)/(self.grid_size*self.grid_size)

        self.last_probs = [[np.ones((self.grid_size,self.grid_size),dtype=float)/(self.grid_size*self.grid_size)]*hist_len for _ in self.locs]
        self.grids = [None]*(len(self.locs)+1)
        self.grids_lock = threading.RLock()
        self.imshow_objs = []
        self.cbs = []
        
        for ith in xrange(len(self.locs)+1):
            self.grids[ith] = uniform.copy()
        
        self.fig, self.axes = plt.subplots(2,1+len(self.locs))
        for ax in self.axes.reshape(-1):
            plt.sca(ax)
            self.imshow_objs.append(plt.imshow(uniform, origin='lower', interpolation='nearest'))
            self.cbs.append(plt.colorbar(shrink=0.25))
            plt.ion()
            plt.draw()
            plt.pause(0.01)
            
        
    def update_probability(self, ith, angle, prob):
        """
        update internal probability distribution for ith sdr given angle/prob
        """
        self.last_probs[ith].pop()
        self.last_probs[ith].insert(0, MapProbability.rotate_spec(angle, prob, self.grids[ith+1], self.locs[ith], self.orientations[ith]))
        with self.grids_lock:
            g = np.ones(self.last_probs[ith][0].shape)
            for p in self.last_probs[ith]:
                g *= p
            self.grids[ith+1] = g / g.sum()
            
    def get_total_probability(self):
        with self.grids_lock:
            grid = self.grids[0]
            for g in self.grids[1:]:
                grid += g # TODO: add or mult?
            if (grid > 0).any():
                grid /= grid.sum()
        return grid
        
    def get_last_probability(self, ith):
        return self.last_probs[ith][0].copy()
    
    def get_probability(self, ith):
        return self.grids[ith+1].copy()
    
    @staticmethod
    def rotate_spec(angle, prob_dist, prev_grid, loc, offset):
        grid = prev_grid.copy()
        for i in xrange(grid.shape[0]):  #row
            for j in xrange(grid.shape[1]): #column
                if j == loc[1]:
                    if i < loc[0]:
                        cell_angle = -np.pi/2
                    else:
                        cell_angle = np.pi/2
                else:
                    cell_angle = np.arctan2(i-loc[0], j-loc[1])

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

        grid[np.isnan(grid)] = 0
        if (grid > 0).any():
            grid /= grid.sum()
        return grid
        
    def draw_last_map(self, ith):
        self.draw_imshow(self.axes[0,ith+1], self.imshow_objs[ith+1], \
                                    self.cbs[ith+1], self.get_last_probability(ith))
        plt.title('Last map {0}'.format(ith))
        
    def draw_history_map(self, ith=None):
        if ith is None:
            plot_num = 0
            grid = self.get_total_probability()
        else:
            plot_num = ith+1
            grid = self.get_probability(ith)
            
        o = len(self.locs)+1
        self.draw_imshow(self.axes[1,plot_num], self.imshow_objs[o+plot_num], \
                                    self.cbs[o+plot_num], self.grids[plot_num])
        if plot_num == 0:
            max_prob = np.unravel_index(grid.argmax(), grid.shape)
            plt.title('Combined history map: Max_prob at ({0:.2f}, {1:.2f})'.format(max_prob[0]*self.discretization, max_prob[1]*self.discretization))
            # plt.plot(max_prob[0], max_prob[1], 'kx', markersize=2.0)
        else:
            plt.title('History map {0}'.format(plot_num))
            
    def draw_imshow(self, ax, imshow_obj, cb, grid):
        with self.grids_lock:
            plt.sca(ax)
        
            imshow_obj.set_data(grid)
            cb.set_clim(vmin=grid.min(),vmax=grid.max())
            cb.draw_all()
            
            #plt.draw()
            plt.pause(0.01)
    

if __name__ == '__main__':
    physical_grid_size = 15
    locs = np.array([[5, 5], [5, 7], [10, 2]])
    orientations = np.array([-np.pi/2., -np.pi, 0])
    discretization = 1.5
    map_prob = MapProbability(locs, orientations, discretization, physical_grid_size)

    ith = 0
    angle = np.linspace(-np.pi/4., np.pi/4., 100)
    prob0 = np.ones(len(angle)) / len(angle)
    prob1 = np.cos(angle)
    prob1 /= prob1.sum()

    map_prob.update_probability(0, angle, prob0)
    map_prob.update_probability(1, angle, prob1)
    start = time.time()
    for ith in [0, 1]:
        map_prob.draw_last_map(ith)
        map_prob.draw_history_map(ith)
    map_prob.draw_history_map()

    print('Draw time: {0}'.format(time.time()-start))
    print('Press enter to exit')
    raw_input()

from utils import *

def force_aspect(ax,aspect=1):
    im = ax.get_images()
    extent =  im[0].get_extent()
    ax.set_aspect(abs((extent[1]-extent[0])/(extent[3]-extent[2]))/aspect)

def fast_plotter(ax, im_obj, Z):
    canvas = ax.figure.canvas
    #background = canvas.copy_from_bbox(ax.bbox)
    #canvas.restore_region(background)
    im_obj.set_data(Z)
    ax.draw_artist(im_obj)
    #canvas.blit(ax.bbox)
    #canvas.gui_repaint()

class MapProbability:
    
    def __init__(self, locs, orientations, grid_size):
        """
        locs: list of locations
        orientations: list of orientations
        """
        self.locs = locs
        self.orientations = orientations
        self.grid_size = grid_size
        self.grids = [None]*(len(locs)+1)
        self.grids_lock = threading.RLock()
        self.imshow_objs = [None]*(len(locs)+1)
        self.cbs = [None]*(len(locs)+1)
        
        for ith in xrange(len(locs)+1):
            self.grids[ith] = np.ones((self.grid_size,self.grid_size),dtype=float)/(grid_size*grid_size)
        
        self.fig, self.axes = plt.subplots(1,1+len(locs))
        for ith, ax in enumerate(self.axes):
            plt.sca(ax)
            plt.xticks(np.r_[0:grid_size])
            plt.yticks(np.r_[0:grid_size])
            ax.grid(which='major', axis='x', linewidth=0.75, linestyle='-', color='0.5')
            ax.grid(which='major', axis='y', linewidth=0.75, linestyle='-', color='0.5')
            self.imshow_objs[ith] = plt.imshow(self.grids[ith], origin='lower', interpolation='nearest')
            #ax.pcolormesh(self.grids[ith])
            #ax.set_aspect('equal', 'datalim')
            #force_aspect(ax)
            self.cbs[ith] = plt.colorbar(shrink=0.25)
            plt.ion()
            plt.draw()
            plt.pause(0.01)
            
        self.backgrounds = [self.fig.canvas.copy_from_bbox(ax.bbox) for ax in self.axes]
    
    def update_probability(self, ith, angle, prob):
        """
        update internal probability distribution for ith sdr given angle/prob
        """
        grid, loc, orientation = self.grids[ith+1].copy(), self.locs[ith], self.orientations[ith]
        valid = np.zeros(grid.shape, dtype=bool)
        for i in np.r_[:grid.shape[0]]:  #row
            for j in np.r_[:grid.shape[1]]: #column
                if j == loc[1]:
                    if i < loc[0]:
                        cell_angle = -np.pi/2
                    else:
                        cell_angle = np.pi/2
                else:
                    cell_angle = np.arctan2(i-loc[0], j-loc[1])

                cell_angle = cell_angle + orientation

                if cell_angle > np.pi:
                    cell_angle = cell_angle - 2*np.pi
                elif cell_angle < -np.pi:
                    cell_angle = cell_angle + 2*np.pi

                # finding the closest point in angle
                index = np.argmin(abs(angle-cell_angle))

                if min(angle) <= cell_angle <= max(angle):
                    valid[i,j] = True
                    grid[i,j] *= prob[index]
                else:
                    #valid[i,j] = False
                    grid[i,j] = 0
        
        #grid[valid] /= grid[valid].sum()
        #grid[True-valid] /= grid[True-valid].sum()
        grid /= grid.sum()
        self.grids[ith+1] = grid
        
        #grid = MapProbability.rotate_spec(angle, prob, self.grids[ith+1], self.locs[ith], self.orientations[ith])
        #with self.grids_lock:
        #    self.grids[ith+1] *= grid
        #    self.grids[ith+1] /= self.grids[ith+1].sum()
    
    def get_total_probability(self):
        with self.grids_lock:
            grid = self.grids[0]
            for g in self.grids[1:]:
                grid *= g
            grid /= grid.sum()
        return grid
    
    def get_probability(self, ith):
        return self.grids[ith+1]
    
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

        return grid
        
    def draw_map(self, ith=None):
        if ith is None:
            plot_num = 0
            grid = self.get_total_probability()
        else:
            plot_num = ith+1
            grid = self.get_probability(ith)
            
        with self.grids_lock:
            plt.sca(self.axes[plot_num])
            #self.axes[plot_num].pcolormesh(grid)
            #self.axes[plot_num].set_aspect('equal', 'datalim')
            #force_aspect(self.axes[plot_num])
            
            #self.fig.canvas.restore_region(self.backgrounds[plot_num])
            self.imshow_objs[plot_num].set_data(grid)
            self.cbs[plot_num].set_clim(vmin=grid.min(),vmax=grid.max())
            self.cbs[plot_num].draw_all() 
            #self.axes[plot_num].draw_artist(self.imshow_objs[plot_num])
            #self.fig.canvas.blit(self.axes[plot_num].bbox)
            
            plt.draw()
            plt.pause(0.01)
    

if __name__ == '__main__':
    grid_size = 20
    locs = np.array([[10, 5], [10, 10], [10, 15]])
    orientations = np.array([-np.pi/2., -np.pi, 0])

    map_prob = MapProbability(locs, orientations, grid_size)
    
    ith = 0
    angle = np.linspace(-np.pi/4., np.pi/4., 100)
    prob0 = np.ones(len(angle)) / len(angle)
    prob1 = np.cos(angle)
    prob1 /= prob1.sum()
    
    map_prob.update_probability(0, angle, prob0)
    map_prob.update_probability(1, angle, prob1)
    start = time.time()
    map_prob.draw_map(0)
    map_prob.draw_map(1)
    map_prob.draw_map()
    
    print('Draw time: {0}'.format(time.time()-start))
    print('Press enter to exit')
    raw_input()

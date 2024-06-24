# -*- coding: utf-8 -*-
"""
Created on Fri May 14 08:29:33 2021

@author: jdconey
"""

import xarray
import iris
import matplotlib.pyplot as plt
from matplotlib.widgets import Lasso
from matplotlib.collections import RegularPolyCollection
from matplotlib import path
import matplotlib.patches as mpatches
import numpy as np
#file = '20210206T0900Z-PT0000H00M-wind_vertical_velocity_on_pressure_levels.nc'

def get_variables(fname):
    """
    Function to return a list of the variables within a given netCDF file

    Parameters
    ----------
    fname: str
        path to file where netCDF is located

    Returns
    -------
    list
        list of strings containing the variables.

    """
    x = xarray.open_dataset(fname)
    variables  = x.variables.mapping
    return list(variables.keys())

def load_xarray(fname,var):
    """
    Function to read in a netCDF file as an xarray Dataset, and return a DataArray, specified by var
    If var not present in the Dataset then the entire Dataset is returned.

    Parameters
    ----------
    fname : str
        path to file where netCDF is located
    var : str
        variable of the Dataset you're interested in, e.g. 'upward_air_velocity'.
        var must be one of the variables in the Dataset!

    Returns
    -------
    x : xarray DataArray/Dataset
    DataArray from file, of var
    if var not present in the Dataset then the entire Dataset is returned.
    
    """
    x = xarray.open_dataset(fname)
    if var in get_variables(fname):
        x = x[var]
    else:
        print(var+ ' not in variables of '+fname)
        print('returning entire Dataset')
    
    return x

def get_proj(fname):
    """
    Get cartopy projection of a dataset from a netCDF file
    Parameters
    ----------
    fname : str
        path to file where netCDF is located

    Returns
    -------
    cubes_crs : crs projection
        cartopy projection. Useful for plotting other data on top etc.

    """
    cubes = iris.load_cube(fname)
    cubes_crs = cubes.coord_system().as_cartopy_crs()
    return cubes_crs

def check_data(data):
    """
    Check whether input data is 2D

    Parameters
    ----------
    data : DataArray
        Usually generated by load_xarray fn.

    """
    if len(data.shape)==2:
        print('Dimensions of DataArray is 2D. Go wild.')
    else:
        print('dimension of DataArray is '+str(len(data.shape))+'. DataArray must be 2D.')

def mask_create(data_array,proj,lman,xcoord='projection_x_coordinate',ycoord='projection_y_coordinate'):
    """
    Generate binary mask based on regions drawn on interactive matplotlib figure

    Parameters
    ----------
    data_array : xarray DataArray
        The raw data
    proj : ccrs projection
        cartopy projection of data_array; can be found using get_proj fn.
    lman : LassoManager object as defined below
        Collection of lassos drawn using the interactive matplotlib figure.
    xcoord : str, optional
        x coordinate of the DataArray. The default is 'projection_x_coordinate'.
    ycoord : str, optional
        y coordinate of the DataArray. The default is 'projection_y_coordinate'.

    Returns
    -------
    mask : numpy array
        mask in the same dimensions as the DataArray, with a mask as shown by the Lasso.

    """
    xs = data_array.coords[xcoord].values
    ys = data_array.coords[ycoord].values
    lenx = int(len(xs))
    leny = int(len(ys))
    distx = (max(xs)-min(xs))/(lenx-1)
    disty = (max(ys)-min(ys))/(leny-1)
    
    x, y = np.meshgrid(np.arange(min(xs),max(xs)+distx,distx), np.arange(min(ys),max(ys)+disty,disty)) # make a canvas with coordinates
    x, y = x.flatten(), y.flatten()
    points = np.vstack((x,y)).T 
    grids=[]
    for p in lman.paths:
       # p = lman.paths[0] # make a polygon
        grid = p.contains_points(points)
        grids.append(grid)
    if len(grids)>0:
        if len(grids)==1:
            full = grids[0]
        elif len(grids)==2:
            full = grids[0]+grids[1]
        else:
            full = grids[0]+grids[1]
            i=2
            while i<len(grids):
                full = full + grids[i]
                i=i+1
       # return [len(xs),len(ys),min(xs),max(xs),min(ys),max(ys),lenx,leny,full]
        mask = full.reshape(len(xs),len(ys)) # now you have a mask with points inside a polygon
        return mask
    else:
        return np.zeros((len(xs),len(ys)))
    
def combine_data_and_mask(data_array,mask,xcoord='projection_x_coordinate',ycoord='projection_y_coordinate'):
    """
    Combine DataArray and numpy mask into one Dataset, for future plotting etc

    Parameters
    ----------
    data_array : xarray DataArray
        as imported by load_xarray fn.
    mask : np array
        as generated by mask_create function.
    xcoord : str, optional
        x coordinate of data_array. The default is 'projection_x_coordinate'.
    ycoord : str, optional
        y coordinate of data_array. The default is 'projection_y_coordinate'.

    Returns
    -------
    dataset : xarray Dataset
        combination of raw data and truth mask.

    """
    dataset = xarray.Dataset({'data': data_array, 'mask': ((ycoord, xcoord), mask)})
    return dataset

def plot_dataset(dataset,proj,robust=False):
    fig = plt.figure(figsize=(10.5,9))
    ax1 = fig.add_subplot(111,projection=proj)
    dataset['data'].plot.pcolormesh(cmap='seismic',robust=robust,rasterized=True,)#vmin=-4,vmax=4)
    dataset['mask'].plot.contour(cmap='Oranges',alpha=1)
    ax1.coastlines(resolution='10m',alpha=1,zorder=2)
    plt.show()

class LassoManager(object):

    """
    This class has been amended from 
    https://stackoverflow.com/questions/23347392/getting-lasso-to-work-correctly-on-subplots-in-matplotlib.
    
    Show how to use a lasso to select a set of points and get the indices
    of the selected points.  A callback is used to change the color of the
    selected points
    
    This is currently a proof-of-concept implementation (though it is
    usable as is).  There will be some refinement of the API.
    """
    paths=[]
    def __init__(self, ax, data):
        self.axes = ax
        self.canvas = ax.figure.canvas
        self.data = data

        self.Nxy = len(data)

     #   facecolors = [d.color for d in data]
  #      self.xys = [(d.x, d.y) for d in data]
        fig = ax.figure
        self.collection = RegularPolyCollection(
            fig.dpi, 6, sizes=(100,),
      #      facecolors=facecolors,
      #      offsets = self.xys,
            transOffset = ax.transData)

        ax.add_collection(self.collection)

        self.cid = self.canvas.mpl_connect('button_press_event', self.onpress)

    def callback(self, verts):
    #    facecolors = self.collection.get_facecolors()
        p = path.Path(verts)
        self.paths.append(p)
       # codes, verts = zip(*p)
        string_path = p
        patch = mpatches.PathPatch(string_path, facecolor="none", lw=2,edgecolor='red')

        self.axes.add_patch(patch)
        self.canvas.draw_idle()
        self.canvas.widgetlock.release(self.lasso)
        del self.lasso

    def onpress(self, event):
        if self.canvas.widgetlock.locked(): return
        if event.inaxes is None: return
        self.lasso = Lasso(event.inaxes, (event.xdata, event.ydata), self.callback)
        # acquire a lock on the widget drawing
        self.canvas.widgetlock(self.lasso)

from matplotlib import pyplot as plt
import numpy as np
import itertools

from autolens import exc
from autolens.plotting import tools

def plot_grid(grid, axis_limits=None, points=None, as_subplot=False,
              units='arcsec', kpc_per_arcsec=None,
              figsize=(12, 8), pointsize=5, xyticksize=16,
              title='Grid', titlesize=16, xlabelsize=16, ylabelsize=16,
              output_path=None, output_format='show', output_filename='grid'):

    tools.setup_figure(figsize=figsize, as_subplot=as_subplot)
    plt.scatter(y=grid[:, 0], x=grid[:, 1], s=pointsize, marker='.')
    tools.set_title(title=title, titlesize=titlesize)
    set_xy_labels_and_ticks_in_arcsec(units, kpc_per_arcsec,grid.xticks, grid.yticks, xlabelsize, ylabelsize,
                                      xyticksize)

    set_axis_limits(axis_limits)
    plot_points(grid, points)

    plt.tick_params(labelsize=xyticksize)
    tools.output_figure(None, as_subplot, output_path, output_filename, output_format)
    tools.close_figure(as_subplot=as_subplot)

def set_xy_labels_and_ticks_in_arcsec(units, kpc_per_arcsec, xticks, yticks, xlabelsize, ylabelsize, xyticksize):

    if units is 'arcsec' or kpc_per_arcsec is None:

        plt.yticks(np.round(yticks, 1))
        plt.xticks(np.round(xticks, 1))
        plt.xlabel('x (arcsec)', fontsize=xlabelsize)
        plt.ylabel('y (arcsec)', fontsize=ylabelsize)

    elif units is 'kpc':

        plt.xticks(np.round(kpc_per_arcsec * xticks, 1))
        plt.yticks(np.round(kpc_per_arcsec * yticks, 1))
        plt.xlabel('x (kpc)', fontsize=xlabelsize)
        plt.ylabel('y (kpc)', fontsize=ylabelsize)

    else:
        raise exc.VisualizeException('The units supplied to the plotted are not a valid string (must be pixels | '
                                     'arcsec | kpc)')

    plt.tick_params(labelsize=xyticksize)

def set_axis_limits(axis_limits):

    if axis_limits is not None:
        plt.axis(axis_limits)

def plot_points(grid, points):

    if points is not None:
        point_colors = itertools.cycle(["y", "r", "k", "g", "m"])
        for point_set in points:
            plt.scatter(y=grid[point_set, 0], x=grid[point_set, 1], s=8, color=next(point_colors))
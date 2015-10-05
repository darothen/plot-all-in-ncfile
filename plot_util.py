"""
Plotting utility functions.

"""

import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

import numpy as np

import xray
from xray.plot.utils import _determine_cmap_params

import warnings

# Some default plotting arguments; not really used in this script
# but taken from my plotting toolkit along with geo_plot and
# add_colorbar.
_PLOTTYPE_ARGS = {
    'pcolormesh': dict(linewidth='0'),
    'pcolor': dict(linewidth='0'),
    'contourf': dict(),
}


def add_colorbar(mappable, fig=None, ax=None, thickness=0.025,
                 shrink=0.1, pad=0.05, orientation='horizontal'):
    """ Add a colorbar into an existing axis or figure. Need to pass
    either an Axis or Figure element to the appropriate keyword
    argument. Should elegantly handle multi-axes figures.

    Parameters
    ----------
    mappable : mappable
        The element set with data to tailor to the colorbar
    fig : Figure
    ax: Axis
    thickness: float
        The width/height of the colorbar in fractional figure area,
        given either vertical/horizontal orientation.
    shrink: float
        Fraction of the width/height of the figure to leave blank
    pad : float
        Padding between bottom/right subplot edge and the colorbar
    orientation : str
        The orientation of the colorbar

    """
    if (fig is None) and (ax is None):
        raise ValueError("Must pass either 'fig' or 'ax'")
    elif fig is None:
        # Plot on Axis
        cb = plt.colorbar(mappable, ax=ax, pad=pad, orientation=orientation)
    else:
        # Plot onto Figure's set of axes
        axes = fig.get_axes()

        # Get coordinates for making the colorbar
        ul = axes[0]
        lr = axes[-1]
        top = ul.get_position().get_points()[1][1]
        bot = lr.get_position().get_points()[0][1]
        right = lr.get_position().get_points()[1][0]
        left = ul.get_position().get_points()[0][0]

        # Calculate colorbar positioning and geometry
        if orientation ==  'vertical':
            cb_left = right + pad
            cb_width = thickness
            cb_bottom = bot + shrink
            cb_height = (top - shrink) - cb_bottom
        elif orientation == 'horizontal':
            cb_left = left + shrink
            cb_width = (right - shrink) - cb_left
            cb_height = thickness
            cb_bottom = (bot - pad) - cb_height
        else:
            raise ValueError("Uknown orientation '%s'" % orientation)

        cax = fig.add_axes([cb_left, cb_bottom,
                            cb_width, cb_height])
        cb = fig.colorbar(mappable, cax=cax, orientation=orientation)

    return cb


def check_cyclic(data, coord='lon'):
    """ Checks if a DataArray already includes a cyclic point along the
    specified coordinate axis. If not, adds the cyclic point and returns
    the modified DataArray.

    """
    return np.all(data.isel(**{coord: 0}) == data.isel(**{coord: -1}))


def cyclic_dataarray(da, coord='lon'):
    """ Add a cyclic coordinate point to a DataArray along a specified
    named coordinate dimension.

    >>> from xray import DataArray
    >>> data = DataArray([[1, 2, 3], [4, 5, 6]],
    ...                      coords={'x': [1, 2], 'y': range(3)},
    ...                      dims=['x', 'y'])
    >>> cd = cyclic_dataarray(data, 'y')
    >>> print cd.data
    array([[1, 2, 3, 1],
           [4, 5, 6, 4]])
    """
    assert isinstance(da, xray.DataArray)

    lon_idx = da.dims.index(coord)
    cyclic_data, cyclic_coord = add_cyclic_point(da.values,
                                                 coord=da.coords[coord],
                                                 axis=lon_idx)

    # Copy and add the cyclic coordinate and data
    new_coords = dict(da.coords)
    new_coords[coord] = cyclic_coord
    new_values = cyclic_data

    new_da = xray.DataArray(new_values, dims=da.dims, coords=new_coords)

    # Copy the attributes for the re-constructed data and coords
    for att, val in da.attrs.items():
        new_da.attrs[att] = val
    for c in da.coords:
        for att in da.coords[c].attrs:
            new_da.coords[c].attrs[att] = da.coords[c].attrs[att]

    return new_da


def geo_plot(darray, ax=None, method='contourf',
             projection='PlateCarree', grid=False, **kwargs):
    """ Create a global plot of a given variable.

    Parameters:
    -----------
    darray : xray.DataArray
        The darray to be plotted.
    ax : axis
        An existing axis instance, else one will be created.
    method : str
        String to use for looking up name of plotting function via iris
    projection : str or tuple
        Name of the cartopy projection to use and any args
        necessary for initializing it passed as a dictionary;
        see func:`make_geoaxes` for more information
    grid : bool
        Include lat-lon grid overlay
    **kwargs : dict
        Any additional keyword arguments to pass to the plotter,
        including colormap params. If 'vmin' is not in this
        set of optional keyword arguments, the plot colormap will be
        automatically inferred.

    """

    # Set up plotting function
    if method in _PLOTTYPE_ARGS:
        extra_args = _PLOTTYPE_ARGS[method].copy()
    else:
        raise ValueError("Don't know how to deal with '%s' method" % method)
    extra_args.update(**kwargs)

    # Alias a plot function based on the requested method and the
    # datatype being plotted
    plot_func = plt.__dict__[method]

    # `transform` should be the ORIGINAL coordinate system -
    # which is always a simple lat-lon coordinate system in CESM
    # output
    extra_args['transform'] = ccrs.PlateCarree()

    # Was an axis passed to plot on?
    new_axis = ax is None

    if new_axis: # Create a new cartopy axis object for plotting
        if isinstance(projection, (list, tuple)):
            if len(projection) != 2:
                raise ValueError("Expected 'projection' to only have 2 values")
            projection, proj_kwargs = projection[0], projection[1]
        else:
            proj_kwargs = {}

        # hack to look up the name of the projection in the cartopy
        # reference system namespace; makes life a bit easier, so you
        # can just pass a string with the name of the projection wanted.
        proj = ccrs.__dict__[projection](**proj_kwargs)
        ax = plt.axes(projection=proj)
    else: # Set current axis to one passed as argument
        if not hasattr(ax, 'projection'):
            raise ValueError("Expected `ax` to be a GeoAxes instance")
        plt.sca(ax)

    # Setup map
    ax.set_global()
    ax.coastlines()

    try:
        gl = ax.gridlines(crs=extra_args['transform'], draw_labels=True,
                          linewidth=0.5, color='grey', alpha=0.8)
        LON_TICKS = [ -180, -90, 0, 90, 180 ]
        LAT_TICKS = [ -90, -60, -30, 0, 30, 60, 90 ]
        gl.xlabels_top   = False
        gl.ylabels_right = False
        gl.xlines = grid
        gl.ylines = grid
        gl.xlocator = mticker.FixedLocator(LON_TICKS)
        gl.ylocator = mticker.FixedLocator(LAT_TICKS)
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
    except TypeError:
        warnings.warn("Could not label the given map projection.")

    # Infer colormap settings if not provided
    if not ('vmin' in kwargs):
        warnings.warn("Re-inferring color parameters...")
        cmap_kws = _determine_cmap_params(darray.data)
        extra_args.update(cmap_kws)

    gp = plot_func(darray.lon.values, darray.lat.values, darray.data,
                   **extra_args)

    return ax, gp
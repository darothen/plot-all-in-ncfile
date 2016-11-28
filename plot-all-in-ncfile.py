#!/usr/bin/env python
"""
plot_ncfile.py - For each (or given) variables in a netCDF file,
plot each timestamp.

Author: Daniel Rothenberg <darothen@mit.edu>
Date: November 28, 2016

"""

import argparse
import os
import pickle
import sys
import warnings

import cartopy.crs as ccrs

import matplotlib.pyplot as plt
plt.ioff() # turn off interactive plotting for expediency

import pandas as pd

import xarray
from xarray.plot.utils import _determine_cmap_params

from plot_util import *

DESCR = """
Plot snapshots from subsets of variables from a given netCDF file.

To help produce consistent plot formats, supports the serialization of
colormap settings. By default, the script will save a "colorfile" with
the same name as the netCDF file being plotted. This "colorfile" is
just a serialized Python dictionary containing a map from each variable
name in the file to a dictionary of the colormap arguments inferred
during the plotting process.
"""

parser = argparse.ArgumentParser("plot-all-in-ncfile.py",
                                 description=DESCR,
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("nc_file", help="netCDF file to extract data from")
parser.add_argument("-v", "--variables", nargs="*",
                    help="Variables to try to plot; if not supplied,\n"
                         "will plot all 2D variables in file")
parser.add_argument("-c", "--colorfile", type=str,
                    help="File containing the colormap dictionary")
parser.add_argument("--sample", action='store_true',
                    help="Only plot the first timestep for each variable.")

if __name__ == "__main__":
    args = parser.parse_args()

    # Read the given netCDF file
    fn_in = args.nc_file
    try:
        dataset = xray.open_dataset(fn_in, decode_cf=True,
                                    decode_coords=True, mask_and_scale=True)
    except RuntimeError:
        print("Could not open netCDF file '%s'" % fn_in)
        sys.exit(1)
    print("Input file details:")
    for attr, val in dataset.attrs.items():
        print("   " + "%s: %s" % (attr, val))

    # As a safety check, coerce dimension names
    # ['longitude', ] -> 'lon'
    # ['latitude', ] -> 'lat'
    if 'longitude' in dataset:
        dataset.rename({'longitude': 'lon', },
                       inplace=True)
    if 'latitude' in dataset:
        dataset.rename({'latitude': 'lat', },
                       inplace=True)


    # Read colorfile arguments; else, infer the color parameters
    if args.colorfile is not None:
        colorfile = args.colorfile
        try:
            with open(colorfile, 'rb') as f:
                color_data = pickle.load(f)
        except (FileNotFoundError, IOError):
            print("Could not open colorfile '%s'" % args.colorfile)
            sys.exit(1)

        # Warn about variables where color will be freshly inferred
        for v in dataset.variables:
            if v in dataset.dims: continue
            if not (v in color_data):
                warnings.warn("Couldn't find color data for %s" % v)
                color_data[v] = _determine_cmap_params(dataset[v].data)
    else:
        print("Inferring new colormaps")

        color_data = {}
        for v in dataset.variables:
            if v in dataset.dims: continue
            print("   " + v)
            color_data[v] = _determine_cmap_params(dataset[v].data,
                                                   levels=21,
                                                   robust=True,
                                                   extend='both')

    # Save/update the new colorfile
    print("Saving colormap data")
    fn_basename, _ = os.path.splitext(args.nc_file)
    with open(fn_basename+".cf", 'wb') as f:
        pickle.dump(color_data, f)

    #######################################################

    print(dataset)

    for v in dataset.variables:
        if (v in dataset.dims) or (v in dataset.coords): continue

        print("\nPlotting data for variable '%s'..." % v)
        # print("Loading....", flush=True)
        var_data = dataset[v]

        print("   Variable details:")
        for attr, val in var_data.attrs.items():
            print("      " + "%s: %s" % (attr, val))
        print("   Colormap settings:")
        var_cmap_kwargs = color_data[v]
        for key, val in var_cmap_kwargs.items():
            print("      " + "%s: %s" % (key, val))

        # Iterate over time dimension
        for time, plot_data in var_data.groupby('time'):

            ts = pd.to_datetime(str(time), utc=True)
            # detail format - MM-DD-YYYY_hh:mmZ"
            ts_str = ts.strftime('%m-%d-%Y %H:%MZ')
            # filename format - "MMDDYYYY_HHMMZ"
            fn_ts_str = ts.strftime("%m%d%Y_%H%MZ")

            print("   " + ts_str)

            # Check if darray needs a cyclic point added
            if not check_cyclic(plot_data, coord='lon'):
                plot_data = cyclic_dataarray(plot_data, coord='lon')

            # Plot this timeslice
            fig = plt.figure(ts_str)
            ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
            ax, plot = geo_plot(plot_data, ax=ax, **var_cmap_kwargs)

            # Plot aesthetic tweaking
            ax.set_title(ts_str, loc='left')
            cb = add_colorbar(plot, ax=ax, orientation='horizontal',
                              pad=0.1)

            # Label the colorbar with the best info available
            if hasattr(var_data, 'long_name'):
                cb_label = var_data.long_name
            else:
                cb_label = v
            if hasattr(var_data, 'level'):
                cb_label += " (%s)" % var_data.level
            if hasattr(var_data, 'units'):
                cb_label += " [%s]" % var_data.units
            cb.set_label(cb_label)

            plt.draw()

            plot_fmt = 'png'
            out_fn = "%s_%s.%s" % (v, fn_ts_str, plot_fmt)
            plt.savefig(out_fn, dpi=150, bbox_inches='tight')

            plt.close(fig)

            if args.sample:
                break

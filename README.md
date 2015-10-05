`plot-all-in-ncfile.py` example script.

For convenience, a conda environment has been provided with all the packages used to automate this task. The install process is very straightforward (and unnecessary if you already have a scientific Python setup running with the packages [xray][] and [cartopy][]):

```bash
$ cd path/to/plot-all-in-ncfile.py
$ conda env create -f environment.yml
$ source activate plot-all-in-ncfile
```

You may want to install the bleeding-edge release of [xray][],

```bash
$ git install git+https://github.com/xray/xray.git
```

From there, just run the script with the "-h" flag for help/usage. A very simple scheme is used to save color formatting between plots. The script has the to read a "colorfile", which is really just a glorified dictionary of dictionaries which has been saved (pickled) to disk. I patched in to use [xray][]'s tool to automatically infer colormap settings, and if this "colorfile" isn't supplied as an argument, it'll automatically look at all the data for each variable and figure out the best colormap settings and save them in a file with the same basename as the netCDF file being plotted but with the extension `.cf`. Furthermore, if you supply a colorfile but it doesn't contain details for a variable found in the netCDF file, it will automatically infer it and add it to the colorfile.

Since a colorfile is just a dictionary of dicts, you can easily add to it interactively (or maybe with a special function that automates the task). Here's the dictionary contained in the colorfile generated when looking at some TRMM data:

```python
{'rr': {'cmap': <matplotlib.colors.ListedColormap at 0x1169f2390>,
  'cnorm': <matplotlib.colors.BoundaryNorm at 0x116064cc0>,
  'extend': 'max',
  'levels': array([  0. ,   1.5,   3. ,   4.5,   6. ,   7.5,   9. ,  10.5,  12. ,
          13.5,  15. ,  16.5,  18. ,  19.5,  21. ,  22.5,  24. ,  25.5,
          27. ,  28.5,  30. ,  31.5]),
  'vmax': 31.5,
  'vmin': 0.0}}
```

Other options might be to convert these to JSON or YAML and save them on disk in a way that they can be edited by hand; happy to implement that as an example if interested.

## Sample Usage

```bash
$ ./plot-all-in-ncfile.py TRMM_3B42.1998-2013.daily.1deg.V7.nc -c TRMM_3B42.1998-2013.daily.1deg.V7.cf --sample
```

[cartopy]: http://scitools.org.uk/cartopy/
[xray]: http://xray.readthedocs.org
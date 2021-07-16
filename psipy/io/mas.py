"""
Tools for reading MAS (Magnetohydrodynamics on a sphere) model outputs.

Files come in two types, .hdf or .h5. In both cases filenames always have the
structure '{var}{timestep}.{extension}', where:

- 'var' is the variable name
- 'timestep' is the three digit (zero padded) timestep
- 'extension' is '.hdf' or '.h5'
"""
import glob
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from .util import read_hdf4, read_hdf5


__all__ = ['read_mas_file', 'get_mas_variables']


def get_mas_filenames(directory, var):
    directory = Path(directory)
    return sorted(glob.glob(str(directory / f'{var}[0-9][0-9][0-9].h*')))


def read_mas_file(directory, var):
    """
    Read in a single MAS output file.

    Parameters
    ----------
    directory :
        Directory to look in.
    var : str
        Variable name.

    Returns
    -------
    data : xarray.DataArray
        Loaded data.
    """
    files = get_mas_filenames(directory, var)
    if not len(files):
        raise FileNotFoundError(f'Could not find file for variable "{var}" in '
                                f'directory {directory}')

    data = {get_timestep(f): _read_mas(f) for f in files}
    return xr.concat(data.values(),
                     dim=pd.Index(data.keys(), name='time'),
                     compat='identical')


def _read_mas(path):
    """
    Read a single MAS file.
    """
    f = Path(path)
    if f.suffix == '.hdf':
        data, coords = read_hdf4(f)
    elif f.suffix == '.h5':
        data, coords = read_hdf5(f)

    dims = ['phi', 'theta', 'r']
    # Convert from co-latitude to latitude
    coords[1] = np.pi / 2 - np.array(coords[1])
    data = xr.DataArray(data=data, coords=coords, dims=dims)
    return data


def convert_hdf_to_netcdf(directory, var):
    """
    Read in a set of HDF files, and save them out to NetCDF files.

    This is helpful to convert files for loading lazily using dask.

    Warnings
    --------
    This will create a new set of files that same size as *all* the files
    read in. Make sure you have enough disk space before using this function!
    """
    files = get_mas_filenames(directory)

    for f in files:
        print(f'Processing {f}...')
        f = Path(f)
        data = _read_mas(f)
        new_dir = (f.parent / '..' / 'netcdf').resolve()
        new_dir.mkdir(exist_ok=True)
        new_path = (new_dir / f.name).with_suffix('.nc')
        data.to_netcdf(new_path)
        del data


def get_mas_variables(path):
    """
    Return a list of variables present in a given directory.

    Parameters
    ----------
    path :
        Path to the folder containing the MAS data files.

    Returns
    -------
    var_names : list
        List of variable names present in the given directory.
    """
    files = glob.glob(str(path / '*[0-9][0-9][0-9].h*'))
    # Get the variable name from the filename
    # Here we take the filename before .hdf, and remove the last three
    # characters which give the timestep
    var_names = [Path(f).stem.split('.h')[0][:-3] for f in files]
    if not len(var_names):
        raise FileNotFoundError(f'No variable files found in {path}')
    # Use list(set()) to get unique values
    return list(set(var_names))


def get_timestep(path):
    """
    Extract the timestep from a given MAS output filename.
    """
    return int(Path(path).stem[-3:])

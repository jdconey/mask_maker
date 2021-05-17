# mask_maker
Binary mask drawing tool for Met Office UKV netCDF model output

Does what it says on the tin. Rough around the edges. A helper tool to create binary masks for segmentation tasks using Met Office UKV data (I used vertical velocity data, for example).

Requires interactive matplotlib to work properly, hence the jupyter notebook.
All the important functions are in the `mask_maker.py` script which are imported into the notebook to save mess. 
Requires `xarray`, `iris`, `matplotlib` and `numpy`. `cartopy` might be handy, I guess.

YMMV

Let me know if things don't work etc
mm16jdc at leeds dot ac dot uk

If you're interested in seeing the end result of my segmentation model, you can view some results on my [university webpage](https://homepages.see.leeds.ac.uk/~mm16jdc/phd/lee_waves/).

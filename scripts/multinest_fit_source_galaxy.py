import sys

import src.config.config

sys.path.append("../")
import os

from src.imaging import scaled_array
from src.imaging import image
from src.imaging import mask
from src.imaging import grids
from src.profiles import light_profiles as lp
from src.profiles import mass_profiles as mp
from src.pixelization import frame_convolution
from src.autopipe import model_mapper
from src.autopipe import non_linear
from src.analysis import ray_tracing
from src.analysis import galaxy
from src.analysis import fitting

from functools import partial
import pymultinest

lens_name = 'source_sersic'
data_dir = "../weighted_data/"+lens_name.format(os.path.dirname(os.path.realpath(__file__)))

print(data_dir)

im = scaled_array.ScaledArray.from_fits(file_path=data_dir+'/image_coords', hdu=0, pixel_scale=0.1)
noise = scaled_array.ScaledArray.from_fits(file_path=data_dir+'/noise', hdu=0, pixel_scale=0.1)
exposure_time = scaled_array.ScaledArray.from_fits(file_path=data_dir+'/exposure_time', hdu=0,
                                                   pixel_scale=0.1)
psf = image.PSF.from_fits(file_path=data_dir+'/psf', hdu=0, pixel_scale=0.1)

data = image.Image(array=im, effective_exposure_time=exposure_time, pixel_scale=0.1, psf=psf,
                   background_noise=noise, poisson_noise=noise)

msk = mask.Mask.circular(shape_arc_seconds=data.shape_arc_seconds, pixel_scale=data.pixel_scale, radius_mask=2.0)

grid_coords = grids.CoordsCollection.from_mask(mask=msk, sub_grid_size=1, blurring_shape=psf.shape)
grid_data = grids.DataCollection.from_mask(mask=msk, image=data, noise=data.background_noise,
                                           exposure_time=data.effective_exposure_time)
mappers = grids.MapperCollection.from_mask(mask=msk)

frame = frame_convolution.FrameMaker(mask=msk)
convolver = frame.convolver_for_kernel_shape(kernel_shape=data.psf.shape,
                                             blurring_region_mask=msk.blurring_mask_for_kernel_shape(
                                                 kernel_shape=data.psf.shape))
kernel_convolver = convolver.convolver_for_kernel(kernel=data.psf)

# NON LINEAR ANALYSIS #

config = src.config.config.DefaultPriorConfig(config_folder_path='../src/config')
model_map = model_mapper.ModelMapper(config=config, mass_profile=mp.EllipticalIsothermal,
                                     light_profile=lp.EllipticalSersic)
multinest = non_linear.MultiNest(path='../results/', obj_name='test_fit', model_mapper=model_map)

def prior(cube, ndim, n_params, model_mapper):

    phys_cube = model_mapper.physical_vector_from_hypercube_vector(hypercube_vector=cube)

    for i in range(n_params):
        cube[i] = phys_cube[i]

    return cube

def likelihood(physical_cube, ndim, n_params, model_mapper, grid_coords, grid_data, grid_mappers, kernel_convolver):

    physical_model = model_mapper.from_physical_vector(physical_cube)

    lens_galaxy = galaxy.Galaxy(mass_profiles=[physical_model.mass_profile])
    source_galaxy = galaxy.Galaxy(light_profiles=[physical_model.light_profile])
    ray_trace = ray_tracing.Tracer(lens_galaxies=[lens_galaxy], source_galaxies=[source_galaxy],
                                   image_plane_grids=grid_coords)

    return fitting.fit_data_with_profiles(grid_data=grid_data, kernel_convolver=kernel_convolver, tracer=ray_trace)

prior_pass = partial(prior, model_mapper=model_map)
likelihood_pass = partial(likelihood, model_mapper=model_map, grid_coords=grid_coords, grid_data=grid_data,
                          grid_mappers=mappers, kernel_convolver=kernel_convolver)

pymultinest.run(likelihood_pass, prior_pass, n_dims=multinest.total_parameters, n_params=multinest.total_parameters,
                n_clustering_params=None, wrapped_params=None, importance_nested_sampling=True, multimodal=True,
                const_efficiency_mode=False, n_live_points=50, evidence_tolerance=0.5, sampling_efficiency=0.2,
                n_iter_before_update=100, null_log_evidence=-1e+90, max_modes=100, mode_tolerance=-1e+90,
                outputfiles_basename=multinest.results_path + multinest.obj_name + '_', seed=-1, verbose=False,
                resume=True, context=0, write_output=True, log_zero=-1e+100, max_iter=0, init_MPI=True)
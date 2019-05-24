import pytest
from astropy import cosmology as cosmo

from autofit.mapper import model
from autofit.mapper import model_mapper as mm
from autolens.model import galaxy as g
from autolens.model.profiles import light_profiles as lp
from autolens.model.profiles import mass_profiles as mp
from autolens.pipeline import phase as ph


@pytest.fixture(name="lens_galaxy")
def make_lens_galaxy():
    return g.Galaxy(mass=mp.EllipticalMassProfile(), redshift=1.0)


@pytest.fixture(name="source_galaxy")
def make_source_galaxy():
    return g.Galaxy(light=lp.EllipticalLightProfile(), redshift=2.0)


@pytest.fixture(name="lens_galaxies")
def make_lens_galaxies(lens_galaxy):
    lens_galaxies = model.ModelInstance()
    lens_galaxies.lens = lens_galaxy
    return lens_galaxies


@pytest.fixture(name="lens_result")
def make_lens_result(lens_galaxies):
    instance = model.ModelInstance()
    instance.lens_galaxies = lens_galaxies

    return ph.LensPlanePhase.Result(instance, 1.0, mm.ModelMapper(), None,
                                    ph.LensPlanePhase.Analysis(lens_data=None, cosmology=cosmo.Planck15,
                                                               positions_threshold=1.0), None)


@pytest.fixture(name="lens_source_result")
def make_lens_source_result(source_galaxy, lens_galaxy):
    source_galaxies = model.ModelInstance()
    lens_galaxies = model.ModelInstance()
    source_galaxies.source = source_galaxy
    lens_galaxies.lens = lens_galaxy

    instance = model.ModelInstance()
    instance.source_galaxies = source_galaxies
    instance.lens_galaxies = lens_galaxies

    return ph.LensSourcePlanePhase.Result(instance, 1.0, mm.ModelMapper(), None,
                                          ph.LensSourcePlanePhase.Analysis(lens_data=None,
                                                                           cosmology=cosmo.Planck15,
                                                                           positions_threshold=1.0), None)


@pytest.fixture(name="multi_plane_result")
def make_multi_plane_result(lens_galaxy, source_galaxy):
    instance = model.ModelInstance()
    galaxies = model.ModelInstance()
    galaxies.lens = lens_galaxy
    galaxies.source = source_galaxy
    instance.galaxies = galaxies

    return ph.MultiPlanePhase.Result(instance, 1.0, mm.ModelMapper(), None,
                                     ph.MultiPlanePhase.Analysis(lens_data=None,
                                                                 cosmology=cosmo.Planck15,
                                                                 positions_threshold=1.0), None)


class TestImagePassing(object):
    def test_lens_galaxy_dict(self, lens_result, lens_galaxy):
        assert lens_result.name_galaxy_tuples == [("lens", lens_galaxy)]

    def test_lens_source_galaxy_dict(self, lens_source_result, lens_galaxy, source_galaxy):
        assert lens_source_result.name_galaxy_tuples == [("lens", lens_galaxy), ("source", source_galaxy)]

    def test_multi_plane_galaxy_dict(self, multi_plane_result, lens_galaxy, source_galaxy):
        assert multi_plane_result.name_galaxy_tuples == [("lens", lens_galaxy), ("source", source_galaxy)]

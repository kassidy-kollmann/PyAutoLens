import autofit as af
import autolens as al
from test import runner

test_type = "model_mapper"
test_name = "use_constant_as_mean_of_gaussian_prior"
data_type = "lens_light_dev_vaucouleurs"
data_resolution = "LSST"


def make_pipeline(name, phase_folders, optimizer_class=af.MultiNest):
    class MMPhase(al.PhaseImaging):

        pass

    phase1 = MMPhase(
        phase_name="phase_1",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(redshift=0.5, light=al.light_profiles.EllipticalSersic)
        ),
        optimizer_class=optimizer_class,
    )

    phase1.optimizer.const_efficiency_mode = True
    phase1.optimizer.n_live_points = 20
    phase1.optimizer.sampling_efficiency = 0.8

    class MMPhase2(al.PhaseImaging):
        def customize_priors(self, results):

            centre_value = results.from_phase(
                "phase_1"
            ).constant.galaxies.lens.light.mask_centre
            self.galaxies.lens.light.mask_centre.centre_0 = af.GaussianPrior(
                mean=centre_value[0], sigma=0.5
            )
            self.galaxies.lens.light.mask_centre.centre_1 = af.GaussianPrior(
                mean=centre_value[1], sigma=0.5
            )

            intensity_value = results.from_phase(
                "phase_1"
            ).constant.galaxies.lens.light.intensity
            self.galaxies.lens.light.intensity = af.GaussianPrior(
                mean=intensity_value, sigma=1.0
            )

            effective_radius_value = results.from_phase(
                "phase_1"
            ).constant.galaxies.lens.light.effective_radius
            self.galaxies.lens.light.effective_radius = af.GaussianPrior(
                mean=effective_radius_value, sigma=2.0
            )

            sersic_index_value = results.from_phase(
                "phase_1"
            ).constant.galaxies.lens.light.sersic_index
            self.galaxies.lens.light.sersic_index = af.GaussianPrior(
                mean=sersic_index_value, sigma=2.0
            )

            axis_ratio_value = results.from_phase(
                "phase_1"
            ).constant.galaxies.lens.light.axis_ratio
            self.galaxies.lens.light.axis_ratio = af.GaussianPrior(
                mean=axis_ratio_value, sigma=0.3
            )

            phi_value = results.from_phase("phase_1").constant.galaxies.lens.light.phi
            self.galaxies.lens.light.phi = af.GaussianPrior(mean=phi_value, sigma=30.0)

    phase2 = MMPhase2(
        phase_name="phase_2",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(redshift=0.5, light=al.light_profiles.EllipticalSersic)
        ),
        optimizer_class=optimizer_class,
    )

    phase2.optimizer.const_efficiency_mode = True
    phase2.optimizer.n_live_points = 20
    phase2.optimizer.sampling_efficiency = 0.8

    return al.PipelineImaging(name, phase1, phase2)


if __name__ == "__main__":
    import sys

    runner.run(sys.modules[__name__])
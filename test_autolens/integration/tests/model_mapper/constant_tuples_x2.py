import autofit as af
import autolens as al
from test import runner

test_type = "model_mapper"
test_name = "constant_tuples_x2"
data_type = "lens_light_dev_vaucouleurs"
data_resolution = "LSST"


def make_pipeline(name, phase_folders, optimizer_class=af.MultiNest):
    class MMPhase(al.PhaseImaging):
        def customize_priors(self, results):

            self.galaxies.lens.light.centre_0 = 1.0
            self.galaxies.lens.light.centre_1 = 2.0

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

    return al.PipelineImaging(name, phase1)


if __name__ == "__main__":
    import sys

    runner.run(sys.modules[__name__])
from autolens.commands.base import Base, current_directory
from autolens.exc import CLIException


class Pipeline(Base):

    def run(self):
        from autolens import pipeline
        name = self.options['<name>']
        if name is not None:
            try:
                self.run_pipeline(pipeline.pipeline_dict[name])
            except KeyError:
                raise CLIException("No pipeline called '{}' found".format(name))

        print("Available Pipelines:")
        print("\n".join(list(pipeline.pipeline_dict.keys())))

    def run_pipeline(self, pipeline):
        pass

    @property
    def image_path(self):
        image_path = self.options['<image_path>']
        if image_path is None:
            raise CLIException("Please specify the path to the image folder")
        if not image_path.startswith("/"):
            image_path = "{}/{}".format(current_directory, image_path)
        return image_path

    @property
    def pixel_scale(self):
        return self.options['<pixel-scale>']

    def load_image(self):
        from autolens.imaging import scaled_array
        from autolens.imaging import image as im

        data = scaled_array.ScaledArray.from_fits(file_path='{}/image'.format(self.image_path), hdu=0,
                                                  pixel_scale=self.pixel_scale)
        noise = scaled_array.ScaledArray.from_fits(file_path='{}/noise'.format(self.image_path), hdu=0,
                                                   pixel_scale=self.pixel_scale)
        psf = im.PSF.from_fits(file_path='{}/psf'.format(self.image_path), hdu=0, pixel_scale=0.1)

        return im.Image(array=data, pixel_scale=0.05, psf=psf, noise=noise)

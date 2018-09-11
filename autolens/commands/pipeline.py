from autolens.commands.base import Base, prepend_working_directory
from autolens import conf
from autolens import pipeline
import colorama


def color(text, fore):
    """
    Apply a color to some text.

    Parameters
    ----------
    text: str
        The original text
    fore: colorama.ansi.AnsiFore
        The color to be applied to the text

    Returns
    -------
    text: str
        Colored text
    """
    return "{}{}{}".format(fore, text, colorama.Fore.RESET)


def blue(text):
    """
    Make text blue
    """
    return color(text, colorama.Fore.BLUE)


def red(text):
    """
    Make text red
    """
    return color(text, colorama.Fore.RED)


class Pipeline(Base):

    def run(self):
        name = self.options['<name>']
        conf.instance = conf.Config(self.config_path, self.output_path)
        if self.options['--info']:
            tup = pipeline.pipeline_dict[name]
            print()
            pl = tup.make()
            print(red(name))
            print(tup.doc)
            print()
            print(red("Phases"))
            print("\n".join(["{}\n   {}".format(phase.__class__.__name__, blue(phase.doc)) for phase in pl.phases]))
            return
        if name is not None:
            if name not in pipeline.pipeline_dict:
                if name == "test":
                    self.run_pipeline(pipeline.TestPipeline())
                    return
                print("No pipeline called '{}' found".format(name))
                return
            self.run_pipeline(pipeline.pipeline_dict[name].make())

        print_pipelines()

    def run_pipeline(self, pl):
        from autolens.imaging import image as im
        if self.is_using_hdu:
            image = im.load_from_file(self.data_path, self.image_hdu, self.noise_hdu, self.psf_hdu, self.pixel_scale)
        else:
            image = im.load_from_path(self.image_path, self.noise_path, self.psf_path, pixel_scale=self.pixel_scale)
        pl.run(image)

    @property
    def is_using_hdu(self):
        """
        Returns
        -------
        is_using_hdu: bool
            True iff --data option is set. --data is the path to a file with multiple data layers accessible by setting
            hdus.
        """
        return self.options["--data"] is not None

    @property
    def image_hdu(self):
        """
        Returns
        -------
        str: image_hdu
            The hdu of the image data in the data file
        """
        return int(self.options["--image-hdu"])

    @property
    def noise_hdu(self):
        """
        Returns
        -------
        str: noise_hdu
            The hdu of the noise data in the data file
        """
        return int(self.options["--noise-hdu"])

    @property
    def psf_hdu(self):
        """
        Returns
        -------
        str: psf_hdu
            The hdu of the psf data in the data file
        """
        return int(self.options["--psf-hdu"])

    @property
    @prepend_working_directory
    def image_path(self):
        """
        Get the relative or absolute path to the input image. If the path does not begin with '/' then the current
        working directory will be prepended.

        Returns
        -------
        str: path
            The path to the image
        """
        return self.options['--image']

    @property
    @prepend_working_directory
    def data_path(self):
        """
        Get the relative or absolute path to the input data. Input data includes image, noise and psf with different
        hdu values input by the user. If the path does not begin with '/' then the current working directory will be
        prepended.

        Returns
        -------
        str: path
            The path to the data
        """
        return self.options['--data']

    @property
    @prepend_working_directory
    def noise_path(self):
        """
        Get the relative or absolute path to the input noise. If the path does not begin with '/' then the current
        working directory will be prepended.

        Returns
        -------
        str: path
            The path to the noise
        """
        return self.options['--noise']

    @property
    @prepend_working_directory
    def psf_path(self):
        """
        Get the relative or absolute path to the input psf. If the path does not begin with '/' then the current
        working directory will be prepended.

        Returns
        -------
        str: path
            The path to the psf folder or psf.
        """
        return self.options['--psf']

    @property
    def pixel_scale(self):
        """
        Returns
        -------
        pixel_scale: float
            The size of a single pixel, in arc seconds, as input by the user
        """
        return float(self.options['--pixel-scale'])

    @property
    def config_path(self):
        """
        Returns
        -------
        config_path: str
            The path to the configuration folder. Defaults to 'config' in the current working directory.
        """
        if '--config' in self.options:
            config_path = self.options['--config']
        else:
            config_path = 'config'
        return config_path

    @property
    @prepend_working_directory
    def output_path(self):
        """
        Returns
        -------
        output_path: str
            The path to the configuration folder. Defaults to 'output' in the current working directory.
        """
        return self.options['--output']


def print_pipelines():
    """
    Prints a list of available pipelines taken from the pipeline dictionary.
    """
    print("Available Pipelines:\n")
    print(
        "\n".join(
            ["{}\n  {}".format(key, blue(value.short_doc)) for
             key, value
             in
             pipeline.pipeline_dict.items()]))

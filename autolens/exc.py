class ImagingException(Exception):
    pass


class KernelException(Exception):
    pass


class PriorException(Exception):
    pass


class MultiNestException(Exception):
    pass


class MaskException(Exception):
    pass


class GalaxyException(Exception):
    pass


class RayTracingException(Exception):
    pass


class PixelizationException(Exception):
    pass


class InversionException(Exception):
    pass


class FittingException(Exception):
    pass


class PlottingException(Exception):
    pass


class PriorLimitException(PriorException):
    pass

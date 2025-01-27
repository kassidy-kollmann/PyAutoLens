import logging
import math
from dataclasses import dataclass
from typing import Tuple, List, Iterator, Type, Optional

import autoarray as aa

from autoarray.structures.triangles import array

from autolens.lens.tracer import Tracer

logger = logging.getLogger(__name__)


@dataclass
class Step:
    """
    A step in the triangle solver algorithm.

    Attributes
    ----------
    number
        The number of the step.
    initial_triangles
        The triangles at the start of the step.
    filtered_triangles
        The triangles trace to triangles that contain the source plane coordinate.
    neighbourhood
        The neighbourhood of the filtered triangles.
    up_sampled
        The neighbourhood up-sampled to increase the resolution.
    """

    number: int
    initial_triangles: aa.AbstractTriangles
    filtered_triangles: aa.AbstractTriangles
    neighbourhood: aa.AbstractTriangles
    up_sampled: aa.AbstractTriangles


class PointSolver:
    # noinspection PyPep8Naming
    def __init__(
        self,
        scale: float,
        y_min: float,
        y_max: float,
        x_min: float,
        x_max: float,
        pixel_scale_precision: float,
        magnification_threshold=0.1,
        ArrayTriangles: Type[aa.AbstractTriangles] = array.ArrayTriangles,
    ):
        """
        Determine the image plane coordinates that are traced to be a source plane coordinate.

        This is performed efficiently by iteratively subdividing the image plane into triangles and checking if the
        source plane coordinate is contained within the triangle. The triangles are subsampled to increase the
        resolution

        Parameters
        ----------
        pixel_scale_precision
            The target pixel scale of the image grid.
        ArrayTriangles
            The class to use for the triangles.
        """
        self.scale = scale
        self.y_min = y_min
        self.y_max = y_max
        self.x_min = x_min
        self.x_max = x_max
        self.pixel_scale_precision = pixel_scale_precision
        self.magnification_threshold = magnification_threshold
        self.ArrayTriangles = ArrayTriangles

    # noinspection PyPep8Naming
    @classmethod
    def for_grid(
        cls,
        grid: aa.Grid2D,
        pixel_scale_precision: float,
        magnification_threshold=0.1,
        ArrayTriangles: Type[aa.AbstractTriangles] = array.ArrayTriangles,
    ):
        scale = grid.pixel_scale

        y = grid[:, 0]
        x = grid[:, 1]

        y_min = y.min()
        y_max = y.max()
        x_min = x.min()
        x_max = x.max()

        return cls(
            scale=scale,
            y_min=y_min,
            y_max=y_max,
            x_min=x_min,
            x_max=x_max,
            pixel_scale_precision=pixel_scale_precision,
            magnification_threshold=magnification_threshold,
            ArrayTriangles=ArrayTriangles,
        )

    @property
    def n_steps(self) -> int:
        """
        How many times should triangles be subdivided?
        """
        return math.ceil(math.log2(self.scale / self.pixel_scale_precision))

    def _source_plane_grid(
        self,
        tracer: Tracer,
        grid: aa.type.Grid2DLike,
        source_plane_redshift: Optional[float] = None,
    ) -> aa.type.Grid2DLike:
        """
        Calculate the source plane grid from the image plane grid.

        Parameters
        ----------
        grid
            The image plane grid.

        Returns
        -------
        The source plane grid computed by applying the deflections to the image plane grid.
        """

        source_plane_index = -1

        if source_plane_redshift is not None:
            for redshift in tracer.plane_redshifts:
                source_plane_index += 1
                if redshift == source_plane_redshift:
                    break

        deflections = tracer.deflections_between_planes_from(
            grid=grid, plane_i=0, plane_j=source_plane_index
        )
        # noinspection PyTypeChecker
        return grid.grid_2d_via_deflection_grid_from(deflection_grid=deflections)

    def solve(
        self,
        tracer: Tracer,
        source_plane_coordinate: Tuple[float, float],
        source_plane_redshift: Optional[float] = None,
    ) -> aa.Grid2DIrregular:
        """
        Solve for the image plane coordinates that are traced to the source plane coordinate.

        This is done by tiling the image plane with triangles and checking if the source plane coordinate is contained
        within the triangle. The triangles are subsampled to increase the resolution with only the triangles that
        contain the source plane coordinate and their neighbours being kept.

        The means of the triangles  are then filtered to keep only those with an absolute magnification above the
        threshold.

        Parameters
        ----------
        source_plane_coordinate
            The source plane coordinate to trace to the image plane.

        Returns
        -------
        A list of image plane coordinates that are traced to the source plane coordinate.
        """
        if self.n_steps == 0:
            raise ValueError(
                "The target pixel scale is too large to subdivide the triangles."
            )

        steps = list(
            self.steps(
                tracer=tracer,
                source_plane_coordinate=source_plane_coordinate,
                source_plane_redshift=source_plane_redshift,
            )
        )
        final_step = steps[-1]
        kept_triangles = final_step.filtered_triangles

        filtered_means = self._filter_low_magnification(
            tracer=tracer, points=kept_triangles.means
        )

        difference = len(kept_triangles.means) - len(filtered_means)
        if difference > 0:
            logger.debug(
                f"Filtered one multiple-image with magnification below threshold."
            )
        elif difference > 1:
            logger.warning(
                f"Filtered {difference} multiple-images with magnification below threshold."
            )

        return aa.Grid2DIrregular(values=filtered_means)

    def _filter_low_magnification(
        self, tracer: Tracer, points: List[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        """
        Filter the points to keep only those with an absolute magnification above the threshold.

        Parameters
        ----------
        points
            The points to filter.

        Returns
        -------
        The points with an absolute magnification above the threshold.
        """
        return [
            point
            for point, magnification in zip(
                points,
                tracer.magnification_2d_via_hessian_from(
                    grid=aa.Grid2DIrregular(points),
                    buffer=self.scale,
                ),
            )
            if abs(magnification) > self.magnification_threshold
        ]

    def _filter_triangles(
        self,
        tracer: Tracer,
        source_plane_coordinate: Tuple[float, float],
        triangles: aa.AbstractTriangles,
        source_plane_redshift: Optional[float] = None,
    ):
        """
        Filter the triangles to keep only those that contain the source plane coordinate.

        Parameters
        ----------
        triangles
            A set of triangles that may contain the source plane coordinate.
        source_plane_coordinate
            The source plane coordinate to check if it is contained within the triangles.

        Returns
        -------
        The triangles that contain the source plane coordinate.
        """
        source_plane_grid = self._source_plane_grid(
            tracer=tracer,
            grid=aa.Grid2DIrregular(triangles.vertices),
            source_plane_redshift=source_plane_redshift,
        )
        source_triangles = triangles.with_vertices(source_plane_grid.array)
        indexes = source_triangles.containing_indices(point=source_plane_coordinate)
        return triangles.for_indexes(indexes=indexes)

    def steps(
        self,
        tracer: Tracer,
        source_plane_coordinate: Tuple[float, float],
        source_plane_redshift: Optional[float] = None,
    ) -> Iterator[Step]:
        """
        Iterate over the steps of the triangle solver algorithm.

        Parameters
        ----------
        source_plane_coordinate
            The source plane coordinate to trace to the image plane.

        Returns
        -------
        An iterator over the steps of the triangle solver algorithm.
        """
        initial_triangles = self.ArrayTriangles.for_limits_and_scale(
            y_min=self.y_min,
            y_max=self.y_max,
            x_min=self.x_min,
            x_max=self.x_max,
            scale=self.scale,
        )

        for number in range(self.n_steps):
            kept_triangles = self._filter_triangles(
                tracer=tracer,
                source_plane_coordinate=source_plane_coordinate,
                triangles=initial_triangles,
                source_plane_redshift=source_plane_redshift,
            )
            neighbourhood = kept_triangles.neighborhood()
            up_sampled = neighbourhood.up_sample()

            yield Step(
                number=number,
                initial_triangles=initial_triangles,
                filtered_triangles=kept_triangles,
                neighbourhood=neighbourhood,
                up_sampled=up_sampled,
            )

            initial_triangles = up_sampled

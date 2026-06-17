from across.sdk.v1 import (
    ObservationFootprintCreate,
    Point,
)
from across.tools import Coordinate, Polygon
from across.tools.footprint import Footprint


def _convert(footprint_points: list[list[Point]]) -> Footprint:
    """Convert SDK detector points into an ACROSS tools footprint model.

    Args:
        footprint_points: Detector polygons represented as SDK points, where
            each point stores sky offsets in RA and Dec coordinates.

    Returns:
        A `Footprint` object containing polygon detectors in tools format.
    """
    detectors = []
    for detector in footprint_points:
        detectors.append(
            Polygon(
                coordinates=[Coordinate(ra=point.x, dec=point.y) for point in detector]
            )
        )

    return Footprint(detectors=detectors)


def project_footprint(
    footprint_points: list[list[Point]], ra: float, dec: float, roll_angle: float
) -> list[ObservationFootprintCreate]:
    """Project detector footprints to a sky position and roll angle.

    Args:
        footprint_points: Detector polygons in instrument-relative coordinates.
        ra: Right ascension of the pointing center, in degrees.
        dec: Declination of the pointing center, in degrees.
        roll_angle: Field rotation angle applied during projection, in degrees.

    Returns:
        A list of `ObservationFootprintCreate` objects in SDK-ready format.
    """
    tools_footprint = _convert(footprint_points)

    projected_footprint = tools_footprint.project(
        coordinate=Coordinate(ra=ra, dec=dec), roll_angle=roll_angle
    )

    footprint_creates = []

    for projected_detector in projected_footprint.detectors:
        footprint_creates.append(
            ObservationFootprintCreate(
                polygon=[
                    Point(x=coord.ra, y=coord.dec)
                    for coord in projected_detector.coordinates
                ]
            )
        )

    return footprint_creates

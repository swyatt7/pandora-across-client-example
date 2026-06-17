from __future__ import annotations

try:
    from .schedule_handler import PandoraACROSSScheduleHandler
except ImportError:
    from schedule_handler import PandoraACROSSScheduleHandler  # type: ignore

from datetime import datetime
from xml.etree import ElementTree as ET

from across.client import Client
import across.sdk.v1 as sdk


def extract_observations(xml_file_data) -> list[dict]:
    """Extract observation records from a Pandora ScienceCalendar XML file.

    The parser reads visit and sequence blocks, then converts spacecraft
    pointing and timing values into dictionary types for ACROSS ingestion.

    Args:
        xml_file_data: XML source passed through to the parser. This can be a
            path-like value or an open file object accepted by
            ``xml.etree.ElementTree.parse``.

    Returns:
        A list of dictionaries. Each dictionary contains visit and sequence
        identifiers, sky coordinates, roll angle, start and end datetimes,
        and exposure duration in seconds.
    """
    tree = ET.parse(xml_file_data)
    root = tree.getroot()

    # Default namespace from the XML
    ns = {"p": "/pandora/calendar/"}

    observations = []

    for visit in root.findall("p:Visit", ns):
        visit_id = visit.findtext("p:ID", namespaces=ns)

        for seq in visit.findall("p:Observation_Sequence", ns):
            seq_id = seq.findtext("p:ID", namespaces=ns)

            obs_params = seq.find("p:Observational_Parameters", ns)
            if obs_params is None:
                continue

            target = obs_params.findtext("p:Target", namespaces=ns)

            boresight = obs_params.find("p:Boresight", namespaces=ns)
            ra = float(boresight.findtext("p:RA", namespaces=ns)) # type: ignore
            dec = float(boresight.findtext("p:DEC", namespaces=ns)) # type: ignore
            roll = float(boresight.findtext("p:Roll", namespaces=ns)) # type: ignore

            timing = obs_params.find("p:Timing", ns)
            start_str = timing.findtext("p:Start", namespaces=ns) # type: ignore
            end_str = timing.findtext("p:Stop", namespaces=ns) # type: ignore

            start = datetime.fromisoformat(start_str) # type: ignore
            end = datetime.fromisoformat(end_str) # type: ignore

            observations.append(
                {
                    "visit_id": visit_id,
                    "sequence_id": seq_id,
                    "target": target,
                    "ra": ra,
                    "dec": dec,
                    "roll": roll,
                    "start": start,
                    "end": end,
                    "duration_seconds": (end - start).total_seconds(),
                }
            )

    return observations


def ingest(xml_file_data, client: Client | None = None) -> None:
    """Parse a Pandora XML schedule and submit it through the handler.

    Args:
        xml_file_data: XML source passed through to the parser. This can be a
            path-like value or an open file object accepted by
            ``xml.etree.ElementTree.parse``.
        client: Optional ACROSS client instance. If not provided, a new client
            will be created with default configuration.

    Returns:
        None
    """

    if client is None:
        client = Client()

    observations = extract_observations(xml_file_data)

    handler = PandoraACROSSScheduleHandler(
        client=client,
        observation_status=sdk.ObservationStatus.PLANNED,
        schedule_status=sdk.ScheduleStatus.PLANNED,
        schedule_fidelity=sdk.ScheduleFidelity.HIGH,
        schedule_name="high_fidelity_planned",
    )
    handler.run(observations)


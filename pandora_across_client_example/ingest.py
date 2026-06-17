from __future__ import annotations

import argparse
from pathlib import Path

from schedule_handler import PandoraACROSSScheduleHandler

from datetime import datetime
from xml.etree import ElementTree as ET

from across.client import Client
import across.sdk.v1 as sdk


def extract_observations(xml_file: str) -> list[dict]:
    """
    Extract observation information from a Pandora ScienceCalendar XML file.

    Parameters
    ----------
    xml_file : str
        Path to the XML file.

    Returns
    -------
    list[dict]
        List of observation dictionaries containing:

        - visit_id
        - sequence_id
        - target
        - ra
        - dec
        - roll
        - start
        - end
        - duration_seconds
    """
    tree = ET.parse(xml_file)
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


def load_xml(xml_path: Path) -> str:
	"""Load and return XML file contents."""
	if not xml_path.exists():
		raise FileNotFoundError(f"XML file not found: {xml_path}")

	return xml_path.read_text(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
		description="Read a PAN-SCICAL-COM XML schedule and send it to the ACROSS schedule handler."
	)
    parser.add_argument(
		"xml_path",
		nargs="?",
		default=(
			Path(__file__).resolve().parents[1]
			/ "data"
			/ "PAN-SCICAL-COM-20260527-VF-20260601-EX-20260608-R001_jpredits_cleaned00.xml"
		),
		type=Path,
		help="Path to the PAN-SCICAL-COM XML file.",
	)
    args = parser.parse_args()

    observations = extract_observations(args.xml_path)


	# Placeholder `client`; replace with your real ACROSS client instance when available.
    handler = PandoraACROSSScheduleHandler(
        client=Client(),
        observation_status=sdk.ObservationStatus.PLANNED,
        schedule_status=sdk.ScheduleStatus.PLANNED,
        schedule_fidelity=sdk.ScheduleFidelity.LOW,
        schedule_name="low_fidelity_planned",
    )
    handler.run(observations)


if __name__ == "__main__":
	main()

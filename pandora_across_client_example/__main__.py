import argparse
from pathlib import Path

from across.client import Client
from ingest import ingest  # type: ignore


def main() -> None:
    """Parse CLI arguments and ingest a Pandora XML schedule.

    Example:
        python -m pandora_across_client_example \
            data/PAN-SCICAL-COM-20260527-VF-20260601-EX-20260608-R001_jpredits_cleaned00.xml \
            --client-id your_client_id \
            --client-secret your_client_secret

    Returns:
        None
    """

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
    parser.add_argument(
        "--client-id",
        default=None,
        help="ACROSS OAuth client ID (defaults to None).",
    )
    parser.add_argument(
        "--client-secret",
        default=None,
        help="ACROSS OAuth client secret (defaults to None).",
    )

    args = parser.parse_args()

    xml_file_data = open(args.xml_path, "r")

    client = None
    if args.client_id is not None or args.client_secret is not None:
        client = Client(client_id=args.client_id, client_secret=args.client_secret)

    ingest(xml_file_data, client=client)


if __name__ == "__main__":
    main()

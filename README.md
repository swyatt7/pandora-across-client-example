# pandora-across-client-example

Example script for the Pandora Small Sat team to upload planned schedules to ACROSS.

## Prerequisites

- Python 3.12
- Access to ACROSS credentials (client ID and client secret) if you want to authenticate explicitly

## Installation

Choose one of the two supported environment setups below.

### Option A: `.venv` (Python 3.12)

```bash
git clone https://github.com/<your-org>/pandora-across-client-example.git
cd pandora-across-client-example

python3.12 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### Option B: Conda (Python 3.12)

```bash
git clone https://github.com/<your-org>/pandora-across-client-example.git
cd pandora-across-client-example

conda create -n across-dev python=3.12 -y
conda activate across-dev

pip install --upgrade pip
pip install -r requirements.txt
```

## Example Usage (main)

Run the package entrypoint with an XML schedule path and optional ACROSS credentials:

```bash
python pandora_across_client_example/__main__.py \
  data/PAN-SCICAL-COM-20260527-VF-20260601-EX-20260608-R001_jpredits_cleaned00.xml \
  --client-id "your_client_id" \
  --client-secret "your_client_secret"
```

If you omit `--client-id` and `--client-secret`, the script uses the ACROSS client default configuration.

## Integrating `ingest(...)` into Your Workflow

You can call `ingest(...)` directly from your own Python pipeline after preparing or selecting an XML file.

```python
from across.client import Client
from pandora_across_client_example.ingest import ingest


def upload_schedule(xml_path: str, client_id: str, client_secret: str) -> None:
	client = Client(client_id=client_id, client_secret=client_secret)
	with open(xml_path, "r", encoding="utf-8") as xml_file:
		ingest(xml_file, client=client)


if __name__ == "__main__":
	upload_schedule(
		xml_path="data/PAN-SCICAL-COM-20260527-VF-20260601-EX-20260608-R001_jpredits_cleaned00.xml",
		client_id="your_client_id",
		client_secret="your_client_secret",
	)
```

This approach is useful when schedule upload is one step inside a larger automation flow (for example: fetch XML, validate, ingest, then notify).

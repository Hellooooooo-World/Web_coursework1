import argparse
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

OPENAQ_API = "https://api.openaq.org/v3/locations/{locations_id}/sensors"


def safe_ascii(value: object) -> str:
    """Avoid Windows console encoding issues (e.g. µ)."""
    if value is None:
        return ""
    return str(value).encode("ascii", errors="replace").decode("ascii")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List OpenAQ sensors for a location ID.")
    parser.add_argument("--locations-id", type=int, required=True)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--parameter",
        type=str,
        default=None,
        help="Optional parameter filter, e.g. pm25",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = os.environ.get("OPENAQ_API_KEY")
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    params = {"limit": args.limit}

    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            OPENAQ_API.format(locations_id=args.locations_id),
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        payload = response.json()

    results = payload.get("results", [])
    if not results:
        print("No sensors returned.")
        return

    wanted = args.parameter.lower() if args.parameter else None

    for sensor in results:
        sensor_id = sensor.get("id")
        parameter = sensor.get("parameter") or {}
        name = (parameter.get("name") or "").lower()
        units = safe_ascii(parameter.get("units"))

        if wanted and wanted not in name:
            continue

        print(f"sensor_id={sensor_id}\tparameter={safe_ascii(name)}\tunits={units}")

    if args.parameter and wanted:
        print("If you see no lines above, try without --parameter or adjust it.")


if __name__ == "__main__":
    main()

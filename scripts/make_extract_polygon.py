import json
import sys
from pathlib import Path


def main() -> None:
    source, destination = (Path(value) for value in sys.argv[1:3])
    collection = json.loads(source.read_text(encoding="utf-8"))
    if collection.get("type") != "FeatureCollection":
        raise ValueError("Service-area source must be a GeoJSON FeatureCollection.")

    polygons: list[list] = []
    for feature in collection.get("features", []):
        geometry = feature.get("geometry") or {}
        if geometry.get("type") == "Polygon":
            polygons.append(geometry["coordinates"])
        elif geometry.get("type") == "MultiPolygon":
            polygons.extend(geometry["coordinates"])
        else:
            raise ValueError("Service-area geometry must be Polygon or MultiPolygon.")

    if len(collection["features"]) != 2 or not polygons:
        raise ValueError("M1 extraction requires the two configured service areas.")

    destination.write_text(
        json.dumps(
            {
                "type": "Feature",
                "properties": {},
                "geometry": {"type": "MultiPolygon", "coordinates": polygons},
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

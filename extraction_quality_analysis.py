from typing import Any


MISSING = object()


def compare_extracted_fields(
    original_values: dict[str, Any],
    corrected_values: dict[str, Any],
) -> dict[str, Any]:
    field_names = sorted(
        set(original_values) | set(corrected_values)
    )

    fields = []
    counts = {
        "total": len(field_names),
        "unchanged": 0,
        "changed": 0,
        "added": 0,
        "removed": 0,
    }

    for field_name in field_names:
        original = original_values.get(field_name, MISSING)
        corrected = corrected_values.get(field_name, MISSING)

        if original is MISSING:
            status = "added"
        elif corrected is MISSING:
            status = "removed"
        elif original == corrected:
            status = "unchanged"
        else:
            status = "changed"

        counts[status] += 1

        fields.append(
            {
                "field_name": field_name,
                "status": status,
                "original_value": (
                    None if original is MISSING else original
                ),
                "corrected_value": (
                    None if corrected is MISSING else corrected
                ),
            }
        )

    changed_total = (
        counts["changed"]
        + counts["added"]
        + counts["removed"]
    )

    return {
        "counts": counts,
        "changed_total": changed_total,
        "correction_rate": (
            changed_total / counts["total"]
            if counts["total"]
            else 0.0
        ),
        "fields": fields,
    }


def aggregate_quality_analysis(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    groups: dict[tuple, dict[str, Any]] = {}

    for record in records:
        comparison = compare_extracted_fields(
            record["original_values"],
            record["corrected_values"],
        )
        key = (
            record["document_type"],
            record.get("profile"),
            record.get("configuration_hash"),
        )

        group = groups.setdefault(
            key,
            {
                "document_type": key[0],
                "profile": key[1],
                "configuration_hash": key[2],
                "corrected_runs": 0,
                "field_counts": {
                    "total": 0,
                    "unchanged": 0,
                    "changed": 0,
                    "added": 0,
                    "removed": 0,
                },
                "field_corrections": {},
            },
        )

        group["corrected_runs"] += 1

        for status, count in comparison["counts"].items():
            group["field_counts"][status] += count

        for field in comparison["fields"]:
            if field["status"] == "unchanged":
                continue

            field_name = field["field_name"]
            group["field_corrections"][field_name] = (
                group["field_corrections"].get(field_name, 0) + 1
            )

    result_groups = []

    for group in groups.values():
        counts = group["field_counts"]
        corrections = (
            counts["changed"]
            + counts["added"]
            + counts["removed"]
        )

        group["corrections"] = corrections
        group["correction_rate"] = (
            corrections / counts["total"]
            if counts["total"]
            else 0.0
        )
        group["field_corrections"] = [
            {
                "field_name": field_name,
                "corrections": correction_count,
            }
            for field_name, correction_count in sorted(
                group["field_corrections"].items(),
                key=lambda item: (-item[1], item[0]),
            )
        ]
        result_groups.append(group)

    result_groups.sort(
        key=lambda group: (
            group["document_type"],
            group["profile"] or "",
            group["configuration_hash"] or "",
        )
    )

    return {
        "corrected_runs": len(records),
        "groups": result_groups,
    }

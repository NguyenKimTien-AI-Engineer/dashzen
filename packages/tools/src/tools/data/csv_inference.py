from __future__ import annotations

import csv
import io


def infer_column_type(value: str) -> str:
    if value == "":
        return "string"
    try:
        int(value)
        return "integer"
    except ValueError:
        pass
    try:
        float(value)
        return "number"
    except ValueError:
        pass
    return "string"


def infer_columns_from_csv(content: str, *, sample_rows: int = 20) -> list[dict[str, str]]:
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return []

    headers = rows[0]
    data_rows = rows[1 : sample_rows + 1]
    columns: list[dict[str, str]] = []
    for i, header in enumerate(headers):
        col_type = "string"
        for row in data_rows:
            if i >= len(row):
                continue
            inferred = infer_column_type(row[i])
            if inferred != "string":
                col_type = inferred
                break
        columns.append({"name": header, "type": col_type})
    return columns


def table_name_from_path(path: str) -> str:
    stem = path.rsplit(".", 1)[0]
    return stem.replace("/", "_").replace("\\", "_")

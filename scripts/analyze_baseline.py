"""Summarize process samples and optionally externally captured frame times."""
import argparse
import csv
import json
import math
from pathlib import Path
import statistics


def numbers(rows, column):
    values = []
    for row in rows:
        raw = row.get(column)
        if raw in (None, ""):
            continue
        value = float(raw)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"Invalid sample in {column}")
        values.append(value)
    return values


def percentile(values, fraction):
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    low, high = math.floor(index), math.ceil(index)
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def summarize(directory, frames=None, column="FrameTimeMs", unit="ms"):
    with (directory / "process-metrics.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("No process samples")
    result = {"processes": {}, "limitations": "Working set/private bytes are distinct metrics; no free-VA or GPU-memory measurement."}
    for role in sorted({r["role"] for r in rows}):
        group = [r for r in rows if r["role"] == role]
        metrics = {"samples":len(group), "exit_observed":any(r["state"] == "exited" for r in group)}
        for key in ("cpu_percent_machine", "working_set_bytes", "private_bytes"):
            values = numbers(group, key)
            metrics[key] = None if not values else {"median":statistics.median(values), "p95":percentile(values,.95), "peak":max(values)}
        result["processes"][role] = metrics
    if frames:
        with frames.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or column not in reader.fieldnames:
                raise ValueError(f"Missing frame-time column: {column}")
            frame_rows = list(reader)
        values = numbers(frame_rows, column)
        if len(values) != len(frame_rows) or not values or min(values) <= 0:
            raise ValueError("Frame times must all be positive, finite and nonempty")
        if unit == "s": values = [v * 1000 for v in values]
        result["frames"] = {"count":len(values), "average_fps":1000/statistics.mean(values),
                            "p99_frame_time_ms":percentile(values,.99),
                            "fps_at_p99_frame_time":1000/percentile(values,.99),
                            "note":"Use a capture filtered to L4D2; excludes loading/warmup. Percentile FPS is not mean FPS of the slowest 1%."}
    return result


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("directory",type=Path)
    parser.add_argument("--frames",type=Path)
    parser.add_argument("--column",default="FrameTimeMs")
    parser.add_argument("--unit",choices=("ms","s"),default="ms")
    args=parser.parse_args()
    output=args.directory/"summary.json"
    if output.exists(): raise FileExistsError("Existing summary is preserved; use a new result directory")
    result=summarize(args.directory,args.frames,args.column,args.unit)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(output)

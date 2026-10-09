"""Summarize process samples and optionally externally captured frame times."""
import argparse
import csv
import json
import math
from pathlib import Path
import statistics


MIN_LOW_TAIL_FRAMES = 10
FRAME_IDENTITY_COLUMNS = (
    "Application", "ProcessName", "process_name", "ProcessID", "ProcessId",
    "process_id", "PID", "pid", "SwapChainAddress", "swap_chain_address", "role",
)


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


def frame_source(rows):
    """Reject mixed streams when the capture retains process/swapchain identity."""
    source = {}
    for column in FRAME_IDENTITY_COLUMNS:
        values = {(row.get(column) or "").strip() for row in rows}
        if values == {""}:
            continue
        if "" in values or len(values) != 1:
            raise ValueError(f"Frame capture must contain one process/swapchain; mixed or missing {column}")
        source[column] = values.pop()
    return source


def frame_statistics(values):
    ordered = sorted(values)
    if not ordered or any(not math.isfinite(value) or value <= 0 for value in ordered):
        raise ValueError("Frame times must all be positive, finite and nonempty")
    if not math.isfinite(1000 / ordered[0]):
        raise ValueError("Frame times are too small to produce finite FPS")
    result = {
        "count": len(ordered),
        "average_fps": 1000 / statistics.mean(ordered),
        "p99_frame_time_ms": percentile(ordered, .99),
        "fps_at_p99_frame_time": 1000 / percentile(ordered, .99),
        "p99_9_frame_time_ms": percentile(ordered, .999),
        "maximum_instantaneous_fps": 1000 / ordered[0],
        "minimum_low_tail_frames": MIN_LOW_TAIL_FRAMES,
    }
    for label, denominator in (("1", 100), ("0_1", 1000)):
        # Integer arithmetic implements ceil(N * p) without rounding near an integer.
        count = (len(ordered) + denominator - 1) // denominator
        prefix = f"low_{label}_percent"
        result[prefix + "_fps"] = 1000 / statistics.mean(ordered[-count:])
        result[prefix + "_tail_frames"] = count
        result[prefix + "_sample_status"] = (
            "insufficient_tail_samples" if count < MIN_LOW_TAIL_FRAMES else "minimum_tail_samples_met"
        )
    result["note"] = (
        "Use one process and one swapchain from a stable capture, excluding loading/warmup. "
        "Bridge actual Present events come from L4D2Bridge64.exe; without Bridge use the game process. "
        "Do not mix game and Host events or equate game-side counters with displayed FPS. "
        "Verify the process/swapchain externally if identity columns are absent. "
        "Low FPS is 1000 / mean milliseconds of the slowest ceil(N*p) frames (p=0.01 or 0.001), "
        "not the reciprocal of a percentile or the mean of per-frame FPS. "
        "Fewer than 10 tail frames is marked insufficient; meeting this minimum does not establish statistical reliability. "
        "p99 and p99.9 use linear interpolation at (N-1)*p; sparse tails also limit percentile estimates. "
        "Maximum instantaneous FPS is 1000 / minimum frame time and is sensitive to isolated samples. "
        "Present intervals measure submission cadence, not necessarily displayed-frame cadence; record the capture column semantics."
    )
    return result


def summarize(directory, frames=None, column="FrameTimeMs", unit="ms"):
    if unit not in ("ms", "s"):
        raise ValueError("Frame-time unit must be ms or s")
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
            if len(set(reader.fieldnames)) != len(reader.fieldnames):
                raise ValueError("Duplicate frame capture columns are ambiguous")
            frame_rows = list(reader)
        if any(None in row for row in frame_rows):
            raise ValueError("Frame capture has rows with more values than columns")
        values = numbers(frame_rows, column)
        if len(values) != len(frame_rows) or not values or min(values) <= 0:
            raise ValueError("Frame times must all be positive, finite and nonempty")
        if unit == "s":
            values = [v * 1000 for v in values]
            if not all(math.isfinite(v) for v in values):
                raise ValueError("Frame times overflow milliseconds")
        source = frame_source(frame_rows)
        result["frames"] = frame_statistics(values)
        result["frames"]["source"] = source
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
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(output)

import csv, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"scripts"))
from analyze_baseline import summarize

class Baseline(unittest.TestCase):
    def summarize_frames(self, values, unit="ms", identities=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "process-metrics.csv").write_text(
                "role,state,cpu_percent_machine,working_set_bytes,private_bytes\n"
                "host,running,10,100,200\n", encoding="utf-8")
            frames = root / "frames.csv"
            with frames.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["FrameTimeMs", *(identities or {})])
                writer.writeheader()
                for index, value in enumerate(values):
                    writer.writerow({"FrameTimeMs": value, **{
                        column: entries[index] for column, entries in (identities or {}).items()
                    }})
            return summarize(root, frames, unit=unit)["frames"]

    def test_units_metrics_and_invalid_frames(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/"process-metrics.csv").write_text("role,state,cpu_percent_machine,working_set_bytes,private_bytes\nhost,running,,100,200\nhost,running,10,120,220\ngame,running,50,900,1000\n",encoding="utf-8")
            frames=root/"frames.csv"; frames.write_text("dt\n0.01\n0.02\n",encoding="utf-8")
            result=summarize(root,frames,"dt","s")
            self.assertAlmostEqual(result["frames"]["average_fps"],1000/15)
            self.assertEqual(result["frames"]["low_1_percent_fps"],50)
            self.assertEqual(result["frames"]["low_0_1_percent_fps"],50)
            self.assertEqual(result["frames"]["maximum_instantaneous_fps"],100)
            self.assertAlmostEqual(result["frames"]["p99_9_frame_time_ms"],19.99)
            self.assertEqual(result["processes"]["host"]["cpu_percent_machine"]["median"],10)
            self.assertEqual(result["processes"]["host"]["private_bytes"]["peak"],220)
            self.assertEqual(result["processes"]["host"]["samples"],2)
            self.assertEqual(result["processes"]["game"]["samples"],1)
            self.assertEqual(result["processes"]["game"]["cpu_percent_machine"]["median"],50)
            for value in ("0","nan","inf","-inf","-1",""):
                frames.write_text('dt\n"'+value+'"\n',encoding="utf-8")
                with self.assertRaises(ValueError): summarize(root,frames,"dt")

    def test_low_is_reciprocal_of_tail_mean_not_percentile_or_mean_fps(self):
        result = self.summarize_frames(list(range(200, 0, -20)) + [10] * 990)
        self.assertAlmostEqual(result["average_fps"],1000 / 11)
        self.assertEqual(result["low_1_percent_tail_frames"],10)
        self.assertAlmostEqual(result["low_1_percent_fps"],1000 / 110)
        self.assertEqual(result["low_0_1_percent_tail_frames"],1)
        self.assertEqual(result["low_0_1_percent_fps"],5)
        self.assertAlmostEqual(result["p99_frame_time_ms"],10.1)
        self.assertAlmostEqual(result["fps_at_p99_frame_time"],1000 / 10.1)
        self.assertAlmostEqual(result["p99_9_frame_time_ms"],180.02)
        self.assertEqual(result["maximum_instantaneous_fps"],100)

    def test_fractional_tail_count_rounds_up(self):
        result = self.summarize_frames([10] * 999 + [100, 300])
        self.assertEqual(result["low_1_percent_tail_frames"],11)
        self.assertAlmostEqual(result["low_1_percent_fps"],1000 / (490 / 11))
        self.assertEqual(result["low_0_1_percent_tail_frames"],2)
        self.assertEqual(result["low_0_1_percent_fps"],5)

    def test_single_frame_and_insufficient_tail_samples(self):
        result = self.summarize_frames([25])
        for key in ("average_fps", "low_1_percent_fps", "low_0_1_percent_fps",
                    "maximum_instantaneous_fps", "fps_at_p99_frame_time"):
            self.assertEqual(result[key],40)
        for key in ("p99_frame_time_ms", "p99_9_frame_time_ms"):
            self.assertEqual(result[key],25)
        for label in ("1", "0_1"):
            self.assertEqual(result[f"low_{label}_percent_tail_frames"],1)
            self.assertEqual(result[f"low_{label}_percent_sample_status"],"insufficient_tail_samples")

    def test_tail_sample_status_boundary(self):
        for label, denominator in (("1", 100), ("0_1", 1000)):
            for count, expected in ((9 * denominator, "insufficient_tail_samples"),
                                    (9 * denominator + 1, "minimum_tail_samples_met")):
                with self.subTest(label=label,count=count):
                    result = self.summarize_frames([10] * count)
                    self.assertEqual(result[f"low_{label}_percent_sample_status"],expected)
                    self.assertEqual(result[f"low_{label}_percent_tail_frames"],
                                     9 if count == 9 * denominator else 10)
                    self.assertEqual(result["minimum_low_tail_frames"],10)

    def test_frame_stream_identity(self):
        identity = {"Application": ["L4D2Bridge64.exe"] * 2,
                    "ProcessID": ["123"] * 2, "SwapChainAddress": ["0x10"] * 2}
        result = self.summarize_frames([10, 20],identities=identity)
        self.assertEqual(result["source"],{key: values[0] for key,values in identity.items()})
        for column, entries in (("Application", ["left4dead2.exe", "L4D2Bridge64.exe"]),
                                ("ProcessID", ["123", "456"]),
                                ("SwapChainAddress", ["0x10", "0x20"]),
                                ("ProcessID", ["123", ""])):
            with self.subTest(column=column,entries=entries):
                with self.assertRaisesRegex(ValueError,"one process/swapchain"):
                    self.summarize_frames([10, 20],identities={column: entries})
        self.assertEqual(self.summarize_frames([10, 20])["source"],{})

    def test_empty_capture_and_unit_overflow_rejected(self):
        with self.assertRaisesRegex(ValueError,"positive, finite and nonempty"):
            self.summarize_frames([])
        with self.assertRaisesRegex(ValueError,"overflow milliseconds"):
            self.summarize_frames([1e308],unit="s")

    def test_nonfinite_fps_and_unknown_unit_rejected(self):
        for values in ([5e-324], [10, 1e-308]):
            with self.subTest(values=values):
                with self.assertRaisesRegex(ValueError,"finite FPS"):
                    self.summarize_frames(values)
        with self.assertRaisesRegex(ValueError,"unit must be ms or s"):
            self.summarize_frames([10],unit="us")

    def test_ambiguous_frame_csv_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "process-metrics.csv").write_text(
                "role,state,cpu_percent_machine,working_set_bytes,private_bytes\n"
                "host,running,10,100,200\n", encoding="utf-8")
            frames = root / "frames.csv"
            # The second PID column must not hide a mixed process stream.
            frames.write_text("FrameTimeMs,ProcessID,ProcessID\n10,123,456\n20,789,456\n",
                              encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"Duplicate frame capture columns"):
                summarize(root,frames)
            frames.write_text("FrameTimeMs,ProcessID\n10,123,456\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"more values than columns"):
                summarize(root,frames)

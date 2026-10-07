import csv, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"scripts"))
from analyze_baseline import summarize

class Baseline(unittest.TestCase):
    def test_units_metrics_and_invalid_frames(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/"process-metrics.csv").write_text("role,state,cpu_percent_machine,working_set_bytes,private_bytes\nhost,running,,100,200\nhost,running,10,120,220\n",encoding="utf-8")
            frames=root/"frames.csv"; frames.write_text("dt\n0.01\n0.02\n",encoding="utf-8")
            result=summarize(root,frames,"dt","s")
            self.assertAlmostEqual(result["frames"]["average_fps"],1000/15)
            self.assertEqual(result["processes"]["host"]["cpu_percent_machine"]["median"],10)
            self.assertEqual(result["processes"]["host"]["private_bytes"]["peak"],220)
            for value in ("0","nan","-1",""):
                frames.write_text("dt\n"+value+",\n",encoding="utf-8")
                with self.assertRaises(ValueError): summarize(root,frames,"dt")

"""checkpoint.py 单元测试"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from checkpoint import CheckpointManager


class TestCheckpointManager:
    def _make_manager(self, tmp_path):
        filepath = os.path.join(tmp_path, "test_checkpoint.json")
        return CheckpointManager(checkpoint_file=filepath)

    def test_init_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = self._make_manager(tmp)
            assert os.path.exists(mgr.checkpoint_file)

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = self._make_manager(tmp)
            mgr.save_checkpoint("2024-01-15 10:30:00")
            loaded = mgr.load_checkpoint()
            assert loaded == "2024-01-15 10:30:00"

    def test_default_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = self._make_manager(tmp)
            loaded = mgr.load_checkpoint()
            assert loaded is not None  # 默认 7 天前

    def test_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = self._make_manager(tmp)
            mgr.save_checkpoint("2024-06-01 00:00:00")
            mgr.reset()
            loaded = mgr.load_checkpoint()
            # reset 后应该有新的默认值（7 天前），不是 2024-06-01
            assert loaded != "2024-06-01 00:00:00"

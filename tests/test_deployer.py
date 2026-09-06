import unittest
import tempfile
import zipfile
from pathlib import Path
from mcode_web_deploy.deployer import zip_directory, resolve_project_and_dist, detect_project_name, DeployError


class TestDeployer(unittest.TestCase):
    def test_zip_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "index.html").write_text("<h1>Hello</h1>", encoding="utf-8")
            (tmp_path / "test.txt").write_text("sample", encoding="utf-8")
            sub = tmp_path / "sub"
            sub.mkdir()
            (sub / "sub.js").write_text("console.log('hi');", encoding="utf-8")

            zip_bytes = zip_directory(tmp_path)
            self.assertGreater(len(zip_bytes), 0)

            # verify zip content
            import io
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                names = zf.namelist()
                self.assertIn("index.html", names)
                self.assertIn("test.txt", names)
                self.assertIn("sub/sub.js", names)

    def test_resolve_project_and_dist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            dist = tmp_path / "dist"
            dist.mkdir()
            (dist / "index.html").write_text("<h1>Dist</h1>", encoding="utf-8")

            proj, resolved_dist = resolve_project_and_dist(tmp_path)
            self.assertEqual(resolved_dist, dist)

    def test_resolve_root_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "index.html").write_text("<h1>Root</h1>", encoding="utf-8")

            proj, resolved_dist = resolve_project_and_dist(tmp_path)
            self.assertEqual(resolved_dist, tmp_path)

    def test_detect_project_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "package.json").write_text('{"name": "my-demo-app"}', encoding="utf-8")

            name = detect_project_name(tmp_path)
            self.assertEqual(name, "my-demo-app")


if __name__ == "__main__":
    unittest.main()

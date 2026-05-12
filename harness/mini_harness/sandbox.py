import shlex
import subprocess
from pathlib import Path

IMAGE_TAG = "mini-harness:latest"
DOCKERFILE_DIR = Path(__file__).resolve().parent.parent / "container"


class Sandbox:
    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()
        self.container_id: str | None = None

    def _ensure_image(self) -> None:
        existing = subprocess.run(
            ["docker", "images", "-q", IMAGE_TAG],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if existing:
            return
        print(f"Building {IMAGE_TAG} from {DOCKERFILE_DIR}...")
        subprocess.run(
            ["docker", "build", "-t", IMAGE_TAG, str(DOCKERFILE_DIR)],
            check=True,
        )

    def start(self) -> None:
        self._ensure_image()
        result = subprocess.run(
            [
                "docker", "run", "-d", "--rm",
                "--network", "none",
                "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges",
                "--read-only",
                "--tmpfs", "/tmp",
                "-v", f"{self.workspace}:/workspace",
                "--memory", "512m",
                "--pids-limit", "256",
                "-w", "/workspace",
                IMAGE_TAG,
                "sleep", "infinity",
            ],
            capture_output=True, text=True, check=True,
        )
        self.container_id = result.stdout.strip()

    def exec(self, argv: list[str]) -> tuple[int, str, str]:
        if not self.container_id:
            raise RuntimeError("Sandbox is not running.")
        result = subprocess.run(
            ["docker", "exec", self.container_id, *argv],
            capture_output=True, text=True,
        )
        return result.returncode, result.stdout, result.stderr

    def write_file(self, path: str, content: str) -> tuple[int, str]:
        if not self.container_id:
            raise RuntimeError("Sandbox is not running.")
        cmd = f"cat > {shlex.quote(path)}"
        result = subprocess.run(
            ["docker", "exec", "-i", self.container_id, "sh", "-c", cmd],
            input=content, text=True, capture_output=True,
        )
        return result.returncode, result.stderr

    def stop(self) -> None:
        if self.container_id:
            subprocess.run(
                ["docker", "kill", self.container_id],
                capture_output=True,
            )
            self.container_id = None

    def __enter__(self) -> "Sandbox":
        self.start()
        return self

    def __exit__(self, *_exc) -> None:
        self.stop()

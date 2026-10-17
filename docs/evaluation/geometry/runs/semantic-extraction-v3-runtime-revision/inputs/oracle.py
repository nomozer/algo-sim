"""Path adapter only; execute the parent mathematical oracle unchanged, with its own original inputs."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[2] / "semantic-extraction-schema-contract/inputs/oracle.py"),
                   run_name="__main__")

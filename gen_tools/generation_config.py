from dataclasses import dataclass
from pathlib import Path

@dataclass
class GenerationConfig:
    measurement_name: str
    workdir: Path
    outpath: str
    mcprod_path: str
    genprod_image: str
    genprod_repo: str
    genprod_branch: str


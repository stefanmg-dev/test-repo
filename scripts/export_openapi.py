import json
import sys
from pathlib import Path


project_root = Path(__file__).resolve().parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(
        0,
        str(project_root),
    )

from api import app


project_root = Path(__file__).resolve().parent.parent
output_path = (
    project_root
    / "postman"
    / "document-processing.openapi.json"
)

schema = app.openapi()

output_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)

output_path.write_text(
    json.dumps(
        schema,
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)

print(output_path)
print(
    f"Exported {len(schema.get('paths', {}))} API paths"
)

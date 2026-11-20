from fastapi.responses import Response

from app.manifest import canonical


def evidence_file(document, source):
    return Response(canonical({**document, "source": source}), media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="serial-{document["id"][:12]}.json"'})

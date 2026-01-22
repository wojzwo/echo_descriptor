from __future__ import annotations
import os
import uvicorn

def main() -> None:
    host = os.environ.get("ECHOZ_HOST", "127.0.0.1")
    port = int(os.environ.get("ECHOZ_PORT", "8000"))
    uvicorn.run("echo_desc.web.webapp:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    main()
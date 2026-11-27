from __future__ import annotations


def main() -> None:
    import uvicorn

    from .settings import settings

    uvicorn.run(
        "hcdmap_backend.app:app",
        host=settings.http_host,
        port=settings.http_port,
        reload=False,
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from ytmusicapi import YTMusic
from ytmusicapi.exceptions import YTMusicError


APP_ROOT = Path(__file__).resolve().parent.parent
STATIC_ROOT = APP_ROOT / "site"

SearchFilter = Literal[
    "songs",
    "videos",
    "albums",
    "artists",
    "playlists",
    "community_playlists",
    "featured_playlists",
    "profiles",
    "podcasts",
    "episodes",
]
SearchScope = Literal["uploads", "library"]


@lru_cache(maxsize=1)
def get_ytmusic() -> YTMusic:
    return YTMusic()


async def call_ytmusic(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    try:
        return await asyncio.to_thread(func, *args, **kwargs)
    except YTMusicError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - keep API errors shaped for clients.
        raise HTTPException(status_code=500, detail="Unexpected API error") from exc


app = FastAPI(
    title="YTMusicAPI Cloud",
    version="1.0.0",
    description="A read-only HTTP wrapper around the unofficial ytmusicapi Python library.",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

if STATIC_ROOT.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_ROOT / "assets"), name="assets")


@app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(STATIC_ROOT / "index.html")


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/search", tags=["catalog"])
async def search(
    q: Annotated[str, Query(min_length=1, description="Search query")],
    filter: SearchFilter | None = Query(default=None),
    scope: SearchScope | None = Query(default=None),
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ignore_spelling: bool = False,
) -> dict[str, Any]:
    client = get_ytmusic()
    data = await call_ytmusic(
        client.search,
        q,
        filter=filter,
        scope=scope,
        limit=limit,
        ignore_spelling=ignore_spelling,
    )
    return {"query": q, "results": data}


@app.get("/api/suggestions", tags=["catalog"])
async def suggestions(
    q: Annotated[str, Query(min_length=1, description="Partial query")],
) -> dict[str, Any]:
    client = get_ytmusic()
    data = await call_ytmusic(client.get_search_suggestions, q)
    return {"query": q, "suggestions": data}


@app.get("/api/song/{video_id}", tags=["catalog"])
async def song(video_id: str) -> Any:
    client = get_ytmusic()
    return await call_ytmusic(client.get_song, video_id)


@app.get("/api/album/{browse_id}", tags=["catalog"])
async def album(browse_id: str) -> Any:
    client = get_ytmusic()
    return await call_ytmusic(client.get_album, browse_id)


@app.get("/api/artist/{channel_id}", tags=["catalog"])
async def artist(channel_id: str) -> Any:
    client = get_ytmusic()
    return await call_ytmusic(client.get_artist, channel_id)


@app.get("/api/playlist/{playlist_id}", tags=["catalog"])
async def playlist(
    playlist_id: str,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> Any:
    client = get_ytmusic()
    return await call_ytmusic(client.get_playlist, playlist_id, limit=limit)


@app.get("/api/watch", tags=["catalog"])
async def watch_playlist(
    video_id: str | None = Query(default=None),
    playlist_id: str | None = Query(default=None),
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    radio: bool = False,
    shuffle: bool = False,
) -> Any:
    if not video_id and not playlist_id:
        raise HTTPException(status_code=400, detail="Provide video_id or playlist_id")

    client = get_ytmusic()
    return await call_ytmusic(
        client.get_watch_playlist,
        videoId=video_id,
        playlistId=playlist_id,
        limit=limit,
        radio=radio,
        shuffle=shuffle,
    )


@app.get("/api/lyrics/{browse_id}", tags=["catalog"])
async def lyrics(browse_id: str, timestamps: bool = False) -> Any:
    client = get_ytmusic()
    return await call_ytmusic(client.get_lyrics, browse_id, timestamps=timestamps)


@app.get("/api/charts", tags=["catalog"])
async def charts(country: Annotated[str, Query(min_length=2, max_length=2)] = "ZZ") -> Any:
    client = get_ytmusic()
    return await call_ytmusic(client.get_charts, country=country.upper())


@app.get("/api/moods", tags=["catalog"])
async def mood_categories() -> Any:
    client = get_ytmusic()
    return await call_ytmusic(client.get_mood_categories)


@app.get("/api/moods/{params}", tags=["catalog"])
async def mood_playlists(params: str) -> Any:
    client = get_ytmusic()
    return await call_ytmusic(client.get_mood_playlists, params)

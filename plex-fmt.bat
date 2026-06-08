@echo off
setlocal
uv run --project "%~dp0..\plex-media-formatter" plex-fmt %*
exit /b %ERRORLEVEL%
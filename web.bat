@echo off
setlocal enableextensions

REM TDMS - Start or stop the stack with optional Redis clean
REM Usage:
REM   web.bat           -> restart and tail logs
REM   web.bat clean     -> remove TDMS tokens then restart and tail logs
REM   web.bat full      -> FLUSHDB then restart and tail logs
REM   web.bat up        -> bring up detached
REM   web.bat down      -> bring down containers
REM   web.bat stop      -> alias for down

set MODE=%~1
if "%MODE%"=="" set MODE=restart

REM Handle simple commands first
if /I "%MODE%"=="down" (
  echo [TDMS] Stopping containers
  docker compose down --timeout 2
  exit /b 0
)

if /I "%MODE%"=="stop" (
  echo [TDMS] Stopping containers
  docker compose down --timeout 2
  exit /b 0
)

if /I "%MODE%"=="up" (
  echo [TDMS] Starting stack detached
  docker compose up -d
  exit /b 0
)

REM For restart/clean/full modes
set DO_CLEAN=0
set DO_FLUSH=0

if /I "%MODE%"=="clean" (
  set DO_CLEAN=1
  set MODE=restart
)

if /I "%MODE%"=="full" (
  set DO_FLUSH=1
  set MODE=restart
)

echo [TDMS] Bringing stack down
docker compose down --timeout 2 >nul 2>&1

if "%DO_FLUSH%"=="1" (
  echo [TDMS] Redis FLUSHDB
  docker compose up -d redis
  docker compose exec -T tdms-redis redis-cli FLUSHDB
  docker compose down >nul 2>&1
)

if "%DO_CLEAN%"=="1" (
  echo [TDMS] Removing TDMS tokens in Redis
  docker compose up -d redis
  docker compose exec -T tdms-redis redis-cli DEL tdms:google:access_token tdms:google:token_expiry >nul 2>&1
  docker compose exec -T tdms-redis sh -lc "for k in $(redis-cli --scan --pattern 'tdms:sync:token:*'); do redis-cli DEL \"$k\"; done"
  docker compose exec -T tdms-redis sh -lc "for k in $(redis-cli --scan --pattern 'tdms:sync:lock:*'); do redis-cli DEL \"$k\"; done"
  docker compose exec -T tdms-redis sh -lc "for k in $(redis-cli --scan --pattern 'tdms:sync:last_sync:*'); do redis-cli DEL \"$k\"; done"
  docker compose down >nul 2>&1
)

echo [TDMS] Building web and worker
docker compose build web worker

echo [TDMS] Starting stack detached and tailing logs
docker compose up -d
echo [TDMS] Attaching logs - press Ctrl+C to stop tailing
docker compose logs -f web worker redis

echo.
echo [TDMS] Log tail ended. Containers continue running.

endlocal
exit /b 0

# Windows Substrate Inject — BIG ALPHA (user-mode)

**Platform:** v12.0.0  
**Script:** `scripts/inject_alpha_windows_substrate.ps1`

## Honesty (critical)

| Claim | Reality |
|-------|---------|
| “Inject into Windows kernel” (ring-0) | **Not done** — requires WDK, signed `.sys`, admin + Secure Boot policy |
| What we inject | **User-mode substrate**: env, Startup, Scheduled Task, `~/.fusion` pins |
| Meister Hasch | Labor frame preserved — no Realraum offense |

This is the correct, safe, reversible mapping of “kernel inject” language onto Windows **session substrate** for Fusion Hero OS.

## Run

```powershell
cd C:\Users\Admin\fusion-hero-os
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\inject_alpha_windows_substrate.ps1
```

## What it does

1. Pins `prompt.txt`, `alpha_meister_hasch.md`, seal → `~/.fusion/`
2. Writes `~/.fusion/alpha_pin.json` (cycle BIG_ALPHA, meister hash)
3. Sets **User** env: `FUSION_CYCLE`, `FUSION_REPO_ROOT`, `FUSION_PLATFORM_VERSION`, …
4. Registers **Startup** `FusionHeroOS-AlphaEudaemon.cmd`
5. Registers **Task** `FusionHeroOS-AlphaEudaemon` (AtLogOn, Limited)
6. Runs immediate `eudaemon_agent` pulse
7. State: `~/.fusion/windows_alpha_inject.json`

## Verify

```powershell
Get-Content $env:USERPROFILE\.fusion\alpha_pin.json
Get-ScheduledTask -TaskName FusionHeroOS-AlphaEudaemon -ErrorAction SilentlyContinue
[Environment]::GetEnvironmentVariable("FUSION_CYCLE","User")
python -m fusion_hero_os.core.autoload_controller --status
```

## Uninstall (optional)

```powershell
Unregister-ScheduledTask -TaskName FusionHeroOS-AlphaEudaemon -Confirm:$false
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\FusionHeroOS-AlphaEudaemon.cmd" -ErrorAction SilentlyContinue
# clear user env if desired via System Properties → Environment
```

## Related

- `scripts/prepare_reboot_autoload.ps1` — full dashboard autoload
- `docs/ops/AUTOLOAD_CONTROLLER.md`
- `docs/dissertation/ALPHA_MEISTER_HASCH.md`

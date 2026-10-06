# Steam Overlay input investigation after v1.1

Status: **diagnostic build; Steam input is not yet fixed or hardware-validated.**

The new hardware report changes the scope: normal Shift+Tab does nothing, but L4D2's Join Server / Steam Group action can open a visible overlay. The visible UI accepts no mouse input and Shift+Tab cannot close it. This establishes that activation and rendering can work in this installation. Do not replace them or add a second Steam API activation path as an input workaround.

## What the source establishes

- The original game HWND belongs to `left4dead2.exe`. D3D9 commands cross the Bridge to the selected Host, where the actual DXVK device/swapchain and Vulkan presentation run. A Steam Vulkan layer intercepting that presentation must run in that Host. This does **not** prove which Steam component is drawing the reported overlay, receiving its input, or tracking its active state.
- With `server.presenterWindow=True`, windowed vanilla-DXVK presentation uses a Host-owned child of the game HWND. This child has its own message thread and starts **disabled**, so mouse input reaches the game. With the option off, presentation retains the original game-owned HWND. The normal foreground root remains the game window.
- The implemented ReShade public event changes `Presenter::capture`, enables the child for mouse input and sends the existing `UWM_REMIX_UIACTIVE_MSG` to the client. The client then neutralizes game input through its existing Win32/DirectInput/raw-input hooks. None of this state is currently connected to a Steam active/inactive notification.
- The client's legacy forwarding calls `gpRemixMessageChannel->send`, implemented as `PostThreadMessage` to the Remix renderer handshake thread. It does not target the presenter HWND. Vanilla DXVK does not implement that Remix handshake. The independent Bridge server message thread handles focus/timeout notifications; it is not a Steam input dispatcher.
- The existing foreground-scoped low-level keyboard hook posts legacy key messages to the presenter. Successful `PostMessage` means a message was enqueued; it does not prove that Steam consumes it, uses that message queue, or accepts synthetic legacy keyboard messages. It does not replicate raw input, Steam's internal focus checks or a thread's keyboard state.
- Steam and ReShade do not share a public overlay interface. Module presence and a visible UI do not prove that Steam's input hooks are attached to the presenter, nor that ReShade capture should be reused blindly. Two overlays will also need separate active states whose union controls game input suppression.

[Earlier recorded evidence](V1.1-VALIDATION.md) includes `renderer64=1` in the Host; it establishes that the renderer DLL was loaded in that run, not its current input receiver.

The unconnected Steam state is an established integration gap. Its causal relationship to this failure still requires runtime evidence. Focus changes, game mouse capture/clip, WndProc hook ordering and which process receives input remain competing explanations. There is no basis yet for changing global focus, attaching thread input queues, injecting Steam into another process, or creating another overlay/input subsystem.

## Changes in the diagnostic build

New options, both off when omitted:

```ini
client.steamInputDiagnostics = True
server.steamInputDiagnostics = True
logLevel = Info
logApiCalls = False
logServerCommands = False
```

Merge [the snippet](../config/STEAM-INPUT-DIAGNOSTICS.conf) into the existing `bin/.l4d2bridge/bridge.conf`. Preserve the current Host selection, presenter, ReShade and retention options. The normal shipped configuration is unchanged.

The same diagnostic helper runs inside both processes. It samples at most once per second from Present, including when the game stops receiving ordinary input messages. It does not activate Steam, register an unofficial Steam callback ABI, change capture, enable a window, inject input or alter resource policy.

- `event=modules`: process role, PID/architecture and actual presence of `GameOverlayRenderer.dll`, `GameOverlayRenderer64.dll`, `SteamOverlayVulkanLayer.dll`, `SteamOverlayVulkanLayer64.dll`, `steam_api.dll` and `steam_api64.dll`. Delayed load/unload is detected. Presence alone is not activity or rendering proof.
- `event=state`: game/presenter HWND ownership, presenter enabled/capture state, foreground root, foreground thread active/focus/capture HWNDs, local game/presenter thread GUI state, cursor hit-test HWND ownership, clip rectangle size and local WndProc address/module. `downstream` / `downstream_module` identify the client's saved game WndProc. The client observes the actual WndProc through the existing original API trampoline, bypassing Bridge's virtualized GetWindowLong result. `gui_ok=0` or `local_gui_ok=0` means that thread observation was unavailable. Host `capture` denotes ReShade/Bridge capture, **not Steam's active state**.
- `event=route` (client): whether the legacy Remix channel has a handshake target, and current message-pump/custom-hook options. `presenter_delivery=0` describes this legacy channel, not the separate presenter keyboard hook.
- `event=messages`: counts since the previous sample of mouse, keyboard, raw-input and client forwarding attempts, plus Shift+Tab keydown observations. Counts do not log typed text, general key identities, mouse coordinates or raw-input contents. Auto-repeat can increase the shortcut count.

Client counts are observed at the existing Bridge message-processing entry. The forwarding count means the existing message channel's `send` was invoked, not that Steam received it. Host counts are messages that reach the presenter's WndProc; messages consumed earlier by a Steam/ReShade GetMessage hook can be absent. A zero count alone cannot identify a broken route. Without a presenter, no Host window-message counts are collected. The diagnostic reads GUI state for the relevant foreground/window threads but does not profile other applications or hook another application's input.

## Short hardware reproduction

Back up the current client/Host binaries. Install the matching diagnostic client and Host together; keep the existing DXVK backend, ReShade and database. Stay in the main menu, preferably outside a live multiplayer session.

1. Enable the two flags above. Start with the exact configuration that reproduces the issue. Note whether `server.presenterWindow` and ReShade are enabled, and which Host runs.
2. Wait roughly 5 seconds. Press Shift+Tab once, then wait 5 seconds.
3. Use L4D2's Join Server / Steam Group action that already opens Steam. Record the approximate open time.
4. Move the mouse, attempt one click, press Shift+Tab once to close, and wait 5 seconds. Report which actions worked. If it remains stuck, terminate the game as before; this diagnostic build does not promise an escape key or a fix.
5. Send `bridge32.log` and `bridge64.log` for x64 Host, or `bridge32.log` and `bridge-host32.log` for x86 Host. Preserve this failed run before restarting; the logs can be overwritten. Include the current presenter/ReShade settings and the times of opening/closing attempts.

One short reproduction is enough for the first diagnosis; no ETL/system-wide profiling is needed. Disable both flags after testing. If a presenter-on/off A/B is necessary, choose that after inspecting this run, rather than changing several input policies at once.

## Next fix and acceptance gate

Use the paired observations to identify the actual receiver and missing transition. Prefer the existing presenter/message-channel/game-input suppression infrastructure. Do not infer Steam active state by toggling a boolean on Shift+Tab: Steam can open through game requests, hotkeys can fail and focus can change.

Required hardware acceptance: open through the game and Shift+Tab, mouse movement/clicks, keyboard input, repeated Shift+Tab close/open, input returning to the game, Alt+Tab, and ReShade coexistence. Windows native tests can validate the observer and presenter mechanics but cannot claim proprietary Steam Overlay compatibility.

The v1.1 release remains the tested baseline. The investigation does not retroactively mark Steam input as supported, and its findings must not be described as a released fix.

## Attribution

Existing NVIDIA Bridge notices are retained. Newly added diagnostic code is MIT licensed:

`All newly added implementation code in this fork was generated by OpenAI Codex from prompts and specifications provided by yeyunyyds.`

# Steam Overlay input investigation after v1.1

Status: **passive diagnostics after an input-regression rollback; Steam support is not fixed or released.**

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

The window diagnostic helper runs inside both processes. It samples at most once per second from Present, including when the game stops receiving ordinary input messages. It also observes the legacy public Steamworks activation callback in the client and the shortcut's keyboard state in the presenter thread. With only diagnostic flags enabled, it does not change capture or input. The optional correction flags below enable a separate hardware experiment. Neither mode activates Steam or changes resource policy.

- `event=steam-callback`: registers callback 331 only when `client.steamInputDiagnostics=True` and the game's existing `steam_api.dll` exports `SteamAPI_RegisterCallback`. The independent ABI declaration follows Valve's Steamworks SDK 1.51: three callback virtual methods and the one-byte legacy `GameOverlayActivated_t` payload. It includes no SDK implementation, modern optional payload fields or Steam binaries. The observer/code modules stay alive for the process lifetime to avoid a callback pointing into unloaded code. It uses the game's own callback pump; it never calls `SteamAPI_Init`, `RunCallbacks`, `Shutdown` or an activation API. Registration is not proof of callback delivery on this installation.
- `event=steam-active`: records real callback delivery with `active=1/0`. This is distinct from the combined ReShade/Steam Bridge `capture` flag. Diagnostic-only mode performs no capture transition.
- `event=tab-dispatch`: for presenter Tab keydown messages only, records Shift/Tab from `GetKeyState`, `GetKeyboardState` and `GetAsyncKeyState` immediately before TranslateMessage/DispatchMessage. A mismatch establishes a queue-state difference, not proof that Steam uses a particular Win32 API. It logs no text or unrelated key identities. Earlier GetMessage hooks may consume messages before this observation.

- `event=modules`: process role, PID/architecture and actual presence of `GameOverlayRenderer.dll`, `GameOverlayRenderer64.dll`, `SteamOverlayVulkanLayer.dll`, `SteamOverlayVulkanLayer64.dll`, `steam_api.dll` and `steam_api64.dll`. Delayed load/unload is detected. Presence alone is not activity or rendering proof.
- `event=state`: game/presenter HWND ownership, presenter enabled/capture state, foreground root, foreground thread active/focus/capture HWNDs, local game/presenter thread GUI state, cursor hit-test HWND ownership, clip rectangle size and local WndProc address/module. `downstream` / `downstream_module` identify the client's saved game WndProc. The client observes the actual WndProc through the existing original API trampoline, bypassing Bridge's virtualized GetWindowLong result. `gui_ok=0` or `local_gui_ok=0` means that thread observation was unavailable. Host `capture` denotes ReShade/Bridge capture, **not Steam's active state**.
- `event=route` (client): whether the legacy Remix channel has a handshake target, and current message-pump/custom-hook options. `presenter_delivery=0` describes this legacy channel, not the separate presenter keyboard hook.
- `event=messages`: counts since the previous sample of mouse, keyboard, raw-input and client forwarding attempts, plus Shift+Tab keydown observations. Counts do not log typed text, general key identities, mouse coordinates or raw-input contents. Auto-repeat can increase the shortcut count.

Client counts are observed at the existing Bridge message-processing entry. The forwarding count means the existing message channel's `send` was invoked, not that Steam received it. Host counts are messages that reach the presenter's WndProc; messages consumed earlier by a Steam/ReShade GetMessage hook can be absent. A zero count alone cannot identify a broken route. Without a presenter, no Host window-message counts are collected. The diagnostic reads GUI state for the relevant foreground/window threads but does not profile other applications or hook another application's input.

## Short hardware reproduction

### Opt-in correction build

The 22:31–22:32 paired logs establish callback delivery: client PID 17584 registered callback 331 at `22:31:03.592` and received `active=1` at `22:31:52.543`. Host PID 20776 nevertheless remained at `enabled=0 capture=0`, with mouse hit testing on the game. Two shortcut attempts at `22:32:05.722` and `22:32:08.554` both reported `shift_queue=1 tab_queue=0 shift_async=1 tab_async=1`; `GetKeyboardState` likewise reported Tab up. No deactivation callback was observed before shutdown. This proves the client activation notification is available and that the forwarded Tab message lacks matching queue state. It does not prove which keyboard API Steam reads.

The correction experiment is off when these options are omitted:

```ini
client.steamOverlayInput = True
server.steamOverlayInput = True
```

It requires the existing windowed presenter configuration (`server.presenterWindow=True`, `server.presenterInput=True`) and existing client input hooks. Use the matching client and x64 Host update together. Preserve the current working ReShade settings, DXVK backend and retention policy. The packaged `STEAM-INPUT-DIAGNOSTICS.conf` now includes both correction and diagnostic flags; merge it rather than replacing the complete configuration.

The state-forwarding/capture experiment remains available only for isolated development tests. It forwards actual callback state to the Host-owned presenter, with independent Steam/ReShade capture sources. It is **not recommended for users**. The packaged diagnostic snippet explicitly disables both correction flags.

Commit `33e8cb2` also changed Host keyboard state before dispatch and moved focus to the child. The subsequent hardware test failed and reported gameplay input becoming unreliable. Those keyboard-state writes and focus changes have been removed. Current diagnostics only read keyboard state; the original v1.1 keyboard-hook behavior is restored. Disabling the two experiment flags preserves the normal ReShade input path.

The current observer additionally records `sdk_flags` and `sdk_callback` after `SteamAPI_RegisterCallback`. `registered` now reflects the SDK-written registration bit rather than merely successful export lookup/calling. The registration export returns void: reaching it did not itself prove acceptance. Missing activation events must be investigated independently of the Host capture path.

The initial registration-field test exposed a 32-bit layout mismatch in the standalone callback declaration (64-bit passed). The observer now inherits from a separate legacy callback base containing only the three virtual functions, byte flags and integer callback ID. Its size is asserted as 12 bytes on x86 and 16 on x64; SDK-manager writes to that base are tested independently from the derived C++ function objects. Events include `base_bytes` and `diagnostics_revision=2`. This repairs the ABI declaration and the reliability of registration-field observation; it does not prove that the earlier missing activation events were caused by that layout mismatch.

To restore normal input, set **both** `steamOverlayInput` options to `False` and restart. Keep diagnostic flags enabled for the short reproduction below. The normal release configuration and main branch remain unchanged.

### Confirmed failed correction run: 22:47–22:48

The client logged `state_forwarding=1`, and the Host logged numerous `keyboard-state updated=1` events. This confirms execution of the correction build, unlike the earlier run. The tester reported ReShade working, Steam visible but unusable, and gameplay movement/Esc/clicks responding unreliably. No client `steam-active` or `steam-forward` event was recorded despite the visible Steam page. Host `steam-capture active=0` appears only during teardown; there is no activation transition. ReShade capture toggled at `22:48:00.233` / `22:48:00.597`.

The keyboard-state modification failed to make Steam respond and introduced a reported input regression. The logs do not show the Steam focus/capture branch executing, so it cannot explain this run through a Steam activation transition. A Host-owned child can share an input queue with its cross-process parent; writing keyboard state at forwarded-message dispatch can affect input processing in that shared queue. This is a plausible explanation for the regression, not a completed A/B causal proof. The failed writes and the unvalidated focus changes are rolled back rather than expanded. Native capture-union tests did not validate real gameplay input or proprietary Steam hooks.

Current acceptance for the rollback build: ordinary movement/clicks/Esc work, ReShade Home works, and a game-requested Steam opening is recorded with its real callback/registration diagnostics. Continued Steam input failure is expected to remain unresolved. Do not use this rollback as evidence that Steam input has been fixed.

### Follow-up run: 22:42–22:43

The tester reported ReShade working and all Steam interactions still failing. Both logs list `client.steamOverlayInput=True` and `server.steamOverlayInput=True`. However, registration still reports `capture_changed=0`, rather than the correction branch's `state_forwarding=1`. The client receives `active=1` at `22:43:11.977`, but no `steam-forward` event follows. Host shortcut dispatches retain `tab_queue=0` and have no `keyboard-state` correction events; no `steam-capture` event is present. ReShade capture toggles at `22:42:39.233` / `22:42:39.699`.

This run establishes continued failure and no observable execution of the correction paths. It does not yet establish failure of those paths after activation. First compare the installed client and Host SHA-256 against artifact `11392840438` (commit `33e8cb2`, run `37419352518`). The verified artifact contains the correction option names and event strings. Older diagnostic binaries accept/log arbitrary configuration keys without implementing the new correction. A version/loading mismatch is consistent with these observations; installed binary hashes and, if necessary, actual loaded module paths are required before asserting its cause or changing the input design again.

Back up the current client/Host binaries. Install the matching diagnostic client and Host together; keep the existing DXVK backend, ReShade and database. Stay in the main menu, preferably outside a live multiplayer session.

1. Enable the two flags above. Start with the exact configuration that reproduces the issue. Note whether `server.presenterWindow` and ReShade are enabled, and which Host runs.
2. Wait roughly 5 seconds. Press Shift+Tab once, then wait 5 seconds.
3. Use L4D2's Join Server / Steam Group action that already opens Steam. Record the approximate open time.
4. Move the mouse, attempt one click, press Shift+Tab once to close, and wait 5 seconds. Report which actions worked. If it remains stuck, terminate the game as before; this diagnostic build does not promise an escape key or a fix.
5. Send `bridge32.log` and `bridge64.log` for x64 Host, or `bridge32.log` and `bridge-host32.log` for x86 Host. Preserve this failed run before restarting; the logs can be overwritten. Include the current presenter/ReShade settings and the times of opening/closing attempts.

For the activation/keyboard-state build, wait five seconds after opening through the game action, then make two deliberate Shift+Tab attempts (hold Shift first, tap Tab, release both; wait two seconds between attempts). Try one mouse click. Do not repeatedly hold Tab, since auto-repeat obscures individual attempts. Keep all existing settings and the renderer backend unchanged. If the overlay cannot close, preserve the logs after terminating. A missing `steam-active` transition despite successful callback registration is itself a useful result; do not compensate by assuming visibility from the hotkey.

One short reproduction is enough for the first diagnosis; no ETL/system-wide profiling is needed. Disable both flags after testing. If a presenter-on/off A/B is necessary, choose that after inspecting this run, rather than changing several input policies at once.

## Next fix and acceptance gate

### Paired hardware reproduction: 21:29–21:30

The tester explicitly confirmed entering a server and opening Steam through the Steam Group UI. The overlay rendered, but mouse clicks continued to operate L4D2 behind it and Shift+Tab did not close it. This run therefore includes a visible-overlay failure, unlike the preceding run whose visible-overlay state was unconfirmed.

- Client PID 3612 loaded `GameOverlayRenderer.dll` and `steam_api.dll`. Host PID 21280 loaded `GameOverlayRenderer64.dll` and `SteamOverlayVulkanLayer64.dll`; neither Steam API DLL was loaded in the Host. Vulkan presentation runs in the Host, but these module observations do not isolate which Steam component draws each UI element.
- Game HWND `0x00260558` belongs to the client; presenter HWND `0x00080FB0` belongs to the Host. All 73 sampled Host states reported `enabled=0 capture=0`. In foreground-game samples, focus and cursor hit testing remained on the game. The counter totals were **0 Host mouse messages**, versus **6642 client mouse observations**. These are diagnostic observation counts, not unique physical events or counts specifically confined to the overlay-open interval.
- Host counters recorded 90 keyboard messages and 9 Shift+Tab observations. For example, `21:30:20.781` reported `keyboard=8 shift_tab=2`, and `21:30:22.785` reported `keyboard=10 shift_tab=2`, while capture remained off. The shortcut reaches the presenter WndProc; enqueue failure is not the explanation for this reproduction. This does not prove that Steam's input hook accepted it.
- The client legacy Remix channel remained unready (`remix_channel_ready=0 presenter_delivery=0`). This route does not supply mouse input to the vanilla-DXVK presenter. Client counts can include both message-pump and WndProc observations; twice the Host shortcut count does not establish duplicate injection.
- Both logs ended with successful shutdown cleanup. No crash was reported in this reproduction.

The established mouse-routing gap is that opening Steam never enables the Host presenter or activates the existing client input-suppression path. The keyboard shortcut is a separate unresolved acceptance problem: posted legacy messages alone do not reproduce a real input-queue keyboard state, raw input or Steam's focus assumptions. These logs do not identify which of those checks Steam uses.

The next focused integration should observe Steam's actual activation/deactivation in the game, then connect that state to the existing presenter capture mechanism independently of ReShade. Steam and ReShade active states must be combined so closing one cannot release the other's capture. Hotkey diagnostics should inspect only Shift/Tab state at the dispatch boundary before choosing a keyboard-state or focus correction. Do not implement hotkey-based guesses of overlay visibility, add another activation/rendering path, or describe this diagnosis as a working fix.

Use the paired observations to identify the actual receiver and missing transition. Prefer the existing presenter/message-channel/game-input suppression infrastructure. Do not infer Steam active state by toggling a boolean on Shift+Tab: Steam can open through game requests, hotkeys can fail and focus can change.

Required hardware acceptance: open through the game and Shift+Tab, mouse movement/clicks, keyboard input, repeated Shift+Tab close/open, input returning to the game, Alt+Tab, and ReShade coexistence. Windows native tests can validate the observer and presenter mechanics but cannot claim proprietary Steam Overlay compatibility.

The v1.1 release remains the tested baseline. The investigation does not retroactively mark Steam input as supported, and its findings must not be described as a released fix.

## Attribution

Existing NVIDIA Bridge notices are retained. Newly added diagnostic code is MIT licensed:

The Steam callback declarations are independently written against Valve's public legacy binary interface, referenced from [Steamworks SDK 1.51 steam_api_common.h](https://github.com/ValveSoftware/Proton/blob/proton_9.0/lsteamclient/steamworks_sdk_151/steam_api_common.h) and [isteamfriends.h](https://github.com/ValveSoftware/Proton/blob/proton_9.0/lsteamclient/steamworks_sdk_151/isteamfriends.h). Valve retains ownership of its Steam/Steamworks components and SDK. Those components are not redistributed or relicensed as project MIT code. Native API test doubles verify observer mechanics, not proprietary Steam compatibility.

`All newly added implementation code in this fork was generated by OpenAI Codex from prompts and specifications provided by yeyunyyds.`

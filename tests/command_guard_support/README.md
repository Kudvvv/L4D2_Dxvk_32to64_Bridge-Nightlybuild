# Actual Command / IPC guard regression

Run from the repository root after preparing the upstream source and applying
the production patch:

```powershell
./scripts/test_command_guard.ps1
```

The default source is `.deps/dxvk-remix`; use `-SourceDirectory <path>` for another
prepared source tree. The script follows the queue test's MSVC setup: separate
x86 and x64 compiler processes, `SetupVS` with toolset 14.29, C++17, `/O2 /MT`,
and `/W4 /WX`. `-CompileArchitecture x86` or `x64` only builds that architecture.
The normal invocation builds both and runs all scenarios. `-RunOnly` reuses the
last build only when the production source, harness, adapters and executable
hashes still match its metadata. It needs neither a game installation nor
graphics hardware.

For local validation without MSVC, pass `-MingwDirectory <w64devkit/bin>` containing
`i686-w64-mingw32-g++.exe` and `g++.exe`. This is an explicit fallback, not a
replacement for the MSVC CI check. It makes fixture-only namespace/dependent-base
and CRT syntax adjustments and excludes the unselected `BlockingCircularQueue`
header. These adjustments are identical in all variants; the active atomic
queue, data queue, shared memory and semaphore implementations remain real.

## Source boundary

The script compiles the **entire production `util_bridgecommand.cpp` as a separate
translation unit**, including both explicit Bridge template instantiations. It
links real `IpcChannel`, `AtomicCircularQueue`, `CircularQueue`/`CircularBuffer`,
`SharedMemory` and `NamedSemaphore` implementations. It does not extract or
reimplement the Command constructor, destructor, wait, serialization or
publication logic.

All source fixtures and binaries are generated below `.deps/command-guard-test`.
The `current` Command translation unit is checked byte-for-byte against the
selected production source. `seq_cst` restores the original implicit ordering;
`relaxed` adds explicit relaxed arguments. Source checks permit differences only
at the two guard loads and two guard stores. The script accepts either ordering
in the current source, so the test still compares both controls after the
production change. No production file or patch is edited.

Only external dependencies are adapted: fixed finite GlobalOptions timeouts,
inactive exception/data observers, disabled Tracy, and a logger that throws
instead of opening a dialog. The logger allows the actual Host runtime nesting
check to be tested. `/DNDEBUG` deliberately removes the earlier assertion; the
test's own `require` checks remain active. Fatal worker/transport failures exit
nonzero without dialogs, a 120-second watchdog bounds each process, and a
kill-on-close Job cleans up the Host on Client failure.

Known upstream signed/conversion and assert-only-parameter warnings are
suppressed only for production code. The harness and adapters retain `/W4 /WX`.
The MSVC fixture uses the original production headers; no GCC compatibility
changes apply there. Production inline API-wait/data accounting stays disabled;
the real queue wait/wake counters are enabled to verify event coverage.

## Scenarios and checks

Each guard variant runs four fresh x86 Client / x64 Host process pairs:

| Client Device producers | Commands each | Concurrent Module commands | Idle bursts |
| --- | --- | --- | --- |
| 1 | 20,000 | 0 | No |
| 1 | 4,096 | 0 | Yes |
| 4 | 5,000 | 0 | Yes |
| 4 | 5,000 | 5,000 from one producer | Yes |

Every request receives an actual Host Command response. Across three variants
this is 207,288 request/response pairs and 414,576 publications. Eight-slot header
rings and 4,096-byte mappings force repeated header/data wraps. Checks cover UID
order, per-producer order, scalar fields, variable copied/reserved blobs,
checksums, final data offsets, drained queues, cleared guards, and independent
Device/Module channels. Idle runs first exercise an empty response wait and then
require nonzero wait/wake counters and no wait/wake API failures.

The actual Host constructor must reject overlapping Command lifetimes while
allowing a simultaneous command on the other channel. Disabled-Bridge Commands
must set/clear their guards without changing data positions or publishing;
consecutive disabled Client Commands must also release the writer mutex.
Client same-thread recursion is intentionally excluded because its existing
nonrecursive mutex is acquired before the guard.

Build/source hashes are saved beside each executable in `build-metadata.json`;
all twelve successful scenario records are saved in `results.json`. No fixture
depends on the repository's `results/` directory.

This is a native transport regression. It does not validate game performance,
graphics-backend behavior, live shutdown callbacks or crash-history handling.

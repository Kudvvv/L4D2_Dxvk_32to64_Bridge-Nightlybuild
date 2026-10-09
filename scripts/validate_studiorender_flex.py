# SPDX-License-Identifier: MIT
"""Exercise the pinned engine's actual x86 instructions offline with Unicorn.

Requires pefile and unicorn, plus the user's own original DLL. No game binaries
or proprietary source code are bundled. This does not replace game validation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile
from unicorn import (Uc, UcError, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ,
                     UC_PROT_WRITE, UC_PROT_EXEC, UC_ERR_WRITE_UNMAPPED,
                     UC_ERR_READ_UNMAPPED)
from unicorn.x86_const import *

from patch_studiorender_flex import patch_image, CACHE_RVA, NEW_POOL_RVA, POOL_SIZE


STACK = 0x70000000
MAP = 0x71000000
STOP = 0x72000000


def check(condition, message):
    if not condition:
        raise AssertionError(message)


class Machine:
    def __init__(self, data, base, patched):
        self.base = base
        self.cache = base + CACHE_RVA
        self.pool = base + NEW_POOL_RVA if patched else self.cache + 0x75340
        pe = pefile.PE(data=data)
        pe.relocate_image(base)
        mapped = pe.get_memory_mapped_image()
        self.image_size = pe.OPTIONAL_HEADER.SizeOfImage
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(base, self.image_size)
        self.uc.mem_write(base, mapped)
        self.uc.mem_protect(base, pe.OPTIONAL_HEADER.SizeOfHeaders // 4096 * 4096 + 4096, UC_PROT_READ)
        for section in pe.sections:
            size = (max(section.Misc_VirtualSize, section.SizeOfRawData) + 4095) & ~4095
            flags = section.Characteristics
            permissions = ((UC_PROT_READ if flags & 0x40000000 else 0)
                           | (UC_PROT_WRITE if flags & 0x80000000 else 0)
                           | (UC_PROT_EXEC if flags & 0x20000000 else 0))
            self.uc.mem_protect(base + section.VirtualAddress, size, permissions)
        self.uc.mem_map(STACK, 0x10000)
        self.uc.mem_map(MAP, 65536 * 4)
        self.uc.mem_map(STOP, 4096)
        self.uc.reg_write(UC_X86_REG_CR4, self.uc.reg_read(UC_X86_REG_CR4) | 0x600)
        self.put(self.cache + 0x3835c8, MAP)
        self.put(self.cache + 0x3835b4, 7)
        self.put(self.cache + 0x75334, 0)

    def put(self, address, value):
        self.uc.mem_write(address, struct.pack('<I', value))

    def get(self, address):
        return struct.unpack('<I', self.uc.mem_read(address, 4))[0]

    def run(self, start, stop, regs):
        for register, value in regs.items():
            self.uc.reg_write(register, value)
        self.uc.emu_start(self.base + start, stop, count=100)
        check(self.uc.reg_read(UC_X86_REG_EIP) == stop, f'instruction limit at {start:x}')
        return self.uc.reg_read(UC_X86_REG_EAX)

    def allocate(self, vertex):
        self.uc.mem_write(STACK + 0x8000, struct.pack('<II', STOP, vertex))
        return self.run(0x1080, STOP, {
            UC_X86_REG_ESP: STACK + 0x8000, UC_X86_REG_ECX: self.cache,
        })

    def reader(self, which, vertex):
        common = {UC_X86_REG_EBP: STACK + 0x9000}
        if which == 0:
            start, end = 0x5400, 0x541e
            common.update({UC_X86_REG_ECX: self.cache, UC_X86_REG_EDX: vertex, UC_X86_REG_EDI: STACK})
        elif which == 1:
            start, end = 0xdecc, 0xdedb
            common.update({UC_X86_REG_EDX: MAP, UC_X86_REG_EAX: vertex, UC_X86_REG_ESI: self.cache})
        else:
            start, end = (0x1107e, 0x1108d) if which == 2 else (0x112d2, 0x112e1)
            common.update({UC_X86_REG_EAX: MAP, UC_X86_REG_ECX: vertex, UC_X86_REG_EDI: self.cache})
        return self.run(start, self.base + end, common)

    def caller(self, wrinkle, vertex):
        start, end = (0x1129c, 0x112cb) if wrinkle else (0x11048, 0x11077)
        return self.run(start, self.base + end, {
            UC_X86_REG_ESP: STACK + 0x8000, UC_X86_REG_EBP: STACK + 0x9000,
            UC_X86_REG_EDI: self.cache, UC_X86_REG_ECX: vertex,
        })

    def reset(self):
        self.put(STACK + 0x8000, STOP)
        self.run(0x1000, STOP, {UC_X86_REG_ESP: STACK + 0x8000, UC_X86_REG_ECX: self.cache})


def exercise(original, patched, base):
    old, new = Machine(original, base, False), Machine(patched, base, True)
    check(new.uc.mem_read(new.pool, POOL_SIZE) == bytes(POOL_SIZE), 'new pool is not initially zero-filled')
    for begin, end, permissions in new.uc.mem_regions():
        if begin < new.pool + POOL_SIZE and end >= new.pool:
            check(permissions == UC_PROT_READ | UC_PROT_WRITE, 'new pool is not RW/non-executable')
    for count in (0, 1, 9998, 9999):
        for machine in (old, new):
            machine.put(machine.cache + 0x75334, count)
            check(machine.allocate(123) == machine.pool + count * 32, 'pre-limit address')
        check(old.uc.mem_read(MAP + 123 * 4, 4) == new.uc.mem_read(MAP + 123 * 4, 4), 'pre-limit mapping equivalence')

    original_faults = []
    for wrinkle in (False, True):
        old.put(old.cache + 0x75334, 10000)
        check(old.allocate(0) == 0, 'original must return null at capacity')
        try:
            old.caller(wrinkle, 0)
        except UcError as error:
            check(error.errno == UC_ERR_WRITE_UNMAPPED, 'original failed for a reason other than an unmapped write')
            fault_rva = old.uc.reg_read(UC_X86_REG_EIP) - base
            check(fault_rva == (0x112c4 if wrinkle else 0x11070), 'unexpected original fault')
            check(old.uc.reg_read(UC_X86_REG_EAX) == 0, 'original fault not null')
            original_faults.append(hex(fault_rva))
        else:
            raise AssertionError('original null write did not fail')
        for count in (10000, 11854, 65535):
            new.put(new.cache + 0x75334, count)
            check(new.caller(wrinkle, count) == new.pool + count * 32, 'patched caller address')
            check(new.uc.mem_read(new.pool + count * 32, 32) == new.uc.mem_read(base + 0x7e500, 16) * 2, 'caller initialization changed')

    # Sentinel covers original pool and neighboring state; the relocated pool is
    # followed by an unmapped page. Every legal slot uses the address-calculation
    # prefixes of all four readers; this does not emulate entire render routines.
    sentinel_start = new.cache + 0x75338
    sentinel = b'\xa5' * (10000 * 32 + 16)
    new.uc.mem_write(sentinel_start, sentinel)
    new.put(new.cache + 0x75334, 0)
    for index in range(65536):
        # Reverse vertex IDs distinguish source model IDs from cache indices.
        vertex = 65535 - index
        address = new.allocate(vertex)
        check(address == new.pool + index * 32, f'allocator slot {index}')
        check(bytes(new.uc.mem_read(MAP + vertex * 4, 4)) == struct.pack('<HH', 7, index), f'map slot {index}')
        payload = struct.pack('<8I', *([index] * 8))
        new.uc.mem_write(address, payload)
        for reader in range(4):
            check(new.reader(reader, vertex) == address, f'reader {reader} slot {index}')
        check(new.uc.mem_read(address, 32) == payload, f'payload slot {index}')
        if index == 9999:
            check(new.get(new.cache + 0x75334) == 10000, 'mesh accumulation boundary')
        if index == 11854:
            check(new.get(new.cache + 0x75334) == 11855, 'reported workload boundary')
    # Check natural saturation before manually setting any rejection counters.
    # Otherwise a 16-bit counter wrap on the last allocation could go unnoticed.
    check(new.get(new.cache + 0x75334) == 65536, 'natural full-pool counter did not reach 65536')
    expected_pool = b''.join(struct.pack('<8I', *([index] * 8)) for index in range(65536))
    check(new.uc.mem_read(new.pool, POOL_SIZE) == expected_pool, 'later allocations/readers changed earlier payloads')
    previous_map = bytes(new.uc.mem_read(MAP, 65536 * 4))
    check(new.allocate(17) == 0, 'naturally full pool must reject the next allocation')
    check(new.get(new.cache + 0x75334) == 65536, 'natural rejection changed count')
    check(new.uc.mem_read(MAP, 65536 * 4) == previous_map, 'natural rejection changed map')
    check(new.uc.mem_read(new.pool, POOL_SIZE) == expected_pool, 'natural rejection changed payloads')
    check(new.uc.mem_read(sentinel_start, len(sentinel)) == sentinel, 'original pool or adjacent state was overwritten')
    for count in (65536, 65537, 0x7fffffff):
        new.put(new.cache + 0x75334, count)
        previous_map = bytes(new.uc.mem_read(MAP, 65536 * 4))
        check(new.allocate(17) == 0, 'capacity must reject')
        check(new.get(new.cache + 0x75334) == count, 'reject changed count')
        check(new.uc.mem_read(MAP, 65536 * 4) == previous_map, 'reject changed map')
        check(new.uc.mem_read(new.pool, POOL_SIZE) == expected_pool, 'reject changed payloads')
    try:
        new.uc.mem_read(new.pool + POOL_SIZE, 1)
    except UcError as error:
        check(error.errno == UC_ERR_READ_UNMAPPED, 'pool guard check failed for another reason')
    else:
        raise AssertionError('pool guard page unexpectedly mapped')

    for tag in (1, 0xffff, 0):
        new.put(new.cache + 0x3835b4, tag)
        new.reset()
        check(new.get(new.cache + 0x75334) == 0, 'StartModel did not reset count')
        check(new.get(new.cache + 0x3835c8) == 0, 'StartModel did not reset mapping pointer')
        next_tag = (tag + 1) & 0xffff
        check(new.get(new.cache + 0x3835b4) & 0xffff == next_tag, 'StartModel tag behavior')
        new.put(new.cache + 0x3835c8, MAP)
        check(new.caller(False, 0) == new.pool, 'slot zero reuse')
        check(new.uc.mem_read(MAP, 4) == struct.pack('<HH', next_tag, 0), 'reset mapping tag')
    return {'base': hex(base), 'original_null_write_fault_rvas': original_faults,
            'allocated_slots': 65536, 'reader_address_prefixes_per_slot': 4,
            'natural_counter_saturation_and_payload_retention': 'passed',
            'initially_zero_filled_rw_non_executable_pool': 'passed',
            'normal_and_wrinkle_initialization_prefixes': 'passed', 'tag_wrap_and_model_reset': 'passed',
            'original_pool_sentinel_and_end_guard': 'passed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    original = args.original.read_bytes()
    patched, manifest = patch_image(original, experimental_engine_patch=True)
    results = []
    for base in (0x10000000, 0x58000000):
        results.append(exercise(original, patched, base))
        print(f'PASS: actual x86 instructions at base {base:#x}', flush=True)
    report = {'original_sha256': hashlib.sha256(original).hexdigest(),
              'patched_sha256': manifest['output_sha256'], 'emulation': results,
              'scope': 'Offline emulation of selected x86 instruction prefixes, not complete rendering or Windows loader/game validation',
              'game_validated': False}
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

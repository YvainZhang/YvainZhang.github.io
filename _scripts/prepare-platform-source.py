#!/usr/bin/env python3
"""Build the public laboratory source archive from an explicit file allowlist."""
import argparse
import gzip
import hashlib
import io
import json
import pathlib
import re
import tarfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / "linux-link-lab"
OUTPUT = ROOT / "Platform/assets/platform-lab-source.tar.gz"
MANIFEST = ROOT / "_platform_publish/source-manifest.json"
FILES = (
    "src/link.c",
    "platform/Makefile",
    "platform/include/sdk.h", "platform/include/sdk_core.h", "platform/include/sdk_wire.h",
    "platform/core/core.c", "platform/core/wire.c",
    "platform/backends/simulator.c",
    "platform/runtime/linux/runtime.c", "platform/runtime/freertos/runtime.c",
    "platform/runtime/freertos/FreeRTOSConfig.h",
    "platform/tests/core_vectors.c", "platform/tests/runtime_test.c",
    "platform/tests/freertos_test.c", "platform/tests/feature_test.c",
    "platform/examples/demo.c", "platform/examples/benchmark.c", "platform/examples/public-consumer.c",
    "labs/Makefile", "labs/mechanisms.c", "labs/extra.c", "labs/abba-counterexample.c",
    "labs/abi_main.c", "labs/abi_helper.c", "labs/abi_helper.h",
    "kernel-labs/archlab/Makefile", "kernel-labs/archlab/archlab.c",
    "kernel-labs/archlab/archlab_uapi.h", "kernel-labs/archlab/uapi_test.c",
    "kernel-labs/build-vm.sh", "kernel-labs/run-vm.py",
    "scripts/deps/Dockerfile", "scripts/deps/Dockerfile.sanitizers", "scripts/deps/fetch-freertos.sh",
    "scripts/smoke.sh", "scripts/network-integration.sh", "scripts/drop-integration.sh",
    "scripts/raw-frame-test.py", "scripts/benchmark-report.py",
    "scripts/mutation-check.py", "scripts/check-counterexample.py",
)

README = """# Platform laboratory source

Linux mechanisms and a bounded asynchronous C SDK: descriptor lifetime, events,
queues, request completion, stop/recovery, TAP networking, and a FreeRTOS runtime
comparison. The public tutorial is at https://xidianedu.cc/tech/platform/.

## Environments and isolation

The default user experiments run in a disposable Linux container. GCC, make,
Python 3, binutils and Linux headers are required. Run from this archive's root.
The Alpine tool image is pinned by digest; build it on the host:

```sh
docker build -f scripts/deps/Dockerfile -t platform-arch-lab:alpine3.22 scripts/deps
./scripts/run-container.sh user
./scripts/run-container.sh startup
./scripts/run-container.sh shell
```

The shell opens at /work inside an isolated container. Exit closes it. Each
suite also creates a disposable container with networking disabled and only
this directory mounted. No container socket or host network is mounted.
The `user` suite runs core/Linux, feature-disabled, public consumer, mechanism,
deadline mutation and bounded ABBA counterexample checks. It does not download
or run FreeRTOS. `startup` adds deterministic startup-order and thread-create
failure injection to the Linux runtime test; these hooks are absent in normal
builds. Both test binaries also compare direct same-fd dup2 with the special
posix_spawn same-fd action and check fixed-fd backend roundtrips.

## One mechanism at a time

Inside the tool container:

```sh
make -C labs all
./build/labs/mechanisms --list
./build/labs/mechanisms fd
./build/labs/mechanisms epoll
./build/labs/mechanisms memory
make test
make startup-test
make -C platform libraries
make -C labs test
cat build/labs/elf-header.txt
make check-docs
make package
```

Selection names: fd, rollback, save, ipc, blocking, stream, epoll, partial-write,
queue, atomic, memory, extra. Each checks its own assertions and descriptor
baseline; `all` runs the full set. Page-fault counts depend on the kernel.
Output lines describe assertion results, not general real-time guarantees.
`make package` regenerates a source archive from SOURCEFILES.json's file list,
excluding build output and downloaded dependencies.

## FreeRTOS and optional checks

FreeRTOS-Kernel V11.1.0 is downloaded separately and checked against the pinned
SHA256 in scripts/deps/fetch-freertos.sh. Fetch in a temporary container with
ordinary outbound networking, then run the test without networking:

```sh
./scripts/run-container.sh deps
./scripts/run-container.sh freertos
docker build -f scripts/deps/Dockerfile.sanitizers -t platform-arch-sanitizers:bookworm scripts/deps
./scripts/run-container.sh sanitize
./scripts/run-container.sh tsan
./scripts/run-container.sh benchmark
```

The FreeRTOS POSIX port exercises the actual scheduler/tasks/queues on Linux;
it does not establish MCU interrupt latency or hardware timing. The sanitizer
image is separate. A TSan address-layout incompatibility is recorded as SKIP,
not PASS. The TSan container alone uses seccomp=unconfined when required by
the detector. Normal suites retain the default profile. Benchmark generates
five rounds each for request limits 4 and 16, followed by summary.json.
Results and exact command exit codes are saved under build/verification.
`./scripts/run-container.sh reproduction` checks the public Markdown targets,
source repackaging and the fd/epoll/memory single-experiment commands.

## Networking and kernel

`./scripts/run-container.sh network` adds NET_ADMIN and SYS_ADMIN only to its
disposable container for private network namespaces and TAP. It verifies local
delivery, captured ARP/ICMP, delay and selected EtherType dropping.

The provided VM builder currently targets ARM64 Alpine/musl. Use an ARM64
Docker host/image for `./scripts/run-container.sh kernel-build`. The script
refuses a mismatched userspace architecture; it builds modules but never loads
them in the host/container kernel. Run `python3 kernel-labs/run-vm.py` on a
host with qemu-system-aarch64; the guest has no NIC and uses TCG. Serial output
is saved at build/vm/serial.log. Other architectures require a matched kernel,
module toolchain, initramfs loader and QEMU machine; merely changing cc is
insufficient. No target board, MCU timing, KASAN or lockdep result is implied.

## API boundary and licensing

create/start/destroy are serialized by the application. submit/cancel/recover/
post_stop/snapshot may have multiple producers. The owner exclusively mutates
core; callbacks run without the internal mutex. Synchronous stop, stop_wait
and destroy from an owner callback return SDK_ECONTEXT; post_stop is allowed.
Payload is copied on submit; callback payload expires at callback return.
A successful enqueue produces ACCEPT or REJECT; only accepted requests owe a
single TERMINAL. A timed-out stop leaves the object valid for a later wait.
destroy requires every external API caller to have finished.

Self-authored code is MIT (LICENSE). archlab.c declares GPL-2.0-only and must
retain that module license. FreeRTOS is a separate upstream MIT dependency;
its original license remains with the fetched files. No prebuilt libraries or
third-party source are included; compile for the target architecture/libc.
SOURCEFILES.json lists every public file and its SHA256.
"""

MAKEFILE = """CC ?= cc
CFLAGS ?= -O2 -g -std=c11 -Wall -Wextra -Werror
STARTUP_BUILD ?= build/startup
.PHONY: all link test startup-test freertos-test integration kernel-build kernel-test verify check-docs package
all: link
	$(MAKE) -C platform all
	$(MAKE) -C labs all
build/link-lab: src/link.c
	mkdir -p build
	$(CC) $(CFLAGS) $< -o $@
link: build/link-lab
test:
	$(MAKE) -C platform test feature-test public-test
	$(MAKE) -C labs test
	python3 scripts/mutation-check.py
	python3 scripts/check-counterexample.py
startup-test:
	$(MAKE) -C platform BUILD=../$(STARTUP_BUILD) all
	$(CC) $(CFLAGS) -DSDK_TEST_STARTUP -Iplatform/include platform/core/core.c platform/core/wire.c platform/runtime/linux/runtime.c platform/tests/runtime_test.c -pthread -o $(STARTUP_BUILD)/startup-test
	timeout 30 ./$(STARTUP_BUILD)/startup-test $(abspath $(STARTUP_BUILD)/device-sim)
freertos-test:
	$(MAKE) -C platform freertos-test
integration: link
	./scripts/network-integration.sh
	./scripts/drop-integration.sh
kernel-build:
	./kernel-labs/build-vm.sh
kernel-test:
	python3 kernel-labs/run-vm.py
check-docs:
	python3 scripts/check-docs.py
verify: test startup-test check-docs
package:
	python3 scripts/package.py
"""

RUNNER = """#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
suite=${1:-user}
image=platform-arch-lab:alpine3.22
case "$suite" in
 shell) exec docker run --rm -it --network none -v "$root:/work" -w /work "$image" sh ;;
 deps) exec docker run --rm -v "$root:/work" -w /work "$image" sh scripts/deps/fetch-freertos.sh ;;
 user|startup|freertos|benchmark|kernel-build|reproduction) exec docker run --rm --network none -v "$root:/work" -w /work "$image" python3 scripts/verify.py --suite "$suite" ;;
 network) exec docker run --rm --network none --cap-add NET_ADMIN --cap-add SYS_ADMIN --security-opt apparmor=unconfined -v "$root:/work" -w /work "$image" sh -c 'mkdir -p /dev/net; test -c /dev/net/tun || mknod /dev/net/tun c 10 200; python3 scripts/verify.py --suite network' ;;
 sanitize) exec docker run --rm --network none -v "$root:/work" -w /work platform-arch-sanitizers:bookworm python3 scripts/verify.py --suite sanitize ;;
 tsan) exec docker run --rm --network none --security-opt seccomp=unconfined -v "$root:/work" -w /work platform-arch-sanitizers:bookworm python3 scripts/verify.py --suite tsan ;;
 *) echo 'usage: run-container.sh shell|deps|user|startup|freertos|network|benchmark|sanitize|tsan|kernel-build|reproduction' >&2; exit 2 ;;
esac
"""

VERIFY = """#!/usr/bin/env python3
\"\"\"Record command results and current source hashes for public experiments.\"\"\"
import argparse, hashlib, json, pathlib, platform, subprocess, time
root = pathlib.Path(__file__).resolve().parents[1]
suites = {
 'user': [('make', 'test')],
 'startup': [('make', 'startup-test')],
 'reproduction': [('make', '-C', 'labs', 'all'), ('make', 'check-docs', 'package'), ('./build/labs/mechanisms', '--list'),
                  ('./build/labs/mechanisms', 'fd'), ('./build/labs/mechanisms', 'epoll'),
                  ('./build/labs/mechanisms', 'memory')],
 'freertos': [('make', 'freertos-test')],
 'network': [('make', 'integration')],
 'benchmark': [('make', '-C', 'platform', 'benchmark'), ('python3', 'scripts/benchmark-report.py')],
 'sanitize': [('make', '-C', 'platform', 'sanitize'), ('make', '-C', 'labs', 'sanitize'),
              ('make', 'STARTUP_BUILD=build/startup-asan', 'CFLAGS=-O1 -g -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer', 'startup-test')],
 'tsan': [('make', '-C', 'platform', 'BUILD=../build/tsan', 'CFLAGS=-O1 -g -std=c11 -Wall -Wextra -Werror -fsanitize=thread', 'test'),
          ('make', 'STARTUP_BUILD=build/startup-tsan', 'CFLAGS=-O1 -g -std=c11 -Wall -Wextra -Werror -fsanitize=thread', 'startup-test')],
 'kernel-build': [('make', 'kernel-build')],
}
parser = argparse.ArgumentParser()
parser.add_argument('--suite', choices=suites, default='user')
args = parser.parse_args()
names = json.loads((root/'SOURCEFILES.json').read_text())['files']
hashes = {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}
identity = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:12]
run = root/'build/verification'/(time.strftime('%Y%m%d-%H%M%S')+'-'+identity+'-'+args.suite)
run.mkdir(parents=True, exist_ok=False)
record = {'suite': args.suite, 'source_id': identity, 'source_hashes': hashes,
          'environment': platform.uname()._asdict(), 'steps': []}
record['tool_versions'] = {}
for name, command in [('cc', ['cc', '--version']), ('make', ['make', '--version']),
                      ('python', ['python3', '--version']), ('libc', ['ldd', '--version'])]:
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
    record['tool_versions'][name] = {'exit_code': result.returncode,
        'lines': result.stdout.decode(errors='replace').splitlines()[:3]}
for i, command in enumerate(suites[args.suite]):
    try:
        result = subprocess.run(command, cwd=root, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=300 if args.suite=='kernel-build' else 180)
        output, code = result.stdout, result.returncode
    except subprocess.TimeoutExpired as exc:
        output, code = exc.stdout or b'', 124
    log = f'{i:02d}.log'
    (run/log).write_bytes(output)
    skip = args.suite=='tsan' and b'ThreadSanitizer: unexpected memory mapping' in output
    state = 'SKIP' if skip else 'PASS' if code==0 else 'FAIL'
    record['steps'].append({'command': list(command), 'exit_code': code, 'status': state, 'log': log})
    print(json.dumps(record['steps'][-1]), flush=True)
    if state=='FAIL':
        print(output[-7000:].decode(errors='replace'), flush=True)
        break
record['result'] = 'FAIL' if any(s['status']=='FAIL' for s in record['steps']) else 'SKIP' if any(s['status']=='SKIP' for s in record['steps']) else 'PASS'
(run/'manifest.json').write_text(json.dumps(record, indent=2)+'\\n')
print(str(run), flush=True)
raise SystemExit(1 if record['result']=='FAIL' else 0)
"""

CHECK_DOCS = """#!/usr/bin/env python3
import pathlib, re, urllib.parse
root = pathlib.Path(__file__).resolve().parents[1]
errors = []
for p in sorted(root.glob('*.md')):
    for target in re.findall(r'!?\\[[^\\]]*\\]\\(([^)]+)\\)', p.read_text()):
        target = target.split('#')[0]
        if not target or urllib.parse.urlparse(target).scheme:
            continue
        if not (p.parent/urllib.parse.unquote(target)).exists():
            errors.append(f'{p.name}: {target}')
if errors:
    raise SystemExit('\\n'.join(errors))
print('Public archive Markdown local targets: PASS')
"""

PACKAGE = """#!/usr/bin/env python3
import gzip, hashlib, io, json, pathlib, tarfile
root = pathlib.Path(__file__).resolve().parents[1]
names = json.loads((root/'SOURCEFILES.json').read_text())['files']
files = {name: (root/name).read_bytes() for name in names}
files['SOURCEFILES.json'] = (json.dumps({'files': {n: hashlib.sha256(b).hexdigest() for n,b in sorted(files.items())}}, indent=2)+'\\n').encode()
output = root/'build/release/platform-lab-source.tar.gz'
output.parent.mkdir(parents=True, exist_ok=True)
with output.open('wb') as stream, gzip.GzipFile(filename='', fileobj=stream, mode='wb', mtime=0) as gz, tarfile.open(fileobj=gz, mode='w', format=tarfile.PAX_FORMAT) as tar:
    for name, data in sorted(files.items()):
        info = tarfile.TarInfo('platform-lab-source/'+name)
        info.size, info.mtime, info.mode = len(data), 0, 0o755 if name.endswith('.sh') else 0o644
        tar.addfile(info, io.BytesIO(data))
print(str(output))
print('SHA256 '+hashlib.sha256(output.read_bytes()).hexdigest())
"""


def prepare(work):
    payload = {name: (work / name).read_bytes() for name in FILES}
    # Keep the MIT text while writing an explicit public licensing boundary.
    mit = (work / "LICENSE").read_text().split("MIT License\n", 1)[1]
    payload["LICENSE"] = ("Self-authored code is MIT. kernel-labs/archlab/archlab.c is GPL-2.0-only.\n"
        "FreeRTOS is a separate upstream dependency; retain its original MIT license.\n\nMIT License\n" + mit).encode()
    payload.update({"README.md": README.encode(), "Makefile": MAKEFILE.encode(),
        "scripts/run-container.sh": RUNNER.encode(), "scripts/verify.py": VERIFY.encode(),
        "scripts/check-docs.py": CHECK_DOCS.encode(), "scripts/package.py": PACKAGE.encode()})
    vm = payload["kernel-labs/build-vm.sh"].decode()
    if "ARM64 Alpine userspace required" not in vm:
        vm = vm.replace('cd "$(dirname "$0")/.."\n', 'cd "$(dirname "$0")/.."\n'
            'test "$(uname -m)" = aarch64 || { echo "ARM64 Alpine userspace required" >&2; exit 2; }\n'
            'test -f /lib/ld-musl-aarch64.so.1 || { echo "ARM64 musl loader missing" >&2; exit 2; }\n')
    payload["kernel-labs/build-vm.sh"] = vm.encode()
    forbidden = re.compile(r"面试|求职|复习|个人评分|能力缺口|训练指令|interview|career", re.I)
    for name, data in payload.items():
        if forbidden.search(name) or forbidden.search(data.decode()):
            raise ValueError("Internal-purpose wording in public payload: " + name)
    public_hashes = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(payload.items())}
    payload["SOURCEFILES.json"] = (json.dumps({"files": public_hashes}, indent=2) + "\n").encode()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("wb") as stream, gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0) as gz, tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for name, data in sorted(payload.items()):
            info = tarfile.TarInfo("platform-lab-source/" + name)
            info.size, info.mtime = len(data), 0
            info.mode = 0o755 if name.endswith(".sh") else 0o644
            tar.addfile(info, io.BytesIO(data))
    manifest = {"schema": 1, "archive": "Platform/assets/platform-lab-source.tar.gz",
        "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "source_allowlist": {name: hashlib.sha256((work/name).read_bytes()).hexdigest() for name in FILES},
        "public_files": public_hashes,
        "generated_files": [name for name in public_hashes if name not in FILES],
        "edited_copies": ["kernel-labs/build-vm.sh"],
        "licensing": {"self_authored": "MIT", "kernel_module": "GPL-2.0-only", "freertos": "separate upstream MIT dependency"}}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"archive": str(OUTPUT.relative_to(ROOT)), "sha256": manifest["sha256"], "files": len(payload)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=pathlib.Path, default=WORK,
        help="Source workspace or the top-level directory of an extracted public archive")
    args = parser.parse_args()
    prepare(args.source_dir)

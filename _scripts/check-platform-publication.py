#!/usr/bin/env python3
"""Validate the reviewed platform publication without accessing private sources."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import statistics
import tarfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'Platform'
MANIFEST = ROOT / '_platform_publish/manifest.json'
PAGES = {
    'README.md', 'guide/environment.md', 'reference/source.md',
    'reference/api.md', 'reference/verification.md',
    'mechanisms/01-c-abi.md', 'mechanisms/02-build-elf.md',
    'mechanisms/03-fd-lifetime.md', 'mechanisms/04-io-persistence.md',
    'mechanisms/05-process-ipc.md', 'mechanisms/06-events-time.md',
    'mechanisms/07-concurrency-ownership.md', 'mechanisms/08-memory-performance.md',
    'mechanisms/09-network-tap.md', 'mechanisms/10-kernel-lifetime.md',
    'design/01-boot-hardware.md', 'design/02-sdk-contract.md',
    'design/03-linux-freertos.md', 'design/04-reliability-delivery.md',
    'design/05-platform-selection.md', 'design/06-resource-budget.md',
    'design/07-complexity-evolution.md', 'design/08-lifecycle-review.md',
    'cases/01-stop-drain.md', 'cases/02-inflight-budget.md',
    'cases/03-cross-runtime-recovery.md', 'cases/04-exec-fd.md',
    'design/09-capacity-admission.md', 'design/10-failure-recovery.md',
    'design/11-contract-evolution.md',
}
ASSETS = {
    'assets/platform-lab-source.tar.gz',
    'assets/verification-2026-10-04.json',
    'assets/benchmark/summary.json', 'assets/benchmark/runs.json',
    'javascripts/vendor/mermaid-10.4.0.min.js', 'javascripts/platform-diagrams.js',
    *(f'assets/benchmark/limit-{limit}-round-{round_id}.csv'
      for limit in (4, 16) for round_id in range(1, 6)),
}
LINUX_PAGES = {
    'README.md', 'guide/environment.md', 'runtime/01-async-sdk.md',
    'hardware/01-boot-hardware.md',
    *(name for name in PAGES if name.startswith('mechanisms/')),
    'cases/01-stop-drain.md', 'cases/02-inflight-budget.md', 'cases/04-exec-fd.md',
    'advanced/01-reactor-scheduling.md', 'advanced/02-tail-latency.md',
    'advanced/03-resource-isolation.md', 'advanced/04-driver-quiescence.md',
}
RTOS_PAGES = {
    'README.md', '01-environment.md', '02-queue-owner.md', '03-recovery-stop.md',
}
SITE_ROOTS = {
    'linux': ROOT / 'Linux', 'platform': DOCS, 'rtos': ROOT / 'RTOS',
}
SHARED_FILES = {
    '_collection_theme/main.html', 'assets/collections/reading.css',
    'assets/collections/reading-controls.js',
    '_linux_publish/mkdocs.yml', '_platform_publish/mkdocs.yml',
}
FORBIDDEN = re.compile(
    r'面试|求职|个人能力验收|能力缺口|复习强化|学习问答|Hermes|'
    r'linux-link-lab/|(?:assessment|roadmap)/|/Users/'
)


def check_text(name, body):
    match = FORBIDDEN.search(body)
    if match:
        raise ValueError(f'{name}: internal material marker {match.group(0)!r}')


def validate():
    shared_files = {name: ROOT / name for name in SHARED_FILES}
    for name, path in shared_files.items():
        check_text(name, path.read_text(encoding='utf-8'))
    files = {str(p.relative_to(DOCS)): p for p in DOCS.rglob('*') if p.is_file()}
    expected = PAGES | ASSETS
    if set(files) != expected:
        raise ValueError(f'Publication inventory differs: missing={sorted(expected-set(files))}, extra={sorted(set(files)-expected)}')
    reviewed_pages = {f'Platform/{name}': files[name] for name in PAGES}
    for directory, pages in [('Linux', LINUX_PAGES), ('RTOS/Practice', RTOS_PAGES)]:
        collection = ROOT / directory
        published = {str(p.relative_to(collection)): p for p in collection.rglob('*') if p.is_file()}
        if set(published) != pages:
            raise ValueError(f'{directory}: publication inventory differs')
        reviewed_pages.update({f'{directory}/{name}': p for name, p in published.items()})
    for name, path in sorted(reviewed_pages.items()):
        body = path.read_text(encoding='utf-8')
        check_text(name, body)
        if len(re.findall(r'^```', body, re.M)) % 2:
            raise ValueError(f'{name}: unmatched code fence')
        if any(line.rstrip() != line for line in body.splitlines()):
            raise ValueError(f'{name}: trailing whitespace')
        # Ignore illustrative Markdown inside code blocks.
        prose = re.sub(r'^```.*?^```\s*$', '', body, flags=re.M | re.S)
        for link in re.findall(r'\]\(([^)]+)\)', prose):
            target = urlsplit(link.strip('<>'))
            if not target.path:
                continue
            # Check cross-collection links against repository sources, without network access.
            if target.netloc == 'xidianedu.cc' and target.path.startswith('/tech/'):
                parts = unquote(target.path).strip('/').split('/')
                if len(parts) > 1 and parts[1] in SITE_ROOTS:
                    linked = SITE_ROOTS[parts[1]].joinpath(*parts[2:])
                    if target.path.endswith('/'):
                        candidates = [linked.with_suffix('.md'), linked / 'README.md']
                        if len(parts) == 2:
                            candidates = [linked / 'README.md']
                    else:
                        candidates = [linked]
                    if not any(p.is_file() for p in candidates):
                        raise ValueError(f'{name}: missing site resource {link}')
                continue
            if target.scheme or target.netloc:
                continue
            linked = (path.parent / unquote(target.path)).resolve()
            collection_root = ROOT / name.split('/')[0]
            if not linked.is_relative_to(collection_root.resolve()) or not linked.is_file():
                raise ValueError(f'{name}: missing or external local resource {link}')
    for name in ASSETS - {'assets/platform-lab-source.tar.gz'}:
        check_text(name, files[name].read_text(encoding='utf-8'))

    archive = files['assets/platform-lab-source.tar.gz']
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        for member in members:
            parts = Path(member.name).parts
            if not parts or parts[0] != 'platform-lab-source' or '..' in parts:
                raise ValueError(f'Unsafe archive path: {member.name}')
            if member.issym() or member.islnk() or not (member.isdir() or member.isfile()):
                raise ValueError(f'Unsupported archive member: {member.name}')
            if {'docs', 'evidence', 'build', 'third_party', '.git'} & set(parts):
                raise ValueError(f'Non-public archive member: {member.name}')
            if member.isfile():
                body = tar.extractfile(member).read()
                check_text(member.name, body.decode('utf-8'))
        sums_file = tar.extractfile('platform-lab-source/SOURCEFILES.json')
        checksums = json.load(sums_file)['files']
        actual = {m.name.removeprefix('platform-lab-source/'): m
                  for m in members if m.isfile() and m.name != 'platform-lab-source/SOURCEFILES.json'}
        if set(checksums) != set(actual):
            raise ValueError('Source archive checksum inventory differs')
        for name, digest in checksums.items():
            if hashlib.sha256(tar.extractfile(actual[name]).read()).hexdigest() != digest:
                raise ValueError(f'Source archive checksum differs: {name}')

    summaries = json.loads(files['assets/benchmark/summary.json'].read_text())
    runs = json.loads(files['assets/benchmark/runs.json'].read_text())
    wanted = {(limit, round_id) for limit in (4, 16) for round_id in range(1, 6)}
    if {(r['limit'], r['round']) for r in runs} != wanted or len(runs) != 10 or len(summaries) != 10:
        raise ValueError('Benchmark round inventory differs')
    for row in summaries:
        name = f"assets/benchmark/{row['round']}.csv"
        with files[name].open(newline='') as stream:
            samples = list(csv.DictReader(stream))
        completed = sorted(int(r['latency_ns']) / 1e6 for r in samples if r['result'] == 'completed')
        if len(samples) != row['samples'] or len(samples) - len(completed) != row['failures']:
            raise ValueError(f'{name}: benchmark counts differ')
        if [statistics.median(completed), completed[int(.95*(len(completed)-1))], completed[int(.99*(len(completed)-1))]] != [row['median_ms'], row['p95_ms'], row['p99_ms']]:
            raise ValueError(f'{name}: benchmark summary differs')
    for row in runs:
        measured = row['completed'] * 1e9 / row['elapsed_ns']
        if abs(measured-row['requests_per_s']) > .011:
            raise ValueError('Benchmark throughput differs from elapsed duration')
    verification = json.loads(files['assets/verification-2026-10-04.json'].read_text())
    archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    # The producer records the exact download digest in its public verification.
    if archive_hash not in json.dumps(verification):
        raise ValueError('Verification does not identify the public source archive')
    return {
        'schema': 2,
        'site_urls': [f'https://xidianedu.cc/tech/{name}/' for name in SITE_ROOTS],
        'historical_benchmark_dates': '2026-10-02/03',
        'files': {name: hashlib.sha256(path.read_bytes()).hexdigest()
                  for name, path in sorted({**reviewed_pages, **shared_files,
                      **{f'Platform/{name}': files[name] for name in ASSETS}}.items())},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-manifest', action='store_true',
                        help='Refresh the reviewed publication hashes after editing')
    args = parser.parse_args()
    try:
        current = validate()
        if args.write_manifest:
            MANIFEST.write_text(json.dumps(current, ensure_ascii=False, indent=2)+'\n')
        elif not MANIFEST.is_file() or json.loads(MANIFEST.read_text()) != current:
            raise ValueError('Reviewed publication manifest is missing or stale')
    except (ValueError, KeyError, OSError, UnicodeError, tarfile.TarError) as error:
        raise SystemExit(f'Platform publication FAILED: {error}')
    print(f'Publication PASS: {len(PAGES)+len(LINUX_PAGES)+len(RTOS_PAGES)} pages across Linux, RTOS and platform design, {len(ASSETS)} assets, source checksums and benchmark calculations')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Certify broken seeds, authentic reported logs and passing reference repairs."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from verifier.check_debug_behavior import evaluate


def failure_log(contract: dict, results: dict) -> str:
    """Format actual public-call evidence, with independently specified expectations."""
    lines = ['Original failure capture; public calls in each scenario share one fresh process.']
    for result in results['results']:
        lines.append(f"\nScenario: {result['name']}")
        for item in result.get('observations', []):
            lines.append(f"call: {contract['entrypoint']}({json.dumps(item['args'])})")
            lines.append(f"got: {json.dumps(item['actual'], sort_keys=True)}")
            lines.append(f"want: {json.dumps(item['expected'], sort_keys=True)}")
        if result.get('error'):
            raise ValueError(f"Original capture failed to execute: {result['error']}")
    return '\n'.join(lines) + '\n'


def certify(root: Path, refresh: bool = False, names: set[str] | None = None) -> list[dict]:
    """Run and compare every fixture; originals must fail and reference repairs pass."""
    evidence = []
    for cases in sorted((root / 'debug-cases').glob('*.json')):
        name = cases.stem
        if names is not None and name not in names:
            continue
        contract = json.loads(cases.read_text())
        seed = root / 'seeds' / name
        original = evaluate(seed, cases)
        assert original['reward'] == 0.0, f'{name}: seed unexpectedly passes'
        reported = [sequence for sequence in contract['sequences'] if sequence.get('reported')]
        assert reported, f'{name}: no reported failure scenarios'
        with tempfile.TemporaryDirectory(prefix='debug-fixture-') as temporary:
            scratch = Path(temporary)
            reported_cases = scratch / 'reported.json'
            reported_cases.write_text(json.dumps({**contract, 'sequences': reported}))
            capture = evaluate(seed, reported_cases)
            assert all(not result['pass'] for result in capture['results']), f'{name}: reported failure no longer fails'
            text = failure_log(contract, capture)
            log = seed / 'log' / 'failure.log'
            if refresh:
                log.parent.mkdir(exist_ok=True)
                log.write_text(text)
            assert log.read_text() == text, f'{name}: original log does not match executed seed'
            oracle = scratch / 'reference'
            oracle.mkdir()
            for item in seed.iterdir():
                if item.is_file():
                    shutil.copy2(item, oracle / item.name)
            shutil.copy2(root / 'oracles' / f'{name}.py', oracle / contract['artifact'])
            fixed = evaluate(oracle, cases)
            repeated = evaluate(oracle, cases)
            assert fixed['reward'] == repeated['reward'] == 1.0, f'{name}: reference repair fails its contract'
        evidence.append({'task': name, 'seed_reward': original['reward'], 'reference_reward': fixed['reward'],
                         'reported_failures': len(reported), 'public_assertions': sum(len(s['steps']) for s in contract['sequences'])})
    assert evidence, 'No debug fixtures available'
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--refresh-logs', action='store_true', help='explicitly replace captures from current broken seeds')
    args = parser.parse_args()
    print(json.dumps(certify(args.root.resolve(), args.refresh_logs), indent=2))


if __name__ == '__main__':
    main()

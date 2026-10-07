#!/usr/bin/env python3
"""Run verifier-owned public behavior sequences in fresh, bounded subprocesses."""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path


def run_sequence(repo: Path, contract: dict, sequence: dict) -> dict:
    """Load the delivered module once and observe a sequence of public calls."""
    observations = []
    transcript = io.StringIO()
    try:
        with contextlib.redirect_stdout(transcript), contextlib.redirect_stderr(transcript):
            sys.path.insert(0, str(repo))
            spec = importlib.util.spec_from_file_location('submission', repo / contract['artifact'])
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            entrypoint = getattr(module, contract['entrypoint'])
            for step in sequence['steps']:
                actual = {}
                try:
                    actual['result'] = entrypoint(*step.get('args', []), **step.get('kwargs', {}))
                except Exception as exc:
                    actual['raises'] = type(exc).__name__
                expected = {'raises': step['raises']} if 'raises' in step else {'result': step['expected']}
                observations.append({'args': step.get('args', []), 'expected': expected,
                                     'actual': actual, 'pass': actual == expected})
        return {'name': sequence['name'], 'observations': observations,
                'pass': bool(observations) and all(item['pass'] for item in observations),
                'transcript': transcript.getvalue()[-12000:]}
    except Exception as exc:
        return {'name': sequence['name'], 'pass': False, 'observations': observations,
                'error': f'{type(exc).__name__}: {exc}', 'transcript': transcript.getvalue()[-12000:]}


def evaluate(repo: Path, cases: Path) -> dict:
    """Execute every immutable sequence without sharing mutable module state."""
    contract = json.loads(cases.read_text())
    sequences = contract['sequences']
    if not sequences or any(not sequence.get('steps') for sequence in sequences):
        raise ValueError('Verifier contract requires nonempty public call sequences')
    results = []
    for sequence in sequences:
        request = {'contract': contract, 'sequence': sequence}
        try:
            process = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), '--repo', str(repo), '--sequence'],
                input=json.dumps(request), text=True, capture_output=True, timeout=10, cwd=repo,
            )
            result = json.loads(process.stdout) if process.returncode == 0 else {
                'name': sequence['name'], 'pass': False,
                'error': f'child exit {process.returncode}: {process.stderr[-2000:]}',
            }
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            result = {'name': sequence['name'], 'pass': False, 'error': type(exc).__name__}
        results.append(result)
    return {'reward': float(all(result['pass'] for result in results)),
            'executed_sequences': len(results), 'results': results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--cases', type=Path, default=Path('/tests/debug-cases.json'))
    parser.add_argument('--output', type=Path, required=False)
    parser.add_argument('--sequence', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.sequence:
        request = json.load(sys.stdin)
        print(json.dumps(run_sequence(args.repo.resolve(), request['contract'], request['sequence'])))
        return 0
    try:
        result = evaluate(args.repo.resolve(), args.cases)
    except (OSError, ValueError, KeyError) as exc:
        result = {'reward': 0.0, 'error': 'missing_or_invalid_debug_evidence', 'reason': str(exc)}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({'reward': result['reward']}) + '\n')
        args.output.with_name(args.output.stem + '-details.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['reward'] == 1.0 else 1


if __name__ == '__main__':
    raise SystemExit(main())

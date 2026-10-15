---
name: srp
description: >-
  v0.0.61 — Parse raw input once; operations call validators for converted values
  and share equivalent rules, calculations and classifications.
---

# Parsing, validation, operations and dispatch

From the first agent-authored working slice, preserve the public signature and
use these owners. A repair of a supplied mixed entrypoint extracts its current
parsing and core operation in that first repair, not a later capability.

| Owner | Responsibility |
| --- | --- |
| Parser | Raw syntax, normalization, operand shape and token conversion; no acceptance checks on converted numbers. |
| Domain validators | Every requested value/resource acceptance predicate and rejection, including empty-state checks; operations call this owner from its first use, even with one caller. |
| Operations | Separate callables that call applicable validators, calculate results and change state. |
| Public dispatch | Parse once, route converted arguments unchanged, return/format results. |

Apply only the request's current acceptance rules. After conversion, sign,
finiteness and integrality checks belong in validators called by operations.
Never repeat them in parsing, even when the operation already calls a validator.

Implement only the current capability. Future commands/selectors wait for their
own cycle. A validator called by one current operation owns a current rule; it
is not speculative scaffolding. Do not invent domain restrictions.

## Parse completely before routing

One outer parser receives raw input and returns the selector and fully converted
arguments. It owns strip/split/slicing/regex/text normalization, selector
classification, operand counts before indexing and conversion. Validate every
current form, including zero-operand forms; exact matching is valid. Smaller form
parsers may compose inside this boundary, including receiving raw text there.
Dispatch calls only the outer parser, never selects a form parser from raw input.

Prefer `(selector, arguments)` from the first slice. Arguments-only parsing is
valid for one operation; a validated selector suffices for a zero-operand form.
When adding forms, update that return and its caller together. Return normalized
text and numeric values, never numeric strings or unchecked operand lists.

Builtin conversion errors and lexical numeric grammar belong to parsing.
After `float()` or `Decimal()` succeeds, rejection through `math.isfinite()`,
`value.is_finite()` or `value.is_integer()` belongs to a called domain validator,
including the first whole-number capability. Raising a conversion exception
after one of these predicates still rejects a converted value; it does not make
the rule lexical. NaN and infinity can convert successfully. Magnitude,
zero-divisor and resource acceptance likewise belong to called validators.
Builtin `int(token)` rejecting lexical syntax stays in parsing. Representation
normalization is permitted only when it preserves acceptance and mathematical value.

## Operations call rule owners

Create and call a validator when a current operation first needs an acceptance
rule, including one used only in a conditional branch. The operation chooses
whether a rule applies; the validator owns its predicate and rejection. Validate
before calculating/mutating. Operations receive converted arguments; they never
call token-conversion helpers.

This includes index bounds, resource relationships and conditional capacity checks.
An inline `if ...: raise` in an operation still needs its called validator, even
with one caller. The operation may select a mode, then call the validator.

For example, a current command accepting finite whole-valued input can use:

```python
import math


def parse_command(command):
    """Parse the current half command into a selector and converted argument.
    Parameters: command - raw command text.
    Returns: the selector and converted numeric argument tuple.
    """
    print(f"command={command}")
    parts = command.strip().split()
    if len(parts) != 2 or parts[0] != "half":
        raise ValueError("invalid command shape")
    result = ("half", (float(parts[1]),))
    print(result)
    return result


def require_finite(value):
    """Accept the finite value required by the current operation.
    Parameters: value - already converted number.
    Returns: the accepted finite number.
    """
    print(f"value={value}")
    if not math.isfinite(value):
        raise ValueError("nonfinite value")
    print(value)
    return value


def require_integral(value):
    """Accept a finite whole-valued number.
    Parameters: value - already converted number.
    Returns: the accepted finite whole-valued number.
    """
    print(f"value={value}")
    value = require_finite(value)
    if not value.is_integer():
        raise ValueError("fractional value")
    print(value)
    return value


def calculate_half(value):
    """Calculate half an accepted whole-valued number.
    Parameters: value - already converted number.
    Returns: half the accepted value.
    """
    print(f"value={value}")
    value = require_integral(value)
    result = value / 2
    print(result)
    return result


def run_command(command):
    """Parse and route the current half command.
    Parameters: command - raw command text.
    Returns: the operation's numeric result.
    """
    print(f"command={command}")
    selector, arguments = parse_command(command)
    result = calculate_half(*arguments)
    print(result)
    return result
```

Apply the same boundary to Decimal. Widening acceptance changes the validator
and any necessary parser representation together: drop integrality when fractions
become accepted; retain finiteness only if the current contract requires it.

Before adding another operation, read related saved owners and report their
rules and current callers. Derive the new operation's prerequisites from its
contract; sharing storage or operand counts does not inherit another operation's
acceptance rules. Returning a value does not make a mutation a read-only query.
Reuse the same called validator when both operations require equivalent rules;
extract every earlier inline copy in that edit, including conditional guards and
shared subconditions. Positive-and-finite remains shared when another operation
also requires integrality. Different resource identities, names, units, error
messages, comparison direction or read/write callers do not make equivalent
acceptance different. Validate
each resource in a multi-resource operation. An unused helper shares nothing.

For an availability rule, both operations call `require_available(available, requested)`:

```python
def require_available(available, requested):
    """Accept a request within the currently available quantity.
    Parameters: available - quantity the resource can supply; requested - quantity to consume.
    Returns: the accepted requested quantity.
    """
    print(f"available={available}, requested={requested}")
    if requested > available:
        raise ValueError("insufficient available quantity")
    print(requested)
    return requested
```

An operation applying that rule conditionally calls it inside the applicable mode
branch. Extract its earlier inline comparison too when another operation needs it.

Share equivalent classifications/calculations too. A new response form calls the
existing operation helper rather than copying its branches; different output
strings do not make the calculation different. Sharing only its validator leaves
copied classification unshared. Distinct calculations/rules need no common helper;
opposing updates sharing storage are distinct operations.

## Keep dispatch thin and review the saved source

Dispatch may branch on the parsed selector, including a fallback, but never
repeat shape checks, convert tokens, reconstruct commands or inspect raw input
after parsing. Forward converted values unchanged. Operations own arithmetic,
deltas, sums/extrema/sorting/index adjustments, replacement/clearing and mutations.
An operation helper is a separate callable. A selector branch inside the public
entrypoint remains dispatch; zero operands do not permit arithmetic there.
For a one-based position, dispatch calls `operation(parsed_index)` unchanged;
the operation validates it and computes `parsed_index - 1`. Computing that offset
in dispatch or hiding it inside a helper argument is still operation logic.
Dispatch may read/format existing state directly, add a response label, keep a
universal representation guard, or format parsed text with an operation's already
computed result. No getter or formatting-only wrapper is required. A calculation
or domain classification hidden in formatting still belongs in an operation.

Before each capability's final cumulative run, reopen the saved parser, dispatch,
validators and related operations, including unchanged earlier bodies. Report the
parser's converted return shape, dispatch arguments, and shared owners with all
current callers. Follow actual calls; compare every remaining inline acceptance
predicate and corresponding input role, including shared subconditions. Remove
obsolete parsing paths/branches, post-routing conversion and duplicated rules now;
passing behavior or helper names do not establish SRP. Keep growth focused, with
no parallel parsers or unrelated rewrites. Apply selected function documentation
and each function's own parameter/normal-return prints throughout.

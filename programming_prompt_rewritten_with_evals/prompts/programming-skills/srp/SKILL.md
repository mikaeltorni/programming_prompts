---
name: srp
description: >-
  v0.0.55 — Parsing returns converted arguments; operations call validators
  for converted-value and resource acceptance, sharing every current rule.
---

# Parsing, validation, operations and dispatch

**Create a called validator when a current operation first needs a domain
rule. Reuse it when another operation needs that rule.** This reliable default
avoids copying inline guards during later growth. A validator with one current
caller owns a real current rule; it is not a future capability or framework.
Do not invent acceptance rules the request does not require.

Put each current value/resource acceptance predicate and its rejection in that
called validator, including a rule needed only in one operation branch. The
operation may choose whether the validator applies, then calls it; leaving
the predicate and `raise` inline bypasses the rule owner and invites copies.

Read the entire request before coding. From the first agent-authored working
slice, including a small script or repair of a mixed entrypoint, keep the
public signature and use these owners:

| Owner | Work |
| --- | --- |
| Parser | Raw command classification, shape validation, normalization and token conversion. |
| Domain validators | Current acceptance rules on converted values and existing resources. |
| Operations | Call applicable validators, calculate results and change state. |
| Public dispatch | Parse once, route converted arguments unchanged, return/format results. |

When repairing a supplied mixed entrypoint, the first working repair also
extracts its raw parsing/conversion and core operation into these owners.
Fixing only the reported result inside the mixed public function leaves that
slice noncompliant; extracting it in a later capability does not repair the
earlier slice. Keep the extraction local to the current behavior and preserve
the public signature; it introduces no future commands.

Implement only the current capability. A validator is called by its current
operation immediately; future commands, selectors and checks wait for their
own capability.

## Parsing ends before routing

One parser receives the raw command and returns its selector and fully
converted arguments. It owns stripping, splitting, slicing, regex matching,
text normalization, selector classification and operand counts before indexing.
Check each documented form, including zero-operand forms. Exact matching is
valid. Smaller form parsers may compose inside this boundary.
Internal form helpers are part of that one parsing boundary; the dispatcher
still calls the outer parser once and receives fully converted arguments.

Prefer selector-and-arguments results from the first slice so later forms
extend the same parser. Arguments-only parsing is valid for one operation,
and a validated selector alone for a zero-operand form. When adding a command,
update an earlier arguments-only return and its caller together. Dispatch never
chooses a form parser by examining raw input.

Return normalized text and numeric values, not raw numeric strings or operand
lists awaiting shape checks. Builtin conversion errors and lexical grammar
belong here. Predicates on successfully converted values belong in the
operation layer: sign, finiteness, magnitude, integral-value restrictions,
zero divisors, resource constraints, existence, uniqueness and funds/capacity.
A successful float/Decimal conversion can produce NaN or infinity; calling
its finiteness rejection invalid input does not make it a conversion rule.
Likewise, `if not value.is_integer()` after successful float conversion is a
whole-value acceptance rule, even in the first whole-number capability; put it
in the operation's called validator. Builtin `int(token)` rejecting lexical
syntax is different from converting with float and then rejecting its value.
Representation normalization may preserve acceptance and mathematical value;
it must not hide a converted-value rejection in parsing.

For a current numeric form requiring finite whole-valued numbers, keep conversion and the
acceptance check in different owners. Even `inf`/`nan` can convert successfully;
the operation rejects them through its validator. The outer parser calls the
conversion helper before returning its converted argument tuple. Dispatch and
operations never call token-conversion helpers; operations call domain validators:

```python
import math


def parse_number(token):
    """Convert a numeric token without imposing converted-value rules.
    Parameters: token - the current form's numeric text.
    Returns: the converted floating-point value.
    """
    print(f"token={token}")
    result = float(token)
    print(result)
    return result


def require_finite(value):
    """Require the finite value accepted by the current operation.
    Parameters: value - the already converted number.
    Returns: the accepted finite value.
    """
    print(f"value={value}")
    if not math.isfinite(value):
        raise ValueError("nonfinite value")
    print(value)
    return value


def require_integral(value):
    """Require the finite whole value accepted by the current operation.
    Parameters: value - the already converted floating-point number.
    Returns: the accepted finite whole value.
    """
    print(f"value={value}")
    value = require_finite(value)
    if not value.is_integer():
        raise ValueError("fractional value")
    print(value)
    return value


def calculate_half(value):
    """Halve a finite whole-valued number accepted by the current operation.
    Parameters: value - the already converted floating-point number.
    Returns: half the accepted whole value.
    """
    print(f"value={value}")
    value = require_integral(value)
    result = value / 2
    print(result)
    return result
```

Apply that boundary to Decimal finiteness and converted-value integrality too.
Widening an integer-only form to decimal values changes the converted-value
validator and representation, without moving acceptance into its parser.
When fractions become accepted, its operation drops the integral restriction;
it retains the finite rule only when the current contract still requires it.

## Operations call rule owners

Give a current acceptance rule a validator and call it before the operation's
calculation or mutation. For example, an availability rule can use:

```python
def require_available(available, requested):
    """Validate a request against an available quantity.
    Parameters: available - quantity the resource can supply; requested - quantity to consume.
    Returns: the accepted requested quantity.
    """
    print(f"available={available}, requested={requested}")
    if requested > available:
        raise ValueError("insufficient available quantity")
    print(requested)
    return requested


def consume_quantity(available, requested):
    """Calculate what remains after an accepted consumption.
    Parameters: available - current quantity; requested - quantity to consume.
    Returns: the remaining quantity.
    """
    print(f"available={available}, requested={requested}")
    requested = require_available(available, requested)
    result = available - requested
    print(result)
    return result


def calculate_request_cost(available, requested, unit_price):
    """Calculate a request cost accepted by the same availability rule.
    Parameters: available - current quantity; requested - quantity to price; unit_price - price per unit.
    Returns: the accepted request's cost.
    """
    print(f"available={available}, requested={requested}, unit_price={unit_price}")
    requested = require_available(available, requested)
    result = requested * unit_price
    print(result)
    return result
```

Every operation requiring that rule calls the same owner with its own
available/requested quantities. Different resource identities, variable names,
comparison direction or subsequent mutations do not make the rule different.
A multi-resource operation calls the existence validator for each resource.

When the contract requires nonempty data, two distinct calculations share its
acceptance as follows; the actual calls are essential:

```python
def require_nonempty(values):
    """Validate and return data for a nonempty-data operation.
    Parameters: values - the operation's existing collection.
    Returns: the accepted nonempty collection.
    """
    print(f"values={values}")
    if not values:
        raise ValueError("empty collection")
    print(values)
    return values


def calculate_average(values):
    """Calculate the average of accepted nonempty data.
    Parameters: values - the operation's existing collection.
    Returns: the arithmetic average.
    """
    print(f"values={values}")
    values = require_nonempty(values)
    result = sum(values) / len(values)
    print(result)
    return result


def calculate_extrema(values):
    """Calculate the extrema of accepted nonempty data.
    Parameters: values - the operation's existing collection.
    Returns: the minimum and maximum values.
    """
    print(f"values={values}")
    values = require_nonempty(values)
    result = (min(values), max(values))
    print(result)
    return result
```

Before adding an operation, read related existing owners. If an equivalent
rule is still inline, extract it and replace every earlier copy in this same
edit; the new operation calls that helper too. Compare shared subconditions,
not just entire validation blocks: positive-and-finite acceptance stays shared
when one operation additionally requires integrality. An unused helper shares
nothing. Apply this to identical acceptance, classification and calculation.
When another response form needs an existing classification or calculation,
call its operation helper instead of copying its branches into the new form.
Different final strings do not make the underlying calculation different.
Sharing only its domain validator still leaves a copied classification unshared.
An earlier conditional guard still counts: a rule used only in one branch of
an operation must share its owner with the same rule in another operation.
Adding a helper for the new operation while leaving an earlier inline guard
does not complete the extraction.

Before editing the next operation, report the existing rule owners and their
current callers from the saved source. When the new operation needs the same
rule, name the owner it will call and replace any earlier inline copy now.
Different parameter names or units do not change an equivalent acceptance rule.

Distinct calculations or domain rules need no common helper. Opposing updates
sharing a state variable are distinct operations; sharing storage alone proves
no shared decision. Operations choose their own delta, compute results and
own replacement/clearing, sums, extrema, sorting and index adjustment. Operations
choose which current validation modes/rules apply; their validators own the
accept/reject predicates. Mode selection is not permission to repeat those
predicates inline. Revising numeric
acceptance changes the operation/validator and any necessary parser
representation together, while routing continues to forward converted data.

## Keep public dispatch thin

The public entrypoint calls its parser once before choosing an operation,
passes converted arguments unchanged and returns/formats its result:

```python
def run_command(command):
    """Parse and route a current public command.
    Parameters: command - the raw command text.
    Returns: the selected operation's result.
    """
    print(f"command={command}")
    selector, arguments = parse_command(command)
    result = dispatch_operation(selector, arguments)
    print(result)
    return result
```

The routing helper is optional: the entrypoint may branch on the parsed
selector and call operations directly. Routing on an already-validated
selector, including a fallback, is permitted even in a single-operation slice.
It differs from raw classification. Do not repeat parser shape guards, convert
tokens again, reconstruct raw commands or inspect raw input after parsing.

Dispatch may directly read/format existing state without a pass-through getter,
add a literal response label, or keep a universal representation guard on
parsed values. Calculations such as min/max/sum/sorting, mutations, choosing a
delta and operation-specific acceptance belong in operations, including when
hidden inside formatting. No parallel parsers or unrelated rewrites.
Formatting parsed text together with an operation's already computed result
is permitted; a helper whose only work would be that final string is optional.

Before the final cumulative run for each capability, reopen the saved parser,
dispatcher, validators and related operations from disk, including unchanged
earlier operations. Inspect those actual bodies together rather than relying
on a draft, helper names or memory. Follow every validator call;
compare remaining inline predicates across operations, including corresponding
input roles and shared subconditions. Repair copied rules before committing;
passing public behavior does not verify SRP. Extend existing owners, remove
branches replaced by the current revision, and check new and retained public
behavior. With logging selected, each function's own parameter print precedes
helper calls and its complete normal result is printed before return.

Report a short review of those actual saved bodies before that run: the
parser's converted return shape, the arguments dispatch forwards, and each
shared rule's validator plus all current callers. Check token-conversion calls
in dispatch, raw text reused for formatting, old unused form parsers, and
remaining inline acceptance predicates. Remove obsolete parsing paths and
repair duplicated rules before running and committing. This review needs no
new plan file or committed inventory; helper names alone are not evidence.

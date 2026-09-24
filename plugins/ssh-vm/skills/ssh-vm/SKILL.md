---
name: ssh-vm
description: >-
  v1.0.1 — Connect to a VM over SSH when the user needs remote access to that VM.
---

# SSH VM connection

Use the SSH client to connect to the VM address supplied by the user. Check that
the target is reachable and report the connection result. Keep the target
address and authentication choice specific to the current request.

## Ubuntu live USB login

For an Ubuntu Desktop live USB session, try the account `ubuntu` unless the
user supplies another username. The live desktop may log in without a password;
that does not mean SSH accepts an empty password. Do not guess or invent a
password, and do not change SSH authentication settings to permit empty
passwords. Prefer a public key already authorized for that account. If the VM
uses another image or an installed system, verify the account on its console
with `whoami` before assuming `ubuntu` exists.

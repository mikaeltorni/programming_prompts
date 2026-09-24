---
name: ssh-vm
description: >-
  v1.0.3 — Connect to a VM over SSH when the user needs remote access to that VM.
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

## When SSH is unavailable

Try a short, noninteractive connection first and distinguish a refused port,
timeout, host-key warning, and authentication failure. Do not infer a missing
server from `Permission denied`. For `Connection refused` on an Ubuntu live
USB VM, tell the user to open a terminal **on the VM console** and run:

```bash
whoami
sudo apt update
sudo apt install -y openssh-server
sudo systemctl start ssh
sudo systemctl status ssh --no-pager
hostname -I
```

The first command confirms the account name, and `hostname -I` confirms the
current VM address. If no SSH key is already authorized, explain that the live
session's blank local password cannot be used for ordinary SSH login. Offer
`sudo passwd ubuntu` on the VM console to set a temporary password, replacing
`ubuntu` with the confirmed account when different. The user enters the new
password locally and must not send it to the agent. As an alternative, have the
user add the client's public key to that account's `~/.ssh/authorized_keys`
with `.ssh` mode `700` and `authorized_keys` mode `600`. Never ask for a private
key or suggest enabling empty SSH passwords.

If the server is active but still unreachable, check `sudo ss -lntp` for a
listener on port 22, compare the VM address with the requested target, and
check `sudo ufw status`; if UFW is active and blocking SSH, use
`sudo ufw allow OpenSSH` on the VM. A timeout can indicate VM networking or
firewall trouble. On a changed host-key warning, stop and verify the new key
fingerprint on the VM before updating local known hosts. Report the exact
failure and the next console action rather than claiming the VM was tested.
The live USB setup may disappear after a reboot unless the medium is persistent.

## Deploy and verify on the VM

After SSH login succeeds, confirm the remote identity and environment before
copying or changing files: run `id -un`, `hostname`, and the checks relevant to
the task. Use the user-supplied address, username, port, and identity when
provided; keep any chosen SSH options consistent across `ssh`, `scp`, and
`rsync`. Run a bounded connection probe such as
`ssh -o BatchMode=yes -o ConnectTimeout=5 user@host 'id -un; hostname'` so an
automated attempt cannot hang at a password prompt. If password login is the
only option, use an interactive terminal when available and never capture or
repeat the secret. Verify a new host key with the VM owner or its console
before trusting it.

For a deployment task, inspect the target path and its existing data first.
Copy only the files needed for the task with `scp` or `rsync` (without a delete
option), then run the project's documented installation or activation command
on the VM. Respect the target repository's safety and service rules. Run its
relevant tests or live checks **on the VM**, inspect the service status and
logs when applicable, and confirm the installed files or behavior there. A
local test does not establish VM success. Report the remote commands, their
results, and any work that could not be verified because SSH was unavailable.

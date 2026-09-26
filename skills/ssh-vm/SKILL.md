---
name: ssh-vm
description: >-
  v1.0.9 — Use when a task requires SSH access to a VM to deploy software or test it there. Skip local-only tests and SSH discussion without a remote VM action.
---

# SSH VM

Use this skill only when the task calls for an actual SSH deployment or test on
a VM. Ask for the VM IP or hostname if missing. Use `ubuntu` for an Ubuntu
Desktop live USB unless the user gives another username. If password login is
needed and no password or authorized key is available, ask for the VM login
password. Enter passwords only at an interactive SSH prompt; never print, log,
save, or put them in a shell command.

First try a short connection, such as
`ssh -o BatchMode=yes -o ConnectTimeout=5 ubuntu@VM_IP 'id -un; hostname'`.
Use the user's port, username, and key when provided. A password-only VM needs
an interactive SSH session after the probe.

## Fresh Ubuntu live USB

If port 22 refuses the connection, ask the user to finish the Ubuntu welcome
screen, open Terminal **on the VM**, and run:

```bash
whoami
sudo apt update
sudo apt install -y openssh-server
sudo systemctl start ssh
sudo passwd ubuntu
hostname -I
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Use the name from `whoami` instead of `ubuntu` if different. The user sets the
password at the local `passwd` prompts; a blank live-desktop login is not an
SSH password. The last two commands show the current IP and host-key
fingerprint. This setup can disappear on the next live USB boot.

A new live session may generate a new host key. If SSH warns that the key
changed, compare its fingerprint with the VM console's `ssh-keygen` output
before replacing the old `known_hosts` entry. Never disable host-key checks.
If the server answers but says `Permission denied`, check the username and
password; have the user reset the password with `sudo passwd ubuntu` on the VM
if needed. For a timeout, check the current IP, port 22 with
`sudo ss -lntp`, and `sudo ufw status` on the VM.

## Deploy and verify

After login, confirm `id -un`, `hostname`, and the relevant VM environment.
Inspect the destination before copying. Transfer the needed files with `scp`
or `rsync` without a delete option, run the project's installer or activation
on the VM, then check its behavior, status, and logs **on the VM**. Respect the
project's desktop and service rules.

For every relevant local change to a project the user asked to run on the VM,
update that project's VM copy, apply the change there, and verify it there.
Local tests alone do not prove a VM deployment. If SSH is unavailable, report
the exact failure and the VM-console step needed to resume.

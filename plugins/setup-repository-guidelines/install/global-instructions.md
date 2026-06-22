## Linked Linux setup repositories

At the start of a software task, determine whether the current Git repository
is `installation_scripts` or is listed in the sibling
`installation_scripts/scripts/repository_manifest.sh` `CLONE_REPOS` array. If
it is, invoke the `setup-repository-guidelines` skill before editing. Read
membership from that manifest each time; do not use a copied repository list,
so newly added repositories trigger the guidance automatically.

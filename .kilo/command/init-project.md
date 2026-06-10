commands:
  - name: init-project
    description: Auto-triggered initialization with UV and supply-chain protection
    skill: init-project
    match:
      - "*.toml"
      - "pyproject.toml"
      - "uv.lock"
    when:
      - "initializing a new project"
      - "adding python support"
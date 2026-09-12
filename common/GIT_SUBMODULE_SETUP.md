# Git Submodule Setup

`common/` is structured as the future submodule root.

When the shared repository is ready, migrate with this shape:

```powershell
git submodule add git@github.com:jpark-afk/micro_workaround.git common
git submodule update --init --recursive
```

Keep project-specific assets in the parent repository:

- `projects/project_name/user_work/`

Use deployment manifests from `common/management/` to combine shared assets with project-specific inputs.

```powershell
common\management\deploy_from_manifest.bat
```
# Releasing Ontology Author

The user-facing distribution is the `ontology-author` package on PyPI. Users
install it with:

```bash
uv tool install ontology-author
```

## One-time publisher setup

1. Create the `ontology-author` project on TestPyPI, then configure the repository
   as a trusted publisher for it.
2. Repeat for PyPI, with the GitHub Actions environment named `pypi`.
3. In GitHub, require approval for the `pypi` environment.

Trusted publishing uses GitHub's short-lived identity token; no PyPI password
or long-lived upload token is stored in this repository. See the
[PyPA GitHub Actions publishing guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).

## Release process

1. Update `version` in `pyproject.toml` and the release notes.
2. Build the inspector assets, then run `uv run --extra dev pytest` locally.
3. Create and push a version tag such as `v0.1.0`.
4. Create a matching GitHub Release. The release workflow builds an sdist and
   wheel, checks them, uploads them as release artifacts, and publishes to PyPI.
5. In a clean shell, verify the public install:

   ```bash
   uv tool install ontology-author
   mkdir smoke-project && cd smoke-project
   author attach cursor
   ```

The released wheel must include `ontology_author.world`, its bundled inspector
assets and the World SQLite implementation. Historical graph/MCP code is not part of the
normal installation.

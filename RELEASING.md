# Releasing FindMyBook

This project publishes releases from GitHub Actions. The `Release` workflow reads the version from `plugin.json`, builds a clean `FindMyBook.zip`, and attaches it to a GitHub release.

## 1. Prepare the release

1. Update `Version` in `plugin.json` using [Semantic Versioning](https://semver.org/). For example:

   ```json
   "Version": "1.0.0"
   ```

2. Update `README.md` if the installation or usage changed.
3. Commit the changes:

   ```powershell
   git add plugin.json README.md plugin-store/
   git commit -m "chore(release): prepare v1.0.0"
   ```

4. Push the commit:

   ```powershell
   git push origin main
   ```

## 2. Publish v1.0.0

Create and push a semver tag that matches `plugin.json`:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

The `Release` workflow will:

- verify that the tag matches `plugin.json`;
- build `FindMyBook.zip` without `img_cache/`, `debug.log`, or `__pycache__/`;
- publish the GitHub release with generated release notes.

You can also run the workflow manually from **Actions → Release → Run workflow**. In that case, the workflow creates the tag from `plugin.json`.

If the repository still has the old mutable `latest` tag/release, remove it so that `releases/latest` always resolves to a semver release:

```powershell
gh release delete latest --yes
git push origin :refs/tags/latest
```

## 3. Submit to the Flow Launcher plugin store

The manifest entry is staged at:

```
plugin-store/FindMyBook-de485b1f-be4a-4fda-bc3d-cdf9aa6ca801.json
```

1. Fork [Flow-Launcher/Flow.Launcher.PluginsManifest](https://github.com/Flow-Launcher/Flow.Launcher.PluginsManifest).
2. Copy the staged JSON file into the fork's `plugins/` directory.
3. Confirm that `UrlDownload` points to the new release asset and that `Version` matches `plugin.json`.
4. Open a pull request against the manifest repository.
5. Wait for approval. CDN propagation can take a few days after the pull request is merged.

Until the listing is approved, users can install the plugin directly:

```
pm install https://github.com/andreimidari/FindMyBook/releases/latest/download/FindMyBook.zip
```

After the first release, the manifest updater checks every few hours for new GitHub releases and refreshes the store entry automatically, including `Description`, `Author`, `Language`, `Website`, and `MinimumAppVersion`. Bump `plugin.json`, tag the release, and the store will pick it up.

## Release checklist

- [ ] `plugin.json` has a valid UUID `ID`.
- [ ] `plugin.json` has the real `Website` URL.
- [ ] `plugin.json` `Version` is bumped.
- [ ] `README.md` installation steps are current.
- [ ] `LICENSE` is present.
- [ ] The release tag matches `plugin.json` (`v1.0.0`).
- [ ] The release zip contains `main.py`, `plugin.json`, `app.png`, and `Lib/`.
- [ ] The release zip does not contain `img_cache/`, `debug.log`, or `__pycache__/`.
- [ ] The plugin-store manifest entry points to the new release.

# FindMyBook

Search for books on [Open Library](https://openlibrary.org/) directly from [Flow Launcher](https://www.flowlauncher.com/).

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> **Status:** manual installation is available now. The Flow Launcher plugin-store listing is pending approval.

## Installation

### Flow Launcher plugin store

Once the store listing is approved, install it from **Settings → Plugin Store**, or run:

```
pm install FindMyBook
```

### Manual installation

1. Download `FindMyBook.zip` from the [latest release](https://github.com/andreimidari/FindMyBook/releases/latest).
2. Extract it into a folder named `FindMyBook` inside your Flow Launcher plugins directory:

   ```
   %APPDATA%\FlowLauncher\Plugins\FindMyBook
   ```

3. Restart Flow Launcher.
4. Type `book` to start searching.

You can also install it straight from the release URL:

```
pm install https://github.com/andreimidari/FindMyBook/releases/latest/download/FindMyBook.zip
```

The zip already contains the bundled Python dependencies in `Lib/`, so you do not need to run `pip install`.

### From source

```powershell
git clone https://github.com/andreimidari/FindMyBook.git
```

Copy or move the cloned folder into `%APPDATA%\FlowLauncher\Plugins\FindMyBook`, then restart Flow Launcher.

## Usage

The plugin is triggered by the `book` keyword.

```
book <book title>
```

Examples:

```
book 1984
book harry potter
book the great gatsby
```

The plugin shows up to 5 matching books with their cover, author, and first publication year. Select a result to open its Open Library page in your browser.

You can change the action keyword in **Flow Launcher → Settings → Plugins → FindMyBook**.

## Features

- Search Open Library by title as you type.
- See covers, authors, and first publication years.
- Open the selected book's Open Library page with one click.
- Covers load directly from Open Library, so results appear without waiting for downloads.

## Requirements

- Flow Launcher, any recent release.
- An internet connection.

## Troubleshooting

**The plugin does not appear in Flow Launcher.**
- Make sure `plugin.json` is directly inside `%APPDATA%\FlowLauncher\Plugins\FindMyBook\`.
- Restart Flow Launcher.
- Check Flow Launcher's log and the plugin's `debug.log` for errors.

**No results are returned.**
- Check your internet connection.
- Try a shorter or more general title.
- Open Library may not have a matching work; try searching on [openlibrary.org](https://openlibrary.org/) directly.

**Covers are missing.**
- Open Library does not have a cover for every book.
- If a book has no cover, the plugin shows its own icon instead.
- Cover images are fetched by Flow Launcher from Open Library, so they need an internet connection.

**The first search is slow.**
- Results appear as soon as Open Library responds. Cover images load separately and may take a moment the first time Flow Launcher displays them.

## Development

Run the plugin manually:

```powershell
python main.py '{"method": "query", "parameters": ["1984"]}'
```

The plugin reads the JSON-RPC request from stdin or from `sys.argv[1]` and prints a JSON response to stdout.

Project layout:

```
main.py                       Plugin entry point and Open Library client
plugin.json                   Flow Launcher plugin manifest
app.png                       Plugin icon
Lib/                          Bundled Python dependencies
.github/workflows/main.yml    Bundles dependencies on requirements changes
.github/workflows/release.yml Builds and publishes the release zip
plugin-store/                 Staged Flow Launcher plugin-store manifest entry
RELEASING.md                  Release and store-submission checklist
LICENSE                       MIT license
```

## Releasing

See [RELEASING.md](RELEASING.md) for the release and plugin-store submission checklist.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

## Attribution

Book data and covers are provided by [Open Library](https://openlibrary.org/), a project of the [Internet Archive](https://archive.org/). This plugin is not affiliated with Open Library or the Internet Archive.

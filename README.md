# Screen Presenter

Desktop application that shows your camera as a presenter overlay, so you can record
your screen with any tool.

## Requirements

- Python 3.14 or later (`uv` installs it automatically)
- macOS 13 or later, Windows or Linux
- A camera

On Linux, the following system libraries are required: `libegl1`, `libgl1`,
`libdbus-1-3`, `libfontconfig1`, `libxkbcommon0`, `libxkbcommon-x11-0`,
`libxcb-cursor0`, `libxcb-icccm4`, `libxcb-image0`, `libxcb-keysyms1`, `libxcb-randr0`,
`libxcb-render-util0`, `libxcb-shape0`, `libxcb-xinerama0` and `libxcb-xkb1`.

## How to work in the project

### Install Uv

In macOS and Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

In Windows:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Set up the project

```bash
git clone https://github.com/jajimenez/screen-presenter.git
cd screen-presenter
uv sync
```

### Run the application

```bash
uv run screen-presenter
```

or:

```bash
uv run python -m screen_presenter
```

On macOS, the system asks for camera permission the first time the application runs.

### Run the tests

```bash
uv run pytest
```

### Lint and format the code

```bash
uv run ruff check .
uv run ruff format .
```

### Build the application

The application is packaged with Briefcase:

```bash
uv sync --group package
uv run briefcase create
uv run briefcase build
uv run briefcase run
uv run briefcase package
```

- `create` generates the application scaffold for the current platform.
- `build` compiles the application.
- `run` runs the built application.
- `package` creates the distributable package for the current platform. On macOS, use
  `uv run briefcase package --adhoc-sign` for local builds that are not signed with a
  developer identity.

The Linux package uses the system Python, so the target system must provide Python 3.14
or later.

### Versioning and releases

The version is taken from the Git tag by hatch-vcs and
`src/screen_presenter/_version.py` is generated automatically, so don't edit it by hand.

To create a release, tag the commit and push the tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Project structure

```text
src/screen_presenter/     Application source code
    app.py                Entry point (creates the QApplication and the main window)
    main_window.py        Main window
    camera_controller.py  Camera handling
    about_dialog.py       "About" dialog
    platform_support.py   Platform-specific settings
    resources/            Logos and other resources
packaging/                Application icons used by Briefcase
tests/                    Tests
```

## License

This project is licensed under the terms of the [MIT license](LICENSE).

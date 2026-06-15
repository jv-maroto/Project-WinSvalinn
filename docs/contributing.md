# Contributing to WinSvalinn

## Development Setup

```bash
# Clone the repository
git clone https://github.com/winsvalinn/winsvalinn.git
cd winsvalinn

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run the app
python -m winsvalinn
```

## Project Structure

See [architecture.md](architecture.md) for detailed module documentation.

## Code Guidelines

- **No hardcoded colors** — import from `winsvalinn.constants`
- **All strings through i18n** — use `self.i18n.t(key)` for user-visible text
- **Core modules stay GUI-free** — `core/` must not import tkinter/customtkinter
- **Thread long operations** — never block the GUI thread
- **Silent registry failures** — registry tweaks use try/except to avoid crashes

## Adding a New View

1. Create `src/winsvalinn/ui/views/my_view.py`
2. Define a mixin class (e.g., `MyViewMixin`)
3. Add it to the inheritance chain in `app.py`
4. Add navigation entry in `_build_sidebar()` and `_navigate()`
5. Add i18n key in `i18n/strings.py`

## Running Tests

```bash
pytest                    # Run all tests
pytest tests/test_security.py  # Run specific test
pytest -v                 # Verbose output
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

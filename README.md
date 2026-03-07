# flask-debugtoolbar-extrapanels

A collection of extra panels for [Flask-DebugToolbar](https://github.com/flask-debugtoolbar/flask-debugtoolbar).

## Panels

### SignalsPanel

Displays all [Blinker](https://blinker.readthedocs.io/) signals fired during a request, including the built-in Flask signals and any custom signals you register.

The panel shows:
- Signal name
- Sender
- Keyword arguments
- Time fired

Built-in Flask signals tracked automatically:

- `request_started`
- `request_finished`
- `request_tearing_down`
- `got_request_exception`
- `template_rendered`
- `before_render_template`
- `appcontext_pushed`
- `appcontext_popped`
- `appcontext_tearing_down`
- `message_flashed`

## Installation

```bash
pip install flask-debugtoolbar-extrapanels
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add flask-debugtoolbar-extrapanels
```

## Requirements

- Python >= 3.10
- flask-debugtoolbar >= 0.16.0

## Usage

Add `flask_debugtoolbar_extrapanels.SignalsPanel` to the `DEBUG_TB_PANELS` list in your Flask app config:

```python
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key"
app.config["DEBUG"] = True
app.config["DEBUG_TB_ENABLED"] = True
app.config["DEBUG_TB_PANELS"] = [
    "flask_debugtoolbar.panels.versions.VersionDebugPanel",
    "flask_debugtoolbar.panels.timer.TimerDebugPanel",
    "flask_debugtoolbar.panels.headers.HeaderDebugPanel",
    "flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel",
    "flask_debugtoolbar.panels.config_vars.ConfigVarsDebugPanel",
    "flask_debugtoolbar.panels.template.TemplateDebugPanel",
    "flask_debugtoolbar.panels.logger.LoggingPanel",
    "flask_debugtoolbar.panels.route_list.RouteListDebugPanel",
    "flask_debugtoolbar_extrapanels.SignalsPanel",
]

toolbar = DebugToolbarExtension(app)
```

### Watching custom signals

Use `SignalsPanel.watch()` to register any Blinker `NamedSignal` before the first request:

```python
from blinker import signal
from flask_debugtoolbar_extrapanels import SignalsPanel

my_signal = signal("my-custom-signal")
SignalsPanel.watch("my_custom_signal", my_signal)
```

After registration, every time `my_signal` fires during a request it will appear in the Signals panel.

## Running the example app

```bash
git clone https://github.com/mariofix/flask-debugtoolbar-extrapanels.git
cd flask-debugtoolbar-extrapanels
pip install flask-debugtoolbar
pip install -e .
python example_app.py
```

Open `http://localhost:5000/` in your browser. The debug toolbar will appear with a **Signals** tab.

- Visit `/flash` to trigger `message_flashed`
- Visit `/custom` to trigger a custom Blinker signal

## Development

### Setup

```bash
git clone https://github.com/mariofix/flask-debugtoolbar-extrapanels.git
cd flask-debugtoolbar-extrapanels
uv sync --group dev
```

### Running tests

```bash
uv run pytest
```

## License

See [LICENSE](LICENSE).

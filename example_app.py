"""Minimal example app demonstrating the SignalsPanel.

Run with:
    python example_app.py

Then open http://localhost:5000/ in your browser and look for the
"Signals" tab in the debug toolbar.
"""

from flask import Flask, flash, redirect, render_template_string, url_for

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
    # --- Our custom panel ---
    "flask_debugtoolbar_extrapanels.SignalsPanel",
]

from flask_debugtoolbar import DebugToolbarExtension  # noqa: E402

toolbar = DebugToolbarExtension(app)

# Optionally watch a custom Blinker signal:
from blinker import signal  # noqa: E402

from flask_debugtoolbar_extrapanels import SignalsPanel  # noqa: E402

my_signal = signal("my-custom-signal")
SignalsPanel.watch("my_custom_signal", my_signal)

INDEX_TEMPLATE = """
<!doctype html>
<html>
<head><title>SignalsPanel Example</title></head>
<body>
  <h1>Flask SignalsPanel Example</h1>
  <p>This page renders a template (triggering <code>template_rendered</code>)
     and flashes a message (triggering <code>message_flashed</code>).</p>
  <p><a href="/flash">Visit /flash to see message_flashed</a></p>
  <p><a href="/custom">Visit /custom to trigger a custom signal</a></p>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul>{% for m in messages %}<li>{{ m }}</li>{% endfor %}</ul>
    {% endif %}
  {% endwith %}
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_TEMPLATE)


@app.route("/flash")
def flash_route():
    flash("Hello from /flash!")
    return redirect(url_for("index"))


@app.route("/custom")
def custom_signal_route():
    my_signal.send(app, message="hello from custom signal", value=42)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)

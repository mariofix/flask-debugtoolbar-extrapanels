import pytest
from blinker import signal as blinker_signal
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

from flask_debugtoolbar_extrapanels import SignalsPanel
from flask_debugtoolbar_extrapanels.signals import _safe_repr


def make_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret"
    app.config["DEBUG"] = True
    app.config["TESTING"] = True
    app.config["DEBUG_TB_ENABLED"] = True
    app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
    app.config["DEBUG_TB_PANELS"] = [
        "flask_debugtoolbar_extrapanels.SignalsPanel",
    ]

    @app.route("/")
    def index():
        return "ok"

    DebugToolbarExtension(app)
    return app


@pytest.fixture(autouse=True)
def reset_extra_signals():
    original = SignalsPanel._extra_signals[:]
    yield
    SignalsPanel._extra_signals = original


@pytest.fixture
def app():
    return make_app()


@pytest.fixture
def client(app):
    return app.test_client()


class TestSafeRepr:
    def test_normal_value(self):
        assert _safe_repr(42) == "42"

    def test_string_value(self):
        assert _safe_repr("hello") == "'hello'"

    def test_truncates_long_repr(self):
        long_obj = "x" * 300
        result = _safe_repr(long_obj)
        assert len(result) <= 200
        assert result.endswith("...")

    def test_handles_repr_exception(self):
        class Bad:
            def __repr__(self):
                raise ValueError("boom")

        result = _safe_repr(Bad())
        assert "repr raised" in result
        assert "ValueError" in result


class TestSignalsPanelMeta:
    def test_nav_title(self, app):
        with app.test_request_context("/"):
            panel = SignalsPanel(jinja_env=None, context={})
            assert panel.nav_title() == "Signals"

    def test_title(self, app):
        with app.test_request_context("/"):
            panel = SignalsPanel(jinja_env=None, context={})
            assert panel.title() == "Flask Signals"

    def test_url(self, app):
        with app.test_request_context("/"):
            panel = SignalsPanel(jinja_env=None, context={})
            assert panel.url() == ""

    def test_nav_subtitle_no_signals(self, app):
        with app.test_request_context("/"):
            panel = SignalsPanel(jinja_env=None, context={})
            assert panel.nav_subtitle() == "0 signals fired"

    def test_nav_subtitle_one_signal(self, app):
        with app.test_request_context("/"):
            panel = SignalsPanel(jinja_env=None, context={})
            panel._fired.append({"name": "x", "sender": "s", "kwargs": {}, "time": "t"})
            assert panel.nav_subtitle() == "1 signal fired"

    def test_nav_subtitle_many_signals(self, app):
        with app.test_request_context("/"):
            panel = SignalsPanel(jinja_env=None, context={})
            panel._fired.extend(
                [
                    {"name": "x", "sender": "s", "kwargs": {}, "time": "t"},
                    {"name": "y", "sender": "s", "kwargs": {}, "time": "t"},
                ]
            )
            assert panel.nav_subtitle() == "2 signals fired"


class TestSignalsPanelWatch:
    def test_watch_registers_signal(self):
        sig = blinker_signal("test-watch-signal")
        SignalsPanel.watch("test_watch_signal", sig)
        names = [name for name, _ in SignalsPanel._extra_signals]
        assert "test_watch_signal" in names

    def test_watched_signal_fires(self, app):
        sig = blinker_signal("test-fire-signal")
        SignalsPanel.watch("test_fire_signal", sig)

        with app.test_request_context("/"):
            panel = SignalsPanel(jinja_env=None, context={})
            sig.send(app, data="hello")
            names = [e["name"] for e in panel._fired]
            assert "test_fire_signal" in names


class TestSignalsPanelDisconnect:
    def test_disconnect_stops_recording(self, app):
        with app.test_request_context("/"):
            panel = SignalsPanel(jinja_env=None, context={})
            import flask.signals

            initial_count = len(panel._fired)
            panel._disconnect_all()

            flask.signals.message_flashed.send(
                app, message="after disconnect", category="info"
            )

            assert len(panel._fired) == initial_count
            assert panel._connections == []
            assert panel._receivers == []


class TestSignalsPanelContent:
    def test_content_no_signals(self, app):
        with app.test_request_context("/"):
            panel = SignalsPanel(jinja_env=None, context={})
            html = panel.content()
            assert "No signals fired" in html

    def test_content_with_signals(self, app):
        with app.test_request_context("/"):
            panel = SignalsPanel(jinja_env=None, context={})
            panel._fired.append(
                {
                    "name": "test_signal",
                    "sender": "<Flask app>",
                    "kwargs": {"key": "value"},
                    "time": "12:00:00.000",
                }
            )
            html = panel.content()
            assert "test_signal" in html
            assert "12:00:00.000" in html


class TestSignalsPanelIntegration:
    def test_flask_signal_recorded_on_request(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_has_content_flag(self, app):
        assert SignalsPanel.has_content is True

    def test_name(self, app):
        assert SignalsPanel.name == "Signals"

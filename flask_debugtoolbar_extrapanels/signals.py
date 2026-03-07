"""Flask Signals debug panel for Flask-DebugToolbar.

Records every Blinker signal that fires during a request and displays them
in the debug toolbar so you can see exactly which signals were sent, who
sent them, and what keyword arguments were passed.
"""

from __future__ import annotations

import datetime
import typing as t

import flask.signals
from blinker import NamedSignal
from flask_debugtoolbar.panels import DebugPanel
from jinja2 import Environment, PackageLoader
from werkzeug import Request, Response

# All built-in Flask signals with their human-readable names.
_FLASK_SIGNALS: list[tuple[str, NamedSignal]] = [
    ("request_started", flask.signals.request_started),
    ("request_finished", flask.signals.request_finished),
    ("request_tearing_down", flask.signals.request_tearing_down),
    ("got_request_exception", flask.signals.got_request_exception),
    ("template_rendered", flask.signals.template_rendered),
    ("before_render_template", flask.signals.before_render_template),
    ("appcontext_pushed", flask.signals.appcontext_pushed),
    ("appcontext_popped", flask.signals.appcontext_popped),
    ("appcontext_tearing_down", flask.signals.appcontext_tearing_down),
    ("message_flashed", flask.signals.message_flashed),
]

# Jinja2 environment that loads templates from *this* package so that the
# panel's template does not need to be installed inside flask_debugtoolbar.
_jinja_env: Environment | None = None


def _get_jinja_env() -> Environment:
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            autoescape=True,
            loader=PackageLoader(__name__, "templates"),
        )
    return _jinja_env


def _safe_repr(value: t.Any) -> str:
    """Return a short, safe string representation of *value*."""
    try:
        r = repr(value)
    except Exception as exc:  # noqa: BLE001
        r = f"<repr raised {type(exc).__name__}: {exc}>"
    # Truncate very long reprs so they don't overwhelm the panel.
    if len(r) > 200:
        r = r[:197] + "..."
    return r


class SignalsPanel(DebugPanel):
    """Debug panel that lists every signal fired during the current request.

    Both built-in Flask signals and any custom Blinker :class:`NamedSignal`
    objects registered via :meth:`watch` are captured.

    Usage in ``DEBUG_TB_PANELS``::

        DEBUG_TB_PANELS = [
            ...
            "flask_debugtoolbar_extrapanels.SignalsPanel",
        ]

    To also monitor your own signals, call :meth:`watch` before the first
    request::

        from blinker import signal
        my_signal = signal("my-signal")

        from flask_debugtoolbar_extrapanels import SignalsPanel
        SignalsPanel.watch("my_signal", my_signal)
    """

    name = "Signals"
    has_content = True

    # Extra signals registered by the application.
    _extra_signals: list[tuple[str, NamedSignal]] = []

    @classmethod
    def watch(cls, name: str, signal: NamedSignal) -> None:
        """Register an additional Blinker signal to monitor.

        :param name: A human-readable label shown in the panel.
        :param signal: The :class:`blinker.NamedSignal` to watch.
        """
        cls._extra_signals.append((name, signal))

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self._fired: list[dict[str, t.Any]] = []
        # Keep strong references to the receivers so they are not garbage-
        # collected while connected (blinker uses weak references by default
        # when connecting bound methods).
        self._receivers: list[t.Callable[..., None]] = []
        self._connections: list[tuple[NamedSignal, t.Callable[..., None]]] = []

        all_signals = _FLASK_SIGNALS + self.__class__._extra_signals
        for signal_name, blinker_signal in all_signals:
            receiver = self._make_receiver(signal_name)
            self._receivers.append(receiver)
            blinker_signal.connect(receiver, weak=False)
            self._connections.append((blinker_signal, receiver))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_receiver(self, signal_name: str) -> t.Callable[..., None]:
        """Return a closure that appends one entry to ``self._fired``."""

        def receiver(sender: t.Any, **kwargs: t.Any) -> None:
            self._fired.append(
                {
                    "name": signal_name,
                    "sender": _safe_repr(sender),
                    "kwargs": {k: _safe_repr(v) for k, v in kwargs.items()},
                    "time": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
                }
            )

        return receiver

    def _disconnect_all(self) -> None:
        for blinker_signal, receiver in self._connections:
            blinker_signal.disconnect(receiver)
        self._connections.clear()
        self._receivers.clear()

    # ------------------------------------------------------------------
    # DebugPanel interface
    # ------------------------------------------------------------------

    def process_response(self, request: Request, response: Response) -> None:
        # Disconnect eagerly so signals fired during teardown are still
        # captured but we don't leak receivers across requests.
        self._disconnect_all()

    def nav_title(self) -> str:
        return "Signals"

    def nav_subtitle(self) -> str:
        n = len(self._fired)
        word = "signal" if n == 1 else "signals"
        return f"{n} {word} fired"

    def title(self) -> str:
        return "Flask Signals"

    def url(self) -> str:
        return ""

    def render(self, template_name: str, context: dict[str, t.Any]) -> str:
        # Override to use our own Jinja2 env so the template is loaded from
        # this package rather than from flask_debugtoolbar's template dir.
        template = _get_jinja_env().get_template(template_name)
        return template.render(**context)

    def content(self) -> str:
        context = self.context.copy()
        context["fired_signals"] = self._fired
        return self.render("panels/signals.html", context)

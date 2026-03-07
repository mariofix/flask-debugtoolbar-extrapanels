from __future__ import annotations

import datetime
import typing as t

import flask.signals
from blinker import NamedSignal
from flask_debugtoolbar.panels import DebugPanel
from jinja2 import Environment, PackageLoader
from werkzeug import Request, Response

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
    try:
        r = repr(value)
    except Exception as exc:  # noqa: BLE001
        r = f"<repr raised {type(exc).__name__}: {exc}>"

    if len(r) > 200:
        r = r[:197] + "..."
    return r


class SignalsPanel(DebugPanel):
    name = "Signals"
    has_content = True

    # Extra signals registered by the application.
    _extra_signals: list[tuple[str, NamedSignal]] = []

    @classmethod
    def watch(cls, name: str, signal: NamedSignal) -> None:
        cls._extra_signals.append((name, signal))

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self._fired: list[dict[str, t.Any]] = []
        self._receivers: list[t.Callable[..., None]] = []
        self._connections: list[tuple[NamedSignal, t.Callable[..., None]]] = []

        all_signals = _FLASK_SIGNALS + self.__class__._extra_signals
        for signal_name, blinker_signal in all_signals:
            receiver = self._make_receiver(signal_name)
            self._receivers.append(receiver)
            blinker_signal.connect(receiver, weak=False)
            self._connections.append((blinker_signal, receiver))

    def _make_receiver(self, signal_name: str) -> t.Callable[..., None]:

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

    def process_response(self, request: Request, response: Response) -> None:
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

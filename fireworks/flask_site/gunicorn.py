# Based on http://docs.gunicorn.org/en/19.6.0/custom.html

import multiprocessing
from typing import Any, Mapping, Optional

import gunicorn.app.base

from fireworks.flask_site.app import app as handler_app


def number_of_workers() -> int:
    return (multiprocessing.cpu_count() * 2) + 1


class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options: Optional[Mapping[str, Any]] = None) -> None:
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self) -> None:
        config = {key: value for key, value in self.options.items() if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


if __name__ == "__main__":
    options = {
        "bind": "127.0.0.1:8080",
        "workers": number_of_workers(),
    }
    StandaloneApplication(handler_app, options).run()

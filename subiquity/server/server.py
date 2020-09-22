# Copyright 2020 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

from aiohttp import web

from subiquitycore.core import Application

from subiquity.common.api.server import bind
from subiquity.common.apidef import API
from subiquity.common.errorreport import (
    ErrorReporter,
    )
from subiquity.common.types import (
    ApplicationState,
    )


log = logging.getLogger('subiquity.server.server')


class MetaController:

    def __init__(self, app):
        self.app = app
        self.context = app.context.child("Meta")

    async def status_GET(self) -> ApplicationState:
        return self.app.status


class SubiquityServer(Application):

    project = "subiquity"
    from subiquity.server import controllers as controllers_mod
    controllers = []

    def make_model(self):
        return None

    def __init__(self, opts):
        super().__init__(opts)
        self.status = ApplicationState.STARTING
        self.server_proc = None
        self.error_reporter = ErrorReporter(
            self.context.child("ErrorReporter"), self.opts.dry_run, self.root)

    def note_file_for_apport(self, key, path):
        self.error_reporter.note_file_for_apport(key, path)

    def note_data_for_apport(self, key, value):
        self.error_reporter.note_data_for_apport(key, value)

    def make_apport_report(self, kind, thing, *, wait=False, **kw):
        return self.error_reporter.make_apport_report(
            kind, thing, wait=wait, **kw)

    async def start_api_server(self):
        app = web.Application()
        bind(app.router, API.meta, MetaController(self))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.UnixSite(runner, self.opts.socket)
        await site.start()

    async def start(self):
        await super().start()
        await self.start_api_server()
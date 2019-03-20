# Copyright 2019 Canonical, Ltd.
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
import subprocess

from subiquitycore.controller import BaseController
from subiquitycore.utils import run_command

from subiquity.ui.views import ZdevView


log = logging.getLogger("subiquitycore.controller.zdev")

class ZdevController(BaseController):

    def __init__(self, common):
        super().__init__(common)
        self.model = self.base_model.zdev

    def default(self):
        self.ui.set_body(ZdevView(self.model, self))

    def cancel(self):
        self.signal.emit_signal('prev-screen')

    def done(self):
        # switch to next screen
        self.signal.emit_signal('next-screen')

    def chzdev(self, action, zdevinfo):
        # TODO add the fake UI to operate on zdev objects
        chzdev_cmd = ['chzdev', '--%s' % action, zdevinfo.id]
        run_command(chzdev_cmd)


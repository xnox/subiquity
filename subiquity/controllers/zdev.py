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

import attr
import logging
import platform
import shlex

from collections import OrderedDict
from urwid import Text

from subiquitycore.controller import BaseController
from subiquitycore.ui.utils import Color
from subiquitycore.utils import run_command
from subiquity.ui.views import ZdevView


log = logging.getLogger("subiquitycore.controller.zdev")

lszdev_cmd = ['lszdev', '--pairs', '--columns',
              'id,type,on,exists,pers,auto,failed,names']

lszdev_stock = '''id="0.0.0190" type="dasd-eckd" on="no" exists="yes" pers="no" auto="no" failed="no" names=""
id="0.0.0191" type="dasd-eckd" on="no" exists="yes" pers="no" auto="no" failed="no" names=""
id="0.0.019d" type="dasd-eckd" on="no" exists="yes" pers="no" auto="no" failed="no" names=""
id="0.0.019e" type="dasd-eckd" on="no" exists="yes" pers="no" auto="no" failed="no" names=""
id="0.0.0200" type="dasd-eckd" on="yes" exists="yes" pers="yes" auto="no" failed="no" names="dasda"
id="0.0.0300" type="dasd-eckd" on="yes" exists="yes" pers="yes" auto="no" failed="no" names="dasdb"
id="0.0.0592" type="dasd-eckd" on="no" exists="yes" pers="no" auto="no" failed="no" names=""
id="0.0.0600:0.0.0601:0.0.0602" type="qeth" on="yes" exists="yes" pers="yes" auto="no" failed="no" names="enc600"
id="0.0.0603:0.0.0604:0.0.0605" type="qeth" on="no" exists="yes" pers="yes" auto="no" failed="yes" names="enc603"
id="0.0.0606:0.0.0607:0.0.0608" type="qeth" on="no" exists="yes" pers="no" auto="no" failed="no" names=""
id="0.0.d000:0.0.d001:0.0.d002" type="qeth" on="yes" exists="yes" pers="yes" auto="no" failed="no" names="encd000"
id="0.0.d003:0.0.d004:0.0.d005" type="qeth" on="no" exists="yes" pers="no" auto="no" failed="no" names=""
id="0.0.0009" type="generic-ccw" on="yes" exists="yes" pers="yes" auto="no" failed="no" names=""
id="0.0.000c" type="generic-ccw" on="no" exists="yes" pers="no" auto="no" failed="no" names=""
id="0.0.000d" type="generic-ccw" on="yes" exists="yes" pers="yes" auto="no" failed="no" names="vmpun-0.0.000d"
id="0.0.000e" type="generic-ccw" on="yes" exists="yes" pers="no" auto="yes" failed="no" names="vmprt-0.0.000e"'''  # noqa: E501


@attr.s
class ZdevInfo:
    id = attr.ib()
    type = attr.ib()
    on = attr.ib()
    exists = attr.ib()
    pers = attr.ib()
    auto = attr.ib()
    failed = attr.ib()
    names = attr.ib()

    @classmethod
    def from_row(cls, row):
        row = dict((k.split('=', 1) for k in shlex.split(row)))
        for k, v in row.items():
            if v == "yes":
                row[k] = True
            if v == "no":
                row[k] = False
        return ZdevInfo(**row)

    @property
    def status(self):
        if self.failed:
            return Color.info_error(Text(_("failed"), align="center"))
        if self.auto and self.on:
            return Color.info_minor(Text(_("auto"), align="center"))
        if self.pers and self.on:
            return Text(_("online"), align="center")
        return Text("", align="center")


class ZdevController(BaseController):

    def __init__(self, common):
        super().__init__(common)
        self.model = self.base_model.zdev
        self.answers = self.all_answers.get('Zdev', {})
        if self.opts.dry_run:
            if platform.machine() == 's390x':
                devices = self.lszdev()
            else:
                devices = lszdev_stock.splitlines()
            zdevinfos = [ZdevInfo.from_row(row) for row in devices]
            self.zdevinfos = OrderedDict([(i.id, i) for i in zdevinfos])

    def default(self):
        if 'accept-default' in self.answers:
            self.done()
        self.ui.set_body(ZdevView(self.model, self))

    def cancel(self):
        self.signal.emit_signal('prev-screen')

    def done(self):
        # switch to next screen
        self.signal.emit_signal('next-screen')

    def chzdev(self, action, zdevinfo):
        if self.opts.dry_run:
            on = action == 'enable'
            self.zdevinfos[zdevinfo.id].on = on
            self.zdevinfos[zdevinfo.id].pers = on
        else:
            chzdev_cmd = ['chzdev', '--%s' % action, zdevinfo.id]
            run_command(chzdev_cmd)

    def get_zdevinfos(self):
        if self.opts.dry_run:
            return self.zdevinfos.values()
        else:
            return self.lszdev()

    def lszdev(self):
        devices = run_command(lszdev_cmd, universal_newlines=True).stdout
        devices = devices.splitlines()
        return [ZdevInfo.from_row(row) for row in devices]

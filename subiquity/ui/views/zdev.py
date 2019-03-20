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

""" zdev

Provides device activation and configuration on s390x

"""
import logging
import shlex

import attr

from urwid import (
    connect_signal,
    Text,
    )

from subiquitycore.ui.actionmenu import (
    Action,
    ActionMenu,
    ActionMenuOpenButton,
    )
from subiquitycore.ui.buttons import (
    back_btn,
    cancel_btn,
    danger_btn,
    done_btn,
    menu_btn,
    other_btn,
    reset_btn,
    )
from subiquitycore.ui.container import (
    ListBox,
    WidgetWrap,
    )
from subiquitycore.ui.form import Toggleable
from subiquitycore.ui.stretchy import Stretchy
from subiquitycore.ui.table import (
    ColSpec,
    TablePile,
    TableRow,
    )
from subiquitycore.ui.utils import (
    button_pile,
    Color,
    make_action_menu_row,
    Padding,
    screen,
    )
from subiquitycore.view import BaseView

from subiquitycore.utils import run_command

log = logging.getLogger('subiquity.ui.zdev')

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
id="0.0.000e" type="generic-ccw" on="yes" exists="yes" pers="no" auto="yes" failed="no" names="vmprt-0.0.000e"'''

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
        for k,v in row.items():
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


class ZdevList(WidgetWrap):

    def __init__(self, parent):
        self.parent = parent
        self.table = TablePile([], spacing=2, colspecs={
            0: ColSpec(rpad=1),
            1: ColSpec(rpad=1),
            2: ColSpec(rpad=1),
            3: ColSpec(rpad=1),
        })
        self._no_zdev_content = Color.info_minor(
            Text(_("No zdev devices found.")))
        super().__init__(self.table)

    def _zdev_action(self, sender, action, zdevinfo):
        if action in ('disable', 'enable'):
            self.parent.controller.chzdev(action, zdevinfo)
            self.parent.refresh_model_inputs()

    def refresh_model_inputs(self):
        devices = run_command(lszdev_cmd, universal_newlines=True).stdout
        devices = devices.splitlines()
        #devices = lszdev_stock.splitlines()
        zdevinfos = [ZdevInfo.from_row(row) for row in devices]

        rows = [TableRow([
            Color.info_minor(heading) for heading in [
                Text(_("ID")),
                Text(_("ONLINE")),
                Text(_("TYPE")),
                Text(_("NAMES")),
            ]])]

        for i, zdevinfo in enumerate(zdevinfos):
            actions = [(_("Enable"), not zdevinfo.on, 'enable'),
                       (_("Disable"), zdevinfo.on, 'disable')]
            menu = ActionMenu(actions)
            connect_signal(menu, 'action', self._zdev_action, zdevinfo)
            cells = [
                Text(zdevinfo.id),
                zdevinfo.status,
                Text(zdevinfo.type),
                Text(zdevinfo.names),
                menu,
            ]
            row = make_action_menu_row(
                cells,
                menu,
                attr_map='menu_button',
                focus_map={
                    None: 'menu_button focus',
                    'info_minor': 'menu_button focus',
                })
            rows.append(row)
        self.table.set_contents(rows)
        if self.table._w.focus_position >= len(rows):
            self.table._w.focus_position = len(rows) - 1


class ZdevView(BaseView):
    title = _("Zdev setup")
    footer = _("Activate and configure Z devices")

    def __init__(self, model, controller):
        log.debug('FileSystemView init start()')
        self.model = model
        self.controller = controller

        self.zdev_list = ZdevList(self)

        body = [
            self.zdev_list,
            Text(""),
            ]

        self.lb = ListBox(body)
        frame = screen(
            self.lb, self._build_buttons(),
            focus_buttons=True)
        super().__init__(frame)
        self.refresh_model_inputs()
        log.debug('FileSystemView init complete()')

    def _build_buttons(self):
        return [
            done_btn(_("Continue"), on_press=self.done),
            back_btn(_("Back"), on_press=self.cancel),
            ]

    def refresh_model_inputs(self):
        self.zdev_list.refresh_model_inputs()
        self.lb.base_widget._select_first_selectable()

    def cancel(self, button=None):
        self.controller.cancel()

    def done(self, result):
        self.controller.done()

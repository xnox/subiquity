# Copyright 2015 Canonical, Ltd.
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

from urwid import Text, Pile, ListBox, CheckBox, Columns
from subiquity.models.filesystem import _humanize_size
from subiquity.view import ViewPolicy
from subiquity.ui.buttons import cancel_btn, done_btn
from subiquity.ui.utils import Color, Padding
from subiquity.ui.interactive import StringEditor
import logging

log = logging.getLogger('subiquity.ui.lvm')


class LogicalVolumeView(ViewPolicy):
    def __init__(self, model, signal, vg):
        self.model = model
        self.signal = signal
        self.vg = vg
        self.size = StringEditor(caption="")
        self.lv_name = StringEditor(caption="")
        body = [
            Padding.center_50(self._build_lv()),
            Padding.line_break(""),
            Padding.center_20(self._build_buttons())
        ]
        super().__init__(ListBox(body))

    def _build_lv(self):
        log.debug('lvm: _build_lv')
        items = [
            Text("CREATE LOGICAL VOLUME"),

            Columns(
                [
                    ("weight", 0.2, Text("Logical Volume Name",
                                         align="right")),
                    ("weight", 0.3,
                     Color.string_input(self.lv_name,
                                        focus_map="string_input focus"))
                ]
            ),
            Columns(
                [
                    ("weight", 0.2, Text("Logical Volume Size",
                                         align="right")),
                    ("weight", 0.3,
                     Color.string_input(self.size,
                                        focus_map="string_input focus"))
                ]
            )
        ]
        return Pile(items)

    def _build_buttons(self):
        log.debug('lvm: _build_buttons')
        cancel = cancel_btn(on_press=self.cancel)
        done = done_btn(on_press=self.done)

        buttons = [
            Color.button(done, focus_map='button focus'),
            Color.button(cancel, focus_map='button focus')
        ]
        return Pile(buttons)

    def done(self, result):
        result = {'name': self.lv_name.value,
                  'size': self.size.value}
        log.debug('lvm_pv_done: result = {}'.format(result))
        self.signal.emit_signal('raid:create-lv', result)

    def cancel(self, button):
        log.debug('lvm: button_cancel')
        self.signal.prev_signal()


class LVMView(ViewPolicy):
    def __init__(self, model, signal):
        self.model = model
        self.signal = signal
        self.selected_disks = []
        body = [
            Padding.center_50(self._build_pv_selection()),
            Padding.line_break(""),
            Padding.center_20(self._build_buttons())
        ]
        super().__init__(ListBox(body))

    def _build_pv_selection(self):
        log.debug('lvm: _build_pv_selection')
        items = [
            Text("DISK SELECTION")
        ]

        # XXX: is it still not recommended to use whole disks for pvcreate?
        # avail_disks = self.model.get_empty_disk_names()
        avail_parts = self.model.get_empty_partition_names()
        avail_devs = sorted(avail_parts)
        if len(avail_devs) == 0:
            return items.append(
                [Color.info_minor(Text("No available disks."))])

        for dname in avail_devs:
            device = self.model.get_disk(dname)
            if device.path != dname:
                # we've got a partition
                pvdev = device.get_partition(dname)
            else:
                pvdev = device

            disk_sz = _humanize_size(pvdev.size)
            disk_string = "{}     {},     {}".format(dname,
                                                     disk_sz,
                                                     device.model)
            log.debug('lvm: disk_string={}'.format(disk_string))
            self.selected_disks.append(CheckBox(disk_string))

        items += self.selected_disks

        return Pile(items)

    def _build_buttons(self):
        log.debug('lvm: _build_buttons')
        cancel = cancel_btn(on_press=self.cancel)
        done = done_btn(on_press=self.done)

        buttons = [
            Color.button(done, focus_map='button focus'),
            Color.button(cancel, focus_map='button focus')
        ]
        return Pile(buttons)

    def done(self, result):
        result = [x.get_label() for x in self.selected_disks if x.state]
        log.debug('lvm_pv_done: result = {}'.format(result))
        self.signal.emit_signal('lvm:create-vg', result)

    def cancel(self, button):
        log.debug('lvm: button_cancel')
        self.signal.prev_signal()

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

import logging
from subiquity.model import ModelPolicy


log = logging.getLogger('subiquity.models.lvm')


class VolumeGroup:
    def __init__(self, name, devices):
        self.name = name
        self.devices = devices
        self.lvs = []

    def add_lv(self, name, size):
        self.lvs.append({'name': name, 'size': size})

    def to_spec(self):
        return {
            'volume_group': {
                'name': self.name,
                'devices': self.devices,
                'lvs': [x for x in self.lvs]
            }
        }


class LVMModel(ModelPolicy):
    """ Model representing LVM
    """
    base_signal = 'menu:lvm:main'
    signals = [
        ('Create volume group',
         base_signal,
         'create_vg'),
        ('Create logical volume',
         'lvm:create-lv',
         'create_lv'),
        ('Finish LVM',
         'lvm:finish',
         'lvm_handler')
    ]

    menu = [
        ('Create Volume Groups',
         'lvm:create-vg',
         'create_vg'),
        ('Create Logical Volums',
         'lvm:create-lv',
         'create_lv')
    ]

    def get_signal_by_name(self, selection):
        for x, y, z in self.get_signals():
            if x == selection:
                return y

    def get_signals(self):
        return self.signals

    def get_menu(self):
        return self.menu

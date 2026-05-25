#!/usr/bin/env python3
#
# Copyright VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import requests

from sys import exit

from vyos.config import Config
from vyos.configdict import is_node_changed
from vyos.configverify import verify_vrf
from vyos.template import render
from vyos.utils.process import call
from vyos import ConfigError
from vyos import airbag
from vyos.utils.process import process_named_running



airbag.enable()

vmagent_service_file = '/etc/systemd/system/vmagent.service'
vmagent_systemd_service = 'vmagent.service'
vmagent_config_file = '/run/vmagent/prometheus.yml'


def get_config(config=None):
    if config:
        conf = config
    else:
        conf = Config()
    base = ['service', 'monitoring', 'vmagent']
    if not conf.exists(base):
        return None

    vmagent = conf.get_config_dict(
        base, key_mangling=('-', '_'), get_first_key=True, with_recursive_defaults=True
    )

    if is_node_changed(conf, base):
        vmagent.update({'vmagent_restart_required': {}})

    return vmagent


def verify(vmagent):
    if not vmagent:
        return None

    verify_vrf(vmagent)


    if 'remote_write' not in vmagent:
        raise ConfigError(
            f'remote write not specified in vmagent'
        )

    if 'job' in vmagent:
        if "snmp_exporter" in vmagent:
            if "target" in vmagent["snmp_exporter"]:
                for target, target_config in vmagent["snmp_exporter"]["target"].items():
                    if "label" in target_config:
                        for label_name, label_config in target_config["label"].items():
                            if "value" not in label_config:
                                raise ConfigError(
                                    f'label value not specified in snmp-exporter target {target} label {label_name}'
                                )
                    else:
                        raise ConfigError(
                            f'label name not specified in snmp-exporter target {target}'
                        )
            else:
                raise ConfigError(
                    f'target not specified in snmp-exporter'
                )
    return None


def generate(vmagent):
    if not vmagent:
        # Delete systemd files
        if os.path.isfile(vmagent_service_file):
            os.unlink(vmagent_service_file)
        return None


    # Render blackbox_exporter service_file
    render(
        vmagent_service_file,
        'prometheus/vmagent.service.j2',
        vmagent,
    )

    if 'job' in vmagent:
        # Render blackbox_exporter config file
        render(
            '/run/vmagent/prometheus.yml',
            'prometheus/vmagent-prometheus.yml.j2',
            vmagent,
        )

        if "snmp_exporter" in vmagent["job"]:
            render(
            '/run/vmagent/snmp-file_sd_config.yml',
            'prometheus/snmp-file_sd_config.yml.j2',
            vmagent['job']["snmp_exporter"],
        )

    return None


def apply(vmagent):
    # Reload systemd manager configuration
    call('systemctl daemon-reload')
    if not vmagent and process_named_running("vmagent"):
        call(f'systemctl stop {vmagent_systemd_service}')

    if not vmagent:
        return

    if process_named_running("vmagent"):
        url = f'http://127.0.0.1:8429/-/reload'
        r = requests.get(url)
    else:
        systemd_action = 'reload-or-restart'
        if 'vmagent_restart_required' in vmagent:
            systemd_action = 'restart'
        call(f'systemctl {systemd_action} {vmagent_systemd_service}')


if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        exit(1)

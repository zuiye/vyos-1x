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
import socket

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


def get_hostname() -> str:
    try:
        hostname = socket.getfqdn()
    except socket.gaierror:
        hostname = socket.gethostname()
    return hostname


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

    restart_required_list = ['global-label', 'listen-address', 'port','remote-write']
    for restart_node in restart_required_list:
        if is_node_changed(conf, base + [restart_node]):
            vmagent.update({'vmagent_restart_required': {}})
            break

    if not conf.exists(base + ['job', 'ping-exporter']):
        # vmagent 删除ping_exporter
        vmagent['job'].pop('ping_exporter', None)
    if not conf.exists(base + ['job', 'snmp-exporter']):
        # vmagent 删除snmp_exporter
        vmagent['job'].pop('snmp_exporter', None)

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
        # 获取hostname 作为global_label的一部分，方便在prometheus中区分不同的vyos设备
        hostname = get_hostname()
        if "global_label" not in vmagent:
            vmagent["global_label"] = {}
        vmagent["global_label"]["vyosName"] = {"value": hostname}
        # Render blackbox_exporter config file


        scrape_interval_dict = {}
        if "snmp_exporter" in vmagent["job"]:
            for target, target_config in vmagent["job"]["snmp_exporter"]["target"].items():
                scrape_interval = target_config["scrape_interval"]
                if scrape_interval not in scrape_interval_dict:
                    scrape_interval_dict[scrape_interval] = {}
                scrape_interval_dict[scrape_interval][target] = target_config

        scrape_interval_keys = list(scrape_interval_dict.keys())
        vmagent["scrape_interval_list"] = scrape_interval_keys

        render(
            '/run/vmagent/prometheus.yml',
            'prometheus/vmagent-prometheus.yml.j2',
            vmagent,
        )

        for scrape_interval, targets_dict in scrape_interval_dict.items():
            render(
                f'/run/vmagent/snmp-file_sd_config-{scrape_interval}.yml',
                'prometheus/snmp-file_sd_config.yml.j2',
                {
                    "targets_dict": targets_dict,
                    "scrape_interval": scrape_interval
                }
            )

        # else:
        #     render(
        #         '/run/vmagent/snmp-file_sd_config.yml',
        #         'prometheus/snmp-file_sd_config.yml.j2',
        #         {},
        #     )


    return None


def apply(vmagent):
    # Reload systemd manager configuration
    call('systemctl daemon-reload')
    if not vmagent and process_named_running("vmagent"):
        call(f'systemctl stop {vmagent_systemd_service}')

    if not vmagent:
        return

    if 'vmagent_restart_required' in vmagent:
        call(f'systemctl restart {vmagent_systemd_service}')
    else:
        url = f'http://127.0.0.1:8429/-/reload'
        r = requests.get(url)
        if r.status_code != 200:
            print(f'Failed to reload vmagent configuration, status code: {r.status_code}')



if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        exit(1)

"""Parser for passive BLE advertisements."""
import logging

from .atc import parse_atc
from .bluemaestro import parse_bluemaestro
from .brifit import parse_brifit
from .govee import parse_govee
from .kegtron import parse_kegtron
from .miscale import parse_miscale
from .inode import parse_inode
from .moat import parse_moat
from .qingping import parse_qingping
from .ruuvitag import parse_ruuvitag
from .sensorpush import parse_sensorpush
from .teltonika import parse_teltonika
from .thermoplus import parse_thermoplus
from .xiaomi import parse_xiaomi
from .xiaogui import parse_xiaogui

_LOGGER = logging.getLogger(__name__)


class BleParser:
    """Parser for BLE advertisements"""
    def __init__(
        self,
        report_unknown=False,
        discovery=True,
        filter_duplicates=False,
        sensor_whitelist=[],
        tracker_whitelist=[],
        aeskeys={}
    ):
        self.report_unknown = report_unknown
        self.discovery = discovery
        self.filter_duplicates = filter_duplicates
        self.sensor_whitelist = sensor_whitelist
        self.tracker_whitelist = tracker_whitelist
        self.aeskeys = aeskeys

        self.lpacket_ids = {}
        self.movements_list = {}
        self.adv_priority = {}

    def parse_data(self, data):
        """Parse the raw data."""
        # check if packet is Extended scan result
        is_ext_packet = True if data[3] == 0x0D else False
        # check for no BR/EDR + LE General discoverable mode flags
        adpayload_start = 29 if is_ext_packet else 14
        # https://www.silabs.com/community/wireless/bluetooth/knowledge-base.entry.html/2017/02/10/bluetooth_advertisin-hGsf
        try:
            adpayload_size = data[adpayload_start - 1]
        except IndexError:
            return None, None
        # check for BTLE msg size
        msg_length = data[2] + 3
        if (
            msg_length <= adpayload_start or msg_length != len(data) or msg_length != (
                adpayload_start + adpayload_size + (0 if is_ext_packet else 1)
            )
        ):
            return None, None
        # extract RSSI byte
        rssi_index = 18 if is_ext_packet else msg_length - 1
        rssi = data[rssi_index]
        # strange positive RSSI workaround
        if rssi > 127:
            rssi = rssi - 256
        # MAC address
        mac = (data[8 if is_ext_packet else 7:14 if is_ext_packet else 13])[::-1]
        sensor_data = None

        while adpayload_size > 1:
            adstuct_size = data[adpayload_start] + 1
            if adstuct_size > 1 and adstuct_size <= adpayload_size:
                adstruct = data[adpayload_start:adpayload_start + adstuct_size]
                # https://www.bluetooth.com/specifications/assigned-numbers/generic-access-profile/
                adstuct_type = adstruct[1]
                if adstuct_type == 0x16 and adstuct_size > 4:
                    # AD type 'UUI16' https://www.bluetooth.com/specifications/assigned-numbers/
                    uuid16 = (adstruct[3] << 8) | adstruct[2]
                    # check for service data of supported manufacturers
                    if uuid16 == 0xFFF9 or uuid16 == 0xFDCD:  # UUID16 = Cleargrass or Qingping
                        sensor_data = parse_qingping(self, adstruct, mac, rssi)
                        break
                    elif uuid16 == 0x181A:  # UUID16 = ATC
                        sensor_data = parse_atc(self, adstruct, mac, rssi)
                        break
                    elif uuid16 == 0xFE95:  # UUID16 = Xiaomi
                        sensor_data = parse_xiaomi(self, adstruct, mac, rssi)
                        break
                    elif uuid16 == 0x181D or uuid16 == 0x181B:  # UUID16 = Mi Scale
                        sensor_data = parse_miscale(self, adstruct, mac, rssi)
                        break
                    elif uuid16 == 0xFEAA:  # UUID16 = Ruuvitag V2/V4
                        sensor_data = parse_ruuvitag(self, adstruct, mac, rssi)
                        break
                    elif uuid16 == 0x2A6E or uuid16 == 0x2A6F:  # UUID16 = Teltonika
                        # Teltonika can contain multiple sevice data payloads in one advertisement
                        sensor_data = parse_teltonika(self, data[adpayload_start:], mac, rssi)
                        break
                    else:
                        if self.report_unknown == "Other":
                            _LOGGER.info("Unknown advertisement received: %s", data.hex())
                elif adstuct_type == 0xFF:
                    # AD type 'Manufacturer Specific Data' with company identifier
                    # https://www.bluetooth.com/specifications/assigned-numbers/company-identifiers/
                    comp_id = (adstruct[3] << 8) | adstruct[2]
                    # check for service data of supported companies
                    if adstruct[0] == 0x1E and comp_id == 0xFFFF:  # Kegtron
                        sensor_data = parse_kegtron(self, adstruct, mac, rssi)
                        break
                    elif adstruct[0] == 0x15 and (comp_id == 0x0010 or comp_id == 0x0011):  # Thermoplus
                        sensor_data = parse_thermoplus(self, adstruct, mac, rssi)
                        break
                    elif adstruct[0] == 0x0C and comp_id == 0xEC88:  # Govee H5051
                        sensor_data = parse_govee(self, adstruct, mac, rssi)
                        break
                    elif adstruct[0] == 0x0A and comp_id == 0xEC88:  # Govee H5074
                        sensor_data = parse_govee(self, adstruct, mac, rssi)
                        break
                    elif adstruct[0] == 0x09 and comp_id == 0xEC88:  # Govee H5072/H5075
                        sensor_data = parse_govee(self, adstruct, mac, rssi)
                        break
                    elif adstruct[0] == 0x09 and comp_id == 0x0001:  # Govee H5101/H5102/H5177
                        sensor_data = parse_govee(self, adstruct, mac, rssi)
                        break
                    elif adstruct[0] == 0x0C and comp_id == 0x0001:  # Govee H5178
                        sensor_data = parse_govee(self, adstruct, mac, rssi)
                        break
                    elif adstruct[0] == 0x0C and comp_id == 0x8801:  # Govee H5179
                        sensor_data = parse_govee(self, adstruct, mac, rssi)
                        break
                    elif comp_id == 0x0499:  # Ruuvitag V3/V5
                        sensor_data = parse_ruuvitag(self, adstruct, mac, rssi)
                        break
                    elif adstruct[0] == 0x14 and (comp_id == 0xaa55):  # Brifit
                        sensor_data = parse_brifit(self, adstruct, mac, rssi)
                        break
                    elif adstruct[0] == 0x0E and adstruct[3] == 0x82:  # iNode
                        sensor_data = parse_inode(self, adstruct, mac, rssi)
                        break
                    elif adstruct[0] == 0x15 and comp_id == 0x1000:  # Moat S2
                        sensor_data = parse_moat(self, adstruct, mac, rssi)
                        break
                    elif adstruct[0] == 0x11 and comp_id == 0x0133:  # BlueMaestro
                        sensor_data = parse_bluemaestro(self, adstruct, mac, rssi)
                        break
                    elif adstruct[0] == 0x10 and adstruct[2] == 0xC0:  # Xiaogui Scale
                        sensor_data = parse_xiaogui(self, adstruct, mac, rssi)
                        break
                    else:
                        if self.report_unknown == "Other":
                            _LOGGER.info("Unknown advertisement received: %s", data.hex())
                elif adstuct_type == 0x06 and adstuct_size > 16:
                    sensorpush_uuid_reversed = b'\xb0\x0a\x09\xec\xd7\x9d\xb8\x93\xba\x42\xd6\x11\x00\x00\x09\xef'
                    if str(adstruct[2:]) == str(sensorpush_uuid_reversed):
                        sensor_data = parse_sensorpush(self, data[adpayload_start:], mac, rssi)
                        break
                    else:
                        if self.report_unknown == "Other":
                            _LOGGER.info("Unknown advertisement received: %s", data.hex())
                else:
                    if self.report_unknown == "Other":
                        _LOGGER.info("Unknown advertisement received: %s", data.hex())
                    sensor_data = None
            adpayload_size -= adstuct_size
            adpayload_start += adstuct_size

        # check for monitored device trackers
        if mac in self.tracker_whitelist:
            tracker_data = {
                "is connected": True,
                "mac": ''.join('{:02X}'.format(x) for x in mac),
                "rssi": rssi,
            }
        else:
            tracker_data = None

        return sensor_data, tracker_data

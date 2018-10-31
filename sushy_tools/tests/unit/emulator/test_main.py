#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json

from oslotest import base
from six.moves import mock

from sushy_tools.emulator import main


@mock.patch('sushy_tools.emulator.main.driver', autospec=True)
class EmulatorTestCase(base.BaseTestCase):

    def setUp(self):
        main.driver = None
        self.app = main.app.test_client()

        super(EmulatorTestCase, self).setUp()

    def test_systems_by_name(self, driver_mock):
        type(driver_mock).systems = mock.PropertyMock(return_value=[
            {'name': 'host0', 'uuid': 'b9fbc4f5-2c81-4c80-97ea-272621fb7360'},
            {'name': 'host1', 'uuid': 'b9fbc4f5-2c81-4c80-97ea-272621fb7361'}])

        response = self.app.get('/redfish/v1/Systems')

        self.assertEqual('200 OK', response.status)
        self.assertEqual(2, response.json['Members@odata.count'])
        self.assertEqual(
            [{'@odata.id': '/redfish/v1/Systems/host0'},
             {'@odata.id': '/redfish/v1/Systems/host1'}],
            response.json['Members'])

    @mock.patch.object(main, 'ADVERTISE_SYSTEM_UUID', '1')
    def test_systems_by_uuid(self, driver_mock):
        type(driver_mock).systems = mock.PropertyMock(return_value=[
            {'name': 'host0', 'uuid': 'b9fbc4f5-2c81-4c80-97ea-272621fb7360'},
            {'name': 'host1', 'uuid': 'b9fbc4f5-2c81-4c80-97ea-272621fb7361'}])

        response = self.app.get('/redfish/v1/Systems')

        self.assertEqual('200 OK', response.status)
        self.assertEqual(2, response.json['Members@odata.count'])
        self.assertEqual(
            [{'@odata.id': '/redfish/v1/Systems/'
                           'b9fbc4f5-2c81-4c80-97ea-272621fb7360'},
             {'@odata.id': '/redfish/v1/Systems/'
                           'b9fbc4f5-2c81-4c80-97ea-272621fb7361'}],
            response.json['Members'])

    def test_bios(self, driver_mock):
        driver_mock.get_bios.return_value = {"attribute 1": "value 1",
                                             "attribute 2": "value 2"}
        response = self.app.get('/redfish/v1/Systems/xxxx-yyyy-zzzz/BIOS')

        self.assertEqual('200 OK', response.status)
        self.assertEqual('BIOS', response.json['Id'])
        self.assertEqual({"attribute 1": "value 1",
                          "attribute 2": "value 2"},
                         response.json['Attributes'])

    def test_bios_settings(self, driver_mock):
        driver_mock.get_bios.return_value = {"attribute 1": "value 1",
                                             "attribute 2": "value 2"}
        response = self.app.get(
            '/redfish/v1/Systems/xxxx-yyyy-zzzz/BIOS/Settings')

        self.assertEqual('200 OK', response.status)
        self.assertEqual('Settings', response.json['Id'])
        self.assertEqual({"attribute 1": "value 1",
                          "attribute 2": "value 2"},
                         response.json['Attributes'])

    def test_bios_settings_patch(self, driver_mock):
        self.app.driver = driver_mock
        response = self.app.patch(
            '/redfish/v1/Systems/xxxx-yyyy-zzzz/BIOS/Settings',
            data=json.dumps({'Attributes': {'key': 'value'}}),
            content_type='application/json')

        self.assertEqual('204 NO CONTENT', response.status)
        driver_mock.set_bios.assert_called_once_with('xxxx-yyyy-zzzz',
                                                     {'key': 'value'})

    def test_reset_bios(self, driver_mock):
        self.app.driver = driver_mock
        response = self.app.post('/redfish/v1/Systems/xxxx-yyyy-zzzz/'
                                 'BIOS/Actions/Bios.ResetBios')

        self.assertEqual('204 NO CONTENT', response.status)
        driver_mock.reset_bios.assert_called_once_with('xxxx-yyyy-zzzz')

    def test_ethernet_interfaces_collection(self, driver_mock):
        driver_mock.get_nics.return_value = [{'id': 'nic1',
                                              'mac': '52:54:00:4e:5d:37'},
                                             {'id': 'nic2',
                                              'mac': '00:11:22:33:44:55'}]
        response = self.app.get('redfish/v1/Systems/xxx-yyy-zzz/'
                                'EthernetInterfaces')

        self.assertEqual('200 OK', response.status)
        self.assertEqual('Ethernet Interface Collection',
                         response.json['Name'])
        self.assertEqual(2, response.json['Members@odata.count'])
        self.assertEqual(['/redfish/v1/Systems/xxx-yyy-zzz/'
                          'EthernetInterfaces/nic1',
                          '/redfish/v1/Systems/xxx-yyy-zzz/'
                          'EthernetInterfaces/nic2'],
                         [m['@odata.id'] for m in response.json['Members']])

    def test_ethernet_interfaces_collection_empty(self, driver_mock):
        driver_mock.get_nics.return_value = []
        response = self.app.get('redfish/v1/Systems/xxx-yyy-zzz/'
                                'EthernetInterfaces')

        self.assertEqual('200 OK', response.status)
        self.assertEqual('Ethernet Interface Collection',
                         response.json['Name'])
        self.assertEqual(0, response.json['Members@odata.count'])
        self.assertEqual([], response.json['Members'])

    def test_ethernet_interface(self, driver_mock):
        driver_mock.get_nics.return_value = [{'id': 'nic1',
                                              'mac': '52:54:00:4e:5d:37'},
                                             {'id': 'nic2',
                                              'mac': '00:11:22:33:44:55'}]
        response = self.app.get('/redfish/v1/Systems/xxx-yyy-zzz/'
                                'EthernetInterfaces/nic2')

        self.assertEqual('200 OK', response.status)
        self.assertEqual('nic2', response.json['Id'])
        self.assertEqual('VNIC nic2', response.json['Name'])
        self.assertEqual('00:11:22:33:44:55',
                         response.json['PermanentMACAddress'])
        self.assertEqual('00:11:22:33:44:55',
                         response.json['MACAddress'])
        self.assertEqual('/redfish/v1/Systems/xxx-yyy-zzz/'
                         'EthernetInterfaces/nic2',
                         response.json['@odata.id'])

    def test_ethernet_interface_not_found(self, driver_mock):
        driver_mock.get_nics.return_value = [{'id': 'nic1',
                                              'mac': '52:54:00:4e:5d:37'},
                                             {'id': 'nic2',
                                             'mac': '00:11:22:33:44:55'}]
        response = self.app.get('/redfish/v1/Systems/xxx-yyy-zzz/'
                                'EthernetInterfaces/nic3')

        self.assertEqual('404 NOT FOUND', response.status)

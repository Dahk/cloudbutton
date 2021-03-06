#
# Copyright IBM Corp. 2020
# Copyright Cloudlab URV 2020
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

def load_config(config_data):
    if 'swift' not in config_data:
        raise Exception("swift section is mandatory in the configuration")

    required_parameters = ('auth_url', 'user_id', 'project_id', 'password', 'region')

    if set(required_parameters) <= set(config_data['swift']):
        pass
    else:
        raise Exception('You must provide {} to access to Swift'.format(required_parameters))

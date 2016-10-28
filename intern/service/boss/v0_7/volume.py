﻿# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from intern.service.boss import BaseVersion
from intern.service.boss.v0_7 import BOSS_API_VERSION
from intern.resource.boss.resource import *
from requests import HTTPError
import blosc
import numpy as np


class VolumeService_0_7(BaseVersion):
    def __init__(self):
        BaseVersion.__init__(self)

    @property
    def version(self):
        """Return the API Version for this implementation
        """
        return BOSS_API_VERSION

    def get_bit_width(self, resource):
        """Method to return the bit width for blosc based on the Resource"""
        datatype = resource.datatype

        if ("uint" in datatype):
            bit_width = int(datatype.split("uint")[1])
        else:
            raise ValueError("Unsupported datatype: {}".format(datatype))

        return bit_width

    def cutout_create(
        self, resource, resolution, x_range, y_range, z_range, time_range, numpyVolume,
        url_prefix, auth, session, send_opts):
        """Upload a cutout to the Boss data store.

        Args:
            resource (intern.resource.resource.Resource): Resource compatible with cutout operations.
            resolution (int): 0 indicates native resolution.
            x_range (list[int]): x range such as [10, 20] which means x>=10 and x<20.
            y_range (list[int]): y range such as [10, 20] which means y>=10 and y<20.
            z_range (list[int]): z range such as [10, 20] which means z>=10 and z<20.
            time_range (optional [list[int]]): time range such as [30, 40] which means t>=30 and t<40.
            numpyVolume (numpy.array): A 3D or 4D (time) numpy matrix in (time)ZYX order.
            url_prefix (string): Protocol + host such as https://api.theboss.io
            auth (string): Token to send in the request header.
            session (requests.Session): HTTP session to use for request.
            send_opts (dictionary): Additional arguments to pass to session.send().
        """
        compressed = blosc.compress(numpyVolume, typesize=self.get_bit_width(resource))

        if numpyVolume.ndim == 3:
            # Can't have time
            if time_range is not None:
                raise ValueError(
                    "You must provide a 4D matrix if specifying a time range")
        elif numpyVolume.ndim == 4:
            # must have time
            if time_range is None:
                raise ValueError(
                    "You must specifying a time range if providing a 4D matrix")
        else:
            raise ValueError(
                "Invalid data format. Only 3D or 4D cutouts are supported. Number of dimensions: {}".format(
                    numpyVolume.ndim))

        req = self.get_cutout_request(
            resource, 'POST', 'application/blosc',
            url_prefix, auth,
            resolution, x_range, y_range, z_range, time_range, compressed)
        prep = session.prepare_request(req)
        resp = session.send(prep, **send_opts)

        if resp.status_code == 201:
            return

        msg = ('Create cutout failed on {}, got HTTP response: ({}) - {}'.format(
            resource.name, resp.status_code, resp.text))
        raise HTTPError(msg, request=req, response=resp)

    def cutout_get(
        self, resource, resolution, x_range, y_range, z_range, time_range,
        url_prefix, auth, session, send_opts):
        """Upload a cutout to the Boss data store.

        Args:
            resource (intern.resource.resource.Resource): Resource compatible with cutout operations.
            resolution (int): 0 indicates native resolution.
            x_range (list[int]): x range such as [10, 20] which means x>=10 and x<20.
            y_range (list[int]): y range such as [10, 20] which means y>=10 and y<20.
            z_range (list[int]): z range such as [10, 20] which means z>=10 and z<20.
            time_range (optional [list[int]]): time range such as [30, 40] which means t>=30 and t<40.
            url_prefix (string): Protocol + host such as https://api.theboss.io
            auth (string): Token to send in the request header.
            session (requests.Session): HTTP session to use for request.
            send_opts (dictionary): Additional arguments to pass to session.send().

        Returns:
            (numpy.array): A 3D or 4D numpy matrix in ZXY(time) order.

        Raises:
            requests.HTTPError
        """

        req = self.get_cutout_request(
            resource, 'GET', 'application/blosc',
            url_prefix, auth, resolution, x_range, y_range, z_range, time_range)
        prep = session.prepare_request(req)
        # Hack in Accept header for now.
        prep.headers['Accept'] = 'application/blosc'
        resp = session.send(prep, **send_opts)

        if resp.status_code == 200:
            raw_data = blosc.decompress(resp.content)
            data_mat = np.fromstring(raw_data, dtype=resource.datatype)

            if time_range:
                # Reshape including time
                return np.reshape(data_mat,
                                  (time_range[1] - time_range[0],
                                   z_range[1] - z_range[0],
                                   y_range[1] - y_range[0],
                                   x_range[1] - x_range[0]),
                                  order='C')
            else:
                # Reshape without including time
                return np.reshape(data_mat,
                                  (z_range[1] - z_range[0],
                                   y_range[1] - y_range[0],
                                   x_range[1] - x_range[0]),
                                  order='C')

        msg = ('Get cutout failed on {}, got HTTP response: ({}) - {}'.format(
            resource.name, resp.status_code, resp.text))
        raise HTTPError(msg, request=req, response=resp)
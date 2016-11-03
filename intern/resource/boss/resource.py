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
from intern.resource import Resource
from abc import abstractmethod


class BossResource(Resource):
    """Base class for Boss resources.

    Attributes:
        name (string): Name of resource.  Used as identifier when talking to
        the Boss API.
        description (string): Text description of resource.
        creator (string): Resource creator.
        raw (dictionary): Holds JSON data returned by the Boss API on a POST (create) or GET operation.
    """
    def __init__(self, name, description, creator='', raw={}):
        """Constructor.

        Args:
            name (string): Name of resource.
            description (string): Description of resource.
            creator (optional[string]): Resource creator.
            raw (optional[dictionary]): Holds JSON data returned by the Boss API on a POST (create) or GET operation.
        """

        self.name = name
        self.description = description
        self.creator = creator
        self.raw = raw

    def valid_volume(self):
        return False

    @abstractmethod
    def get_route(self):
        """Get the route for resource.

        Returns:
            (string): A string that can be appended to the location of an
            endpoint such as 'mycollection/experiment/exp1/channel/chan2'
        """
        assert NotImplemented

    @abstractmethod
    def get_list_route(self):
        """Get the route for listing resources.

        Returns:
            (string): A string that can be appended to the location of an
            endpoint such as 'mycollection/experiment'
        """
        assert NotImplemented

    @abstractmethod
    def get_cutout_route(self):
        """Get the route for cutout operations.

        Not all resources will support this operation.

        Returns:
            (string): A string that can be used as part of a URL.

        Raises:
            (RuntimeError): if operation not supported by the resource.
        """
        assert NotImplemented

    @abstractmethod
    def get_meta_route(self):
        """Get the route for metadata operations.

        Not all resources will support this operation.

        Returns:
            (string): A string that can be used as part of a URL.

        Raises:
            (RuntimeError): if operation not supported by the resource.
        """
        assert NotImplemented

    @abstractmethod
    def get_dict_route(self):
        """Get the route in dictionary form.

        Not all resources will support this operation.

        Returns:
            (dict): A dictionary containing the names of the resource components

        Raises:
            (RuntimeError): if operation not supported by the resource.
        """
        assert NotImplemented


class CollectionResource(BossResource):
    """Top level container for Boss projects.
    """
    def __init__(
        self, name, description='', creator='', raw={}):
        """Constructor.

        Args:
            name (string): Collection name.
            description (optional[string]): Collection description.  Defaults to empty.
            creator (optional[string]): Resource creator.
            raw (optional[dictionary]): Holds JSON data returned by the Boss API on a POST (create) or GET operation.
        """
        BossResource.__init__(self, name, description, creator, raw)

    def get_route(self):
        return self.name

    def get_list_route(self):
        return ''

    def get_cutout_route(self):
        raise RuntimeError('Not supported for collections.')

    def get_meta_route(self):
        return self.name

    def get_dict_route(self):
        return {"collection": self.name}


class ExperimentResource(BossResource):
    """Experiments reside inside a collection and contain channels and
    layers.

    Attributes:
        _coord_frame (string):
        num_hierarchy_levels (int):
        hierarchy_method (string):
        max_time_sample (int):
    """
    def __init__(self, name, collection_name, coord_frame, description='',
        num_hierarchy_levels=1, hierarchy_method='near_iso',
        max_time_sample=0, creator='', raw={}):
        """Constructor.

        Args:
            name (string): Experiment name.
            collection_name (string): Collection name.
            coord_frame (string): Name of coordinate frame used by experiment.
            description (optional[string]): Experiment description.  Defaults to empty.
            num_hierarchy_levels (optional[int]): Defaults to 1.
            hierarchy_method (optional[string]): 'near_iso', 'iso', 'slice'  Defaults to 'near_iso'.
            max_time_sample (optional[int]): Maximum number of time samples for any time series data captured by this experiment.
            creator (optional[string]): Resource creator.
            raw (optional[dictionary]): Holds JSON data returned by the Boss API on a POST (create) or GET operation.
        """

        BossResource.__init__(self, name, description, creator, raw)
        self.coll_name = collection_name

        self._valid_hierarchy_methods = ['near_iso', 'iso', 'slice']

        #ToDo: validate data types.
        self._coord_frame = coord_frame
        self.num_hierarchy_levels = num_hierarchy_levels
        self._hierarchy_method = self.validate_hierarchy_method(
            hierarchy_method)
        self.max_time_sample = max_time_sample

    @property
    def coord_frame(self):
        return self._coord_frame

    @property
    def hierarchy_method(self):
        return self._hierarchy_method

    @hierarchy_method.setter
    def hierarchy_method(self, value):
        """
        Args:
            value (string): Valid values: 'near_iso', 'iso', 'slice'
        Raises:
            ValueError
        """
        self._hierarchy_method = self.validate_hierarchy_method(value)

    def get_route(self):
        return self.coll_name + '/experiment/' + self.name

    def get_list_route(self):
        return self.coll_name + '/experiment/'

    def get_cutout_route(self):
        raise RuntimeError('Not supported for experiments.')

    def get_meta_route(self):
        return self.coll_name + '/' + self.name

    def validate_hierarchy_method(self, value):
        lowered = value.lower()
        if lowered in self._valid_hierarchy_methods:
            return lowered
        raise ValueError('{} is not a valid hierarchy method.'.format(value))

    def get_dict_route(self):
        return {"collection": self.coll_name, "experiment": self.name}


class CoordinateFrameResource(BossResource):
    """
    Coordinate frame used by experiment(s).

    For all ranges, the _stop value is exclusive.  This means valid values will be _less than_ the stop value.

    Attributes:
        name (string): Coordinate frame name.
        description (string): Coordinate frame description.  Defaults to empty.
        x_start (int): Minimum x coordinate (defaults to 0).
        x_stop (int): Maximum x coordinate - exclusive (defaults to 1).
        y_start (int): Minimum y coordinate (defaults to 0).
        y_stop (int): Maximum y coordinate - exclusive (defaults to 1).
        z_start (int): Minimum z coordinate (defaults to 0).
        z_stop (int): Maximum z coordinate - exclusive (defaults to 1).
        x_voxel_size (int): Defaults to 1.
        y_voxel_size (int): Defaults to 1.
        z_voxel_size (int): Defaults to 1.
        voxel_unit (string): 'nanometers', 'micrometers', 'millimeters', 'centimeters'.  Defaults to 'nanometers'.
        time_step (int): Defaults to 0.
        time_step_unit (string): 'nanoseconds', 'microseconds', 'milliseconds', 'seconds'.  Defaults to 'seconds'.
    """
    def __init__(
        self, name, description='',
        x_start=0, x_stop=1, y_start=0, y_stop=1, z_start=0, z_stop=1,
        x_voxel_size=1, y_voxel_size=1, z_voxel_size=1, voxel_unit='nanometers',
        time_step=0, time_step_unit='seconds', creator='', raw={}):
        """Constructor.

        For all ranges, the _stop value is exclusive.  This means valid values will be _less than_ the stop value.

        Args:
            name (string): Coordinate frame name.
            description (optional[string]): Coordinate frame description.  Defaults to empty.
            x_start (optional[int]): Minimum x coordinate (defaults to 0).
            x_stop (optional[int]): Maximum x coordinate - exclusive (defaults to 1).
            y_start (optional[int]): Minimum y coordinate (defaults to 0).
            y_stop (optional[int]): Maximum y coordinate - exclusive (defaults to 1).
            z_start (optional[int]): Minimum z coordinate (defaults to 0).
            z_stop (optional[int]): Maximum z coordinate - exclusive (defaults to 1).
            x_voxel_size (optional[int]): Defaults to 1.
            y_voxel_size (optional[int]): Defaults to 1.
            z_voxel_size (optional[int]): Defaults to 1.
            voxel_unit (optional[string]): 'nanometers', 'micrometers', 'millimeters', 'centimeters'.  Defaults to 'nanometers'.
            time_step (optional[int]): Defaults to 0.
            time_step_unit (optional[string]): 'nanoseconds', 'microseconds', 'milliseconds', 'seconds'.  Defaults to 'seconds'.
            creator (optional[string]): Resource creator.
            raw (optional[dictionary]): Holds JSON data returned by the Boss API on a POST (create) or GET operation.
        """

        BossResource.__init__(self, name, description, raw=raw)

        self._valid_voxel_units = [
            'nanometers', 'micrometers', 'millimeters', 'centimeters']

        self._valid_time_units = [
            'nanoseconds', 'microseconds', 'milliseconds', 'seconds']

        self.x_start = x_start
        self.x_stop = x_stop
        self.y_start = y_start
        self.y_stop = y_stop
        self.z_start = z_start
        self.z_stop = z_stop
        self.x_voxel_size = x_voxel_size
        self.y_voxel_size = y_voxel_size
        self.z_voxel_size = z_voxel_size
        self._voxel_unit = self.validate_voxel_units(voxel_unit)
        self.time_step = time_step
        self._time_step_unit = self.validate_time_units(time_step_unit)

    def get_route(self):
        return self.name

    def get_list_route(self):
        return ''

    def get_cutout_route(self):
        raise RuntimeError('Not supported for coordinate frames.')

    def get_meta_route(self):
        raise RuntimeError('Not supported for coordinate frames.')

    @property
    def voxel_unit(self):
        return self._voxel_unit

    @voxel_unit.setter
    def voxel_unit(self, value):
        """
        Args:
            value (string): Valid values: 'nanometers', 'micrometers', 'millimeters', 'centimeters'
        Raises:
            ValueError
        """
        self._voxel_unit = self.validate_voxel_units(value)

    @property
    def time_step_unit(self):
        return self._time_step_unit

    @time_step_unit.setter
    def time_step_unit(self, value):
        """
        Args:
            value (string): 'nanoseconds', 'microseconds', 'milliseconds', 'seconds'
        Raises:
            ValueError
        """
        self._time_step_unit = self.validate_time_units(value)

    def validate_voxel_units(self, value):
        lowered = value.lower()
        if lowered in self._valid_voxel_units:
            return lowered
        raise ValueError('{} is not a valid voxel unit.'.format(value))

    def validate_time_units(self, value):
        lowered = value.lower()
        if lowered in self._valid_time_units:
            return lowered
        raise ValueError('{} is not a valid time unit.'.format(value))

    def get_dict_route(self):
        return {"coord": self.name}


class ChannelResource(BossResource):
    """
    Holds channel data.

    Attributes:
        coll_name (string): Name of collection containing this resource.
        exp_name (string): Name of experiment containing this resource.
        description (string): Description of channel or layer.
        default_time_step (int):
        base_resolution (int):
        _type (string): 'image' or 'annotation'
        _valid_datatypes (list[string]): Allowed data type values (static variable).
        _datatype (string):
    """

    _valid_datatypes = ['uint8', 'uint16', 'uint64']
    _valid_types = ['annotation', 'image']

    def __init__(self, name, collection_name, experiment_name, type,
        description='', default_time_step=0, datatype='uint8',
        base_resolution=0, sources=[], related=[], creator='', raw={}):
        """Constructor.

        Args:
            name (string): Channel name.
            collection_name (string): Parent collection name.
            experiment_name (string): Parent experiment name.
            type (string): 'image' or 'annotation'
            description (optional[string]): Layer description.  Defaults to empty.
            default_time_step (optional[int]): Defaults to 0.
            datatype (optional[string]): 'uint8', 'uint16', 'uint64'  Defaults to 'uint8'.
            base_resolution (optional[int]): Defaults to 0 (native).
            sources (optional[list[string]]): Channels this channel was derived from.
            related (optiona[list[string]]): Channels related to this channel.
            creator (optional[string]): Resource creator.
            raw (optional[dictionary]): Holds JSON data returned by the Boss API on a POST (create) or GET operation.
        """

        BossResource.__init__(self, name, description, creator, raw)
        self.coll_name = collection_name
        self.exp_name = experiment_name

        self._type = self.validate_type(type)
        self._datatype = self.validate_datatype(datatype)

        self.sources = sources

        self.related = related

        #ToDo: validate data types.
        self.default_time_step = default_time_step
        self.base_resolution = base_resolution

    def get_route(self):
        return self.coll_name + '/experiment/' + self.exp_name + '/channel/' + self.name

    def get_list_route(self):
        return self.coll_name + '/experiment/' + self.exp_name + '/channel/'

    def get_cutout_route(self):
        return self.coll_name + '/' + self.exp_name + '/' + self.name

    def get_meta_route(self):
        return self.coll_name + '/' + self.exp_name + '/' + self.name

    def valid_volume(self):
        """Channels and layers are valid resources for interacting with the volume service.
        """
        return True

    @property
    def sources(self):
        return self._sources

    @sources.setter
    def sources(self, value):
        if isinstance(value, str):
            self._sources = [value]
        else:
            self._sources = value

    @property
    def related(self):
        return self._related

    @related.setter
    def related(self, value):
        if isinstance(value, str):
            self._related = [value]
        else:
            self._related = value

    @property
    def type(self):
        """Channel type.

        Returns:
            (string)
        """
        return self._type

    @type.setter
    def type(self, value):
        """
        Args:
            value (string): 'image', 'annotation'
        Raises:
            ValueError
        """
        self._type = self.validate_type(value)

    @property
    def datatype(self):
        """Channel bit depth.

        Returns:
            (string)
        """
        return self._datatype

    @datatype.setter
    def datatype(self, value):
        """
        Args:
            value (string): 'uint8', 'uint16', 'uint64'
        Raises:
            ValueError
        """
        self._datatype = self.validate_datatype(value)

    def validate_type(self, value):
        lowered = value.lower()
        if lowered in ChannelResource._valid_types:
            return lowered
        raise ValueError('{} is not a valid type.'.format(value))

    def validate_datatype(self, value):
        lowered = value.lower()
        if lowered in ChannelResource._valid_datatypes:
            return lowered
        raise ValueError('{} is not a valid data type.'.format(value))

    def get_dict_route(self):
        return {"collection": self.coll_name, "experiment": self.exp_name, "channel": self.name}

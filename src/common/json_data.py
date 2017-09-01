"""
json_data module provides base class for generic serialization/deserialiation
of derived classes with elementaty type checking.

Example:
import json%data as jd

class Animal(jd.JsonData, config={}):
    def __init__():

        self.n_legs = 4       # Default value, type given implicitely, optional on input.
        self.n_legs = int     # Just type, input value obligatory
        self.length = float   # floats are initializble also from ints

        self.head = Chicken   # Construct Chicken form the value
        self.head = jd.Factory({ Chicken, Duck, Goose}) # construct one of given types according to '__class__' key on input

        self.
        def_head = Chicken(dict( chicken_color: "brown") )
        self.head = jd.Factory([Chicken, Duck, Goose], default =def_head)


        super().__init__(config, fill_attrs = []) # run deserialization and checks
        # By default all public attributes (not starting with underscore) are
        # initialized. Alternatively the list of attributes may be provided by the fill_attrs parameter.



class Chicken(Animal):
    # explicit specification of attributes to serialize/deserialize.
    __serialized_attrs__ = [ color, tail ]

    def __init__():
        def.color = 0
        def.wing = 1 # not serialized

TODO:
- Is __init__ the best place to specify types and do deserialization as well?
  We have no way to initialize private attributes (not accesible from input, but known at construction time of the class
  - object created dynamicaly at run time.
  Possibly we can convert this deserialization init into static factory method:

  @class
  def deserialize( cls, config ):
        x = cls.__new__()
        x.n_legs = 4
        # other type definitions
        super().deserialize(x, config )
        return x
"""
#import json


#
#
# TODO:
#  - example of child classes
#  - support both types and default values in declaration of serializable attrs
#

from enum import IntEnum
import inspect






class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class WrongKeyError(Error):
    """Raised when attempt assign data to key that not exist"""
    def __init__(self, key):
        self.key = key

    def __str__(self):
        return "'{}'".format(self.key)


class ClassFactory:
    """
    Helper class for JsonData.
    """
    def __init__(self, class_list):
        """
        Initialize list of possible classes.
        :param class_list:
        """
        if type(class_list) != list:
            class_list = [ class_list ]

        self.class_list = class_list

    def make_instance(self, config):
        """
        Make instance from config dict.
        Dict must contain item "__class__" with name of desired class.
        Desired class must be in class_list.
        :param config:
        :return:
        """
        assert config.__class__ is dict, "Expecting dict instead of: \n{}".format(config)

        if len(self.class_list) == 1 and  not "__class__" in config:
            config["__class__"] = self.class_list[0].__name__

        assert "__class__" in config

        for c in self.class_list:
            if c.__name__ == config["__class__"]:
                config = config.copy()
                del config["__class__"]
                try:
                    return c(config)
                except TypeError:
                    raise TypeError("Non-standard JsonData constructor for class: {}".format(c))
        assert False, "Input class: {} not in the factory list: {} ".format(config["__class__"], self.class_list)

class ClassFromList(ClassFactory):
    def __init__(self, class_name):
        assert issubclass(class_name, JsonData)
        self.class_name = clase_name

    def make_instance(self, config):
        """
        Make instance from config dict.
        Dict must contain item "__class__" with name of desired class.
        Desired class must be in class_list.
        :param config:
        :return:
        """
        assert config.__class__ is list
        return class_name(config)


class JsonData:


    """
    Abstract base class for various data classes.
    These classes are basically just documented dictionaries,
    which are JSON serializable and provide some syntactic sugar
    (see DotDict from Flow123d - Jan Hybs)
    In order to simplify also serialization of non-data classes, we
    should implement serialization of __dict__.

    Why use JSON for serialization? (e.g. instead of pickle)
    We want to use it for both sending the data and storing them in files,
    while some of these files should be human readable/writable.

    Serializable classes will be derived from this one. And data members
    that should not be serialized are prefixed by '_'.

    If list of serialized attributes is provided to constructor,
    these attributes are serialized no matter if prefixed by '_' or not.

    ?? Anything similar in current JobPanel?
    """

    __serialized__attrs___ = []
    """ List of attributes to serilaize. Leave empty to use public attributes."""

    def __init__(self, config):
        """
        Initialize class dict from config serialization.
        :param config: config dict
        :param serialized_attr: list of serialized attributes
        """
        if not hasattr(self, '__serialized_attrs__'):
            filter_attrs = [ key  for key in self.__dict__.keys() if key[0] == "_" ]
        else:
            filter_attrs = [ key for key in self.__dict__.keys() if key not in self.__serialized__attrs__ ]

        try:
            self._deserialize_dict(self.__dict__, config, filter_attrs)
        except WrongKeyError:
            raise WrongKeyError("Unknown attrs in initialization of class {}".format(self.__class__))


    @staticmethod
    def _deserialize_dict(template_dict, config_dict,  skip_attrs):
        for key, temp in template_dict.items():
            if key in skip_attrs:
                continue
            value = config_dict.get(key, temp)
            del config_dict[key]

            if inspect.isclass(temp):
                # just type given
                assert not inspect.isclass(value), "Missing value for obligatory key '{}' of type: {}.".format(key, temp)
                filled_template = JsonData._deserialize_item(temp, value)
            else:
                # given default value
                filled_template = JsonData._deserialize_item(temp.__class__, value)

            template_dict[key] = filled_template

        if config_dict.keys():
            raise WrongKeyError("Keys {} not serializable attrs of dict:\n{}"
                                .format(config_dict.keys(), template_dict))


    @staticmethod
    def _deserialize_item(temp, value):
        """
        Deserialize value.


        :param temp: template for assign value, just type for scalar types, dafualt value already assigned to value.
        :param value: value for deserialization
        :return:
        """

        # No check.
        if temp is None:
            return temp
        elif isinstance(temp, dict):
            JsonData._deserialize_dict(temp, value, [])
            return temp

        # list,
        elif isinstance(temp, list):
            assert value.__class__ is list
            l = []
            if len(temp) == 0:
                l=value
            elif len(temp) == 1:
                for v in value:
                    l.append(JsonData._deserialize_item(temp[0], v))
            else:
                print("Warning: Overwriting default list content:\n {}\n by:\n {}.".format(temp, value))
                l=value
            return l

        # tuple,
        elif isinstance(temp, tuple):
            assert value.__class__ is list, "Expecting list, get class: {}".format(value.__class__)
            assert len(temp) == len(value)
            l = []
            for i_temp, i_val in zip(temp, value):
                l.append(JsonData._deserialize_item(i_temp, i_val))
            return tuple(l)

        # ClassFactory - class given by '__class__' key.
        elif isinstance(temp, ClassFactory):
            return temp.make_instance(value)

        # JsonData default value, keep the type.
        elif isinstance(temp, JsonData):
            return ClassFactory(temp.__name__).make_instance(value)

        # other scalar types
        else:

            if issubclass(temp, IntEnum):
                if value.__class__ is str:
                    return temp[value]
                elif value.__class__ is int:
                    return temp(value)
                else:
                    assert False, "{} is not value of IntEnum: {}".format(value, temp)

            else:
                try:
                    filled_template = temp(value)
                except:
                    raise Exception("Can not convert value {} to type {}.".format(value, temp))
                return filled_template


    def serialize(self):
        """
        Serialize the object.
        :return:
        """
        return self._get_dict()

    def _get_dict(self):
        """Return dict for serialization."""
        d = {"__class__": self.__class__.__name__}
        for k, v in self.__dict__.items():
            if self._is_attr_serialized(k) and not isinstance(v, ClassFactory):
                d[k] = JsonData._serialize_object(v)
        return d

    @staticmethod
    def _serialize_object(obj):
        """Prepare object for serialization."""
        if isinstance(obj, JsonData):
            return obj._get_dict()
        elif isinstance(obj, IntEnum):
            return obj.name
        elif isinstance(obj, dict):
            d = {}
            for k, v in obj.items():
                d[k] = JsonData._serialize_object(v)
            return d
        elif isinstance(obj, list) or isinstance(obj, tuple):
            l = []
            for v in obj:
                l.append(JsonData._serialize_object(v))
            return l
        else:
            return obj

    # @staticmethod
    # def make_instance(config):
    #     """
    #     Make instance from config dict.
    #     Dict must contain item "__class__" with name of desired class.
    #     :param config:
    #     :return:
    #     """
    #     if "__class__" not in config:
    #         return None
    #
    #     # find class by name
    #     cn = config["__class__"]
    #     if cn in locals():
    #         c = locals()[cn]
    #     elif cn in globals():
    #         c = globals()[cn]
    #     else:
    #         return None
    #
    #     # instantiate class
    #     d = config.copy()
    #     del d["__class__"]
    #     return c(d)
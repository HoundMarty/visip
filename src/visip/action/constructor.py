import attr
import typing

from ..dev.base import _ActionBase
from ..dev import dtype as dtype
from ..dev.parameters import Parameters, ActionParameter



class Value(_ActionBase):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def hash(self):
        return data.hash(self.value)

    def _evaluate(self):
        return self.value

    def format(self, representer, action_name, arg_names):
        value = self.value
        if type(value) is str:
            expr = "'{}'".format(value)
        else:
            expr = str(value)

        return representer.format([expr])


class Pass(_ActionBase):
    """
    Do nothing action. Meant for internal usage in particular.
    """
    def __init__(self):
        super().__init__()

    def _evaluate(self, input: dtype.DataType):
        return input






class _ListBase(_ActionBase):
    """
    Base action class for actions accepting any number of unnamed parameters.
    """
    # We assume that parameters are used only in reinit, which do not use it
    # in this case. After reinit one should use only self.arguments.

    def __init__(self, action_name):
        super().__init__(action_name)
        self.parameters = Parameters()
        self.parameters.append(
            ActionParameter(name=None, type=typing.Any,
                                       default=self.parameters.no_default))


class list_constr(_ListBase):
    def __init__(self):
        super().__init__(action_name='list')

    def format(self, representer, action_name, arg_names):
        return representer.list("[", "]", [(None, arg) for arg in arg_names])

    def evaluate(self, inputs):
        return list(inputs)


class tuple_constr(_ListBase):
    """
    This action is necessary only for better typechecking, using fixed number of items
    of given type.
    """
    def __init__(self):
        super().__init__(action_name='tuple')

    def format(self, representer, action_name, arg_names):
        return representer.list("(", ")", [(None, arg) for arg in arg_names])

    def evaluate(self, inputs):
        return tuple(inputs)


class dict():
    def __init__(self):
        super().__init__()
        self.parameters = Parameters()
        self.parameters.append(ActionParameter(name=None, type=typing.Tuple[typing.Any, typing.Any], default=self.parameters.no_default))

    def format(self, representer, action_name, arg_names):
        # Todo: check that inputs are pairs, extract key/value
        #return format.Format.list("{", "}", [(None, arg) for arg in arg_names])

        return _ActionBase.format(representer, action_name, arg_names)



    def evaluate(self, inputs):
        return { key: val for key, val in inputs}





class ClassActionBase(_ActionBase):
    base_data_type = dtype.DataClassBase
    """
    Action constructs particular Dataclass given in constructor.
    So the action is parametrized by the 'data_class'.
    """
    def __init__(self, data_class):
        super().__init__(data_class.__name__)
        self._data_class = data_class
        self._module = self._data_class.__module__
        self._extract_input_type(func=data_class.__init__, skip_self=True)


    @staticmethod
    def construct_from_params(name: str, params: Parameters, module=None):
        """
        Use Params to consturct the data_class and then instance of ClassActionBase.
        :param name: name of the class
        :param params: instance of Parameters
        :return:
        """
        attributes = {}
        for param in params:
            attributes[param.name] = attr.ib(default=param.default, type=param.type)
        data_class = type(name, (dtype.DataClassBase,), attributes)
        if module:
            data_class.__module__ = module
        return ClassActionBase(attr.s(data_class))



    @staticmethod
    def construct_from_class(data_class):

        return


    @property
    def constructor(self):
        return self._data_class

    def _evaluate(self, *args) -> dtype.DataClassBase:
        return self._data_class(*args)


    def code_of_definition(self, representer, make_rel_name):
        """
        TODO:
        1. prefixin gfor typing.Any and other builtin types is wrong.
        2. need access to definitions of other classes.
        :param representer:
        :param make_rel_name:
        :return:
        """
        lines = ['@wf.Class']
        lines.append('class {}:'.format(self.name))
        for attribute in self.parameters:
            type_code = representer.type_code(attribute.type)
            type_str = make_rel_name(attribute.type.__module__, type_code)


            if attribute.default == self.parameters.no_default:
                default = ""
            else:
                default = "={}".format(attribute.default)
            lines.append("    {}:{}{}".format(attribute.name, type_str, default))

        return "\n".join(lines)


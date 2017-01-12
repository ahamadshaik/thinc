from numpy import prod
import contextlib

from .. import util
from ..train import Trainer
from ..exceptions import ShapeError
from ..ops import NumpyOps
from ..mem import Memory


class Model(object):
    '''Model base class.'''
    name = 'model'
    id = 0
    ops = NumpyOps('cpu')
    Trainer = Trainer
    descriptions = []
    on_data_hooks = []
    on_init_hooks = []
    _operators = {}

    @classmethod
    @contextlib.contextmanager
    def use_operators(cls, operators):
        '''Bind operators to specified functions for the scope of the context:

        Example
        -------

            model = Model()
            other = Model()
            with Model.use_operators({"+": lambda self, other: "plus"}):
                print(model + other)
                # "plus"
            print(model + other)
            # Raises exception --- binding limited to scope of with block.
        '''
        old_ops = dict(cls._operators)
        for op, func in cls.do.items():
            cls._operators[op] = func
        yield
        cls._operators = old_ops

    @classmethod
    @contextlib.contextmanager
    def use_device(cls, device):
        '''Change the device to execute on for the scope of the block.'''
        if device == cls.ops.device:
            yield
        else:
            curr_ops = cls.ops
            self.ops = get_ops(device)
            yield
            cls.ops = curr_ops

    def __init__(self, *args, **kwargs):
        Model.id += 1
        self.id = Model.id
        self.name = self.__class__.name
        kwargs = self._update_defaults(args, kwargs)
        self.mem = None
        self._layers = []
        self.descriptions = dict(self.descriptions)
        self.on_init_hooks = list(self.on_init_hooks)
        self.on_data_hooks = list(self.on_data_hooks)
        self.weights = []
        self.dims = []
        self.grads = []
        for attr, install in self.descriptions.items():
            install(attr, self)
        for hook in self.on_init_hooks:
            hook(self, *args, **kwargs)

    def _update_defaults(self, args, kwargs):
        new_kwargs = {}
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                new_kwargs[key] = value
        return new_kwargs

    def begin_training(self, train_X, train_Y):
        for hook in self.on_data_hooks:
            hook(self, train_X, train_Y)
        return self.Trainer(self, train_X, train_Y)
 
    def predict(self, X):
        y, _ = self.begin_update(X)
        return y
  
    def begin_update(self, X, **kwargs):
        self.check_input(X, expect_batch=True)
        callbacks = []
        for layer in self.layers:
            X = self.ops.xp.ascontiguousarray(X, dtype='f')
            X, inc_layer_grad = layer.begin_update(X)
            callbacks.append(inc_layer_grad)
        def continue_update(gradient):
            for callback in reversed(callbacks):
                gradient = callback(gradient)
            return gradient
        return X, continue_update

    def __add__(self, other):
        '''Apply the function bound to the '+' operator.'''
        return self._operators['+'](self, other)

    def __sub__(self, other):
        '''Apply the function bound to the '-' operator.'''
        return self._operators['-'](self, other)

    def __mul__(self, other):
        '''Apply the function bound to the '*' operator.'''
        return self._operators['*'](self, other)

    def __matmul__(self, other):
        '''Apply the function bound to the '@' operator.'''
        return self._operators['@'](self, other)

    def __truediv__(self, other):
        '''Apply the function bound to the '/' operator.'''
        return self._operators['/'](self, other)

    def __floordiv__(self, other):
        '''Apply the function bound to the '//' operator.'''
        return self._operators['//'](self, other)

    def __mod__(self, other):
        '''Apply the function bound to the '%' operator.'''
        return self._operators['%'](self, other)

    def __pow__(self, other, modulo=None):
        '''Apply the function bound to the '**' operator.'''
        return self._operators['**'](self, other)

    def __lshift__(self, other):
        '''Apply the function bound to the '<<' operator.'''
        return self._operators['<<'](self, other)

    def _rshift__(self, other):
        '''Apply the function bound to the '>>' operator.'''
        return self._operators['>>'](self, other)

    def __and__(self, other):
        '''Apply the function bound to the '&' operator.'''
        return self._operators['&'](self, other)

    def __xor__(self, other):
        '''Apply the function bound to the '^' operator.'''
        return self._operators['^'](self, other)

    def __or__(self, other):
        '''Apply the function bound to the '|' operator.'''
        return self._operators['|'](self, other)

#
#    def predict_one(self, x):
#        X = self.ops.expand_dims(x, axis=0)
#        return self.predict_batch(X)[0]
#
#
##    
#    def pipe(self, stream, batch_size=1000):
#        for batch in util.minibatch(stream, batch_size):
#            ys = self.predict_batch(batch)
#            for y in ys:
#                yield y
#
#    def update(self, stream, batch_size=1000):
#        for X, y in util.minibatch(stream, batch_size=batch_size):
#            output, finish_update = self.begin_update(X)
#            gradient = finish_update(y)
#            yield gradient
# 
#def list_gradients(self):
#    pass
#
#@contextlib.contextmanager
#def use_params(self, params):
#    if ('', self.name) in params:
#        current = self.params.weights.copy()
#        current[:] = self.params.weights
#        self.params.weights[:] = params[('', self.name)]
#        yield
#        self.params.weights[:] = current
#
#def check_input(self, x, expect_batch=False):
#    if self.layers:
#        return self.layers[0].check_input(x, expect_batch=expect_batch)
#    if is_batch(x):
#        shape = x.shape[1:]
#    else:
#        raise ShapeError.expected_batch(locals(), globals())
#    if shape != self.input_shape:
#        raise ShapeError.dim_mismatch(self.input_shape, shape)
#    else:
#        return True
#
#def __call__(self, x):
#    '''Predict a single x.'''
#    self.check_input(x)
#    if is_batch:
#        return self.predict_batch(x)
#    else:
#        return self.predict_one(x)
#
#
#
#def allocate_params(model):
#    '''Allocate all trainable parameters of a model, including for its sublayers,
#    so that parameters can be contiguous in memory.'''
#    # Get total size
#    size = sum(prod(shape) for shape in model.describe_all_params)
#    params = Params(total=size)
#    for i, layer in enumerate(all_layers(model)):
#        layer.name = '%s-%d' % (layer.name, i)
#        for name, shape, init in describe_params(model):
#            params.add(name, shape)
#            if init is not None:
#                init(params.get(name), inplace=True)
#    return params
#
#
#def set_dimensions_given_data(model, X, y):
#    pass
#
#
#def initialize_weights_given_data(model, X, y):
#    for name, weights in model.weights.items():
#        init = model.get_initialzer(name)
#
#    for key, (name, shape, init_func) in model.description.weights:
#        if init_func is not None:
#            weights = model.w.get(key)
#            init_func(weights, X, y)
#
#
#
#def all_layers(model):
#    '''Iterate over all layers in the model.'''
#    queue = [model]
#    seen = set()
#    for layer in queue:
#        yield layer
#        queue.extend(layer.layers)
#        assert id(layer) not in seen # Catch loops!
#        seen.add(id(layer))
#
#
#def describe_all_params(model):
#    for layer in model.all_layers:
#        for name, shape, init in layer.describe_params:
#            yield name, shape, init
#
#

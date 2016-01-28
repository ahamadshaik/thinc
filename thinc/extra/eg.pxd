from cymem.cymem cimport Pool
from libc.math cimport sqrt as c_sqrt
from libc.string cimport memset, memcpy, memmove

from preshed.maps cimport map_init as Map_init
from preshed.maps cimport map_set as Map_set
from preshed.maps cimport map_get as Map_get

from ..structs cimport ExampleC, FeatureC, MapC
from ..typedefs cimport feat_t, weight_t, atom_t
from ..linalg cimport Vec, VecVec


cdef class Example:
    cdef Pool mem
    cdef ExampleC c

    @staticmethod
    cdef inline Example from_ptr(Pool mem, ExampleC* ptr):
        cdef Example eg = Example.__new__(Example)
        eg.mem = mem
        eg.c = ptr[0]
        return eg

    @staticmethod
    cdef inline void init(ExampleC* self, Pool mem, model_shape,
                          blocks_per_layer) except *:
        self.fwd_state = <weight_t**>mem.alloc(len(model_shape), sizeof(void*))
        self.bwd_state = <weight_t**>mem.alloc(len(model_shape), sizeof(void*))
        self.widths = <int*>mem.alloc(len(model_shape), sizeof(int))
        for i, width in enumerate(model_shape):
            self.widths[i] = width
            self.fwd_state[i] = <weight_t*>mem.alloc(width * blocks_per_layer,
                                                     sizeof(weight_t))
            self.bwd_state[i] = <weight_t*>mem.alloc(width * blocks_per_layer,
                                                     sizeof(weight_t))
        self.nr_layer = len(model_shape)

        self.nr_class = model_shape[-1]
        self.scores = <weight_t*>mem.alloc(self.nr_class, sizeof(self.scores[0]))
        self.is_valid = <int*>mem.alloc(self.nr_class, sizeof(self.is_valid[0]))
        memset(self.is_valid, 1, sizeof(self.is_valid[0]) * self.nr_class)
        self.costs = <weight_t*>mem.alloc(self.nr_class, sizeof(self.costs[0]))

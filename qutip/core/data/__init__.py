# First-class type imports

from . import dense, csr
from .dense import Dense
from .csr import CSR
from .base import Data

from .add import *
from .adjoint import *
from .constant import *
from .eigen import *
from .expect import *
from .expm import *
from .inner import *
from .kron import *
from .linalg import *
from .matmul import *
from .make import *
from .mul import *
from .pow import *
from .project import *
from .properties import *
from .ptrace import *
from .reshape import *
from .tidyup import *
from .trace import *
from .solve import *
# For operations with mulitple related versions, we just import the module.
from . import norm, permute


# Set up the data conversions that are known by us.  All types covered by
# conversions will be made available for use in the dispatcher functions.

from .convert import to, create
to.add_conversions([
    (Dense, CSR, dense.from_csr, 1),
    (CSR, Dense, csr.from_dense, 1.4),
])
to.register_aliases(['csr', 'CSR'], CSR)
to.register_aliases(['Dense', 'dense'], Dense)


from . import _creator_utils
import numpy as np
create.add_creators([
    (_creator_utils.is_data, _creator_utils.data_copy, 100),
    (_creator_utils.isspmatrix_csr, CSR, 80),
    (_creator_utils.is_nparray, Dense, 80),
    (_creator_utils.issparse, CSR, 20),
    (_creator_utils.true, Dense, -np.inf),
])
del _creator_utils
del np

from .dispatch import Dispatcher

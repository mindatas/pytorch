from .engine import ExecutionEngine


class Variable(object):

    _execution_engine = ExecutionEngine()

    _fallthrough_methods = [
        'size',
        'stride',
        'nElement',
        'nDimension',
        'elementSize',
        'isContiguous',
        'isSameSizeAs',
        'isSetTo',
        'isSize',
        'is_signed',
        'numel',
        'dim',
        # TODO: add more
    ]

    def __init__(self, tensor, creator=None, volatile=False, requires_grad=True):
        if volatile:
            requires_grad = False
        if not volatile and creator is None:
            creator = Leaf(self, requires_grad)
        self.creator = creator
        self.volatile = volatile
        self.dirty = False
        self._requires_grad = None
        self._data = tensor
        self._grad = None

    @property
    def grad(self):
        if not self.volatile and self.requires_grad:
            # TODO: this won't have to be zeroed in the future
            self._grad = self._grad or self.data.new(self.data.size()).zero_()
        return self._grad

    @property
    def data(self):
        if self.dirty:
            raise RuntimeError('Accessing data of a dirty variable!')
        return self._data

    @property
    def requires_grad(self):
        if self.volatile:
            return False
        if self._requires_grad is not None:
            return self._requires_grad
        return self.creator.requires_grad

    def mark_dirty(self):
        self.dirty = True
        self._data = None

    def __getattr__(self, name):
        if name in self._fallthrough_methods:
            return getattr(self.data, name)
        raise AttributeError(name)

    def __getitem__(self, key):
        return Index(key)(self)

    def __deepcopy__(self, memo):
        if isinstance(self.creator, Leaf):
            return Variable(self.data.clone(), requires_grad=self.requires_grad,
                    volatile=self.volatile)
        raise RuntimeError("Only Variables created explicitly by the user "
                "(graph leaves) support the deepcopy protocol at the moment")

    def backward(self, gradient=None):
        if self.volatile:
            raise RuntimeError('calling backward on a volatile variable')
        if not self.requires_grad:
            raise RuntimeError("calling backward on a variable that doesn't require gradient")
        if gradient is None:
            if self.data.numel() != 1:
                raise RuntimeError('backward should be called only on a scalar (i.e. 1-element tensor) or with gradient w.r.t. the variable')
            gradient = self.data.new(1).fill_(1)
        self._execution_engine.run_backward(self, gradient)

    def __repr__(self):
        if self.dirty:
            return 'Variable used in an in-place operation'
        return 'Variable containing:' + self.data.__repr__()

    def register_hook(self, name, hook):
        if self.volatile:
            raise RuntimeError('registering hook on a volatile variable')
        if not self.requires_grad:
            raise RuntimeError("registering hook on a variable that doesn't require gradient")
        self.creator.register_hook(name, hook, self)

    def remove_hook(self, name):
        if self.volatile:
            raise RuntimeError("volatile variables don't support hooks")
        self.creator.remove_hook(name)

    def contiguous_(self):
        self._data = self.data.contiguous()
        return self

    def type(self, t):
        if t != type(self.data):
            return Type(t)(self)
        return self

    def _add(self, other, inplace):
        if isinstance(other, Variable):
            return Add(inplace)(self, other)
        else:
            assert not torch.isTensor(other)
            return AddConstant(other, inplace)(self)

    def add(self, other):
        return self._add(other, False)

    def add_(self, other):
        return self._add(other, True)

    def _sub(self, other, inplace):
        if isinstance(other, Variable):
            return Sub(inplace=inplace)(self, other)
        else:
            assert not torch.isTensor(other)
            return SubConstant(other, inplace=inplace)(self)

    def sub(self, other):
        return self._sub(other, False)

    def sub_(self, other):
        return self._sub(other, True)

    def mul(self, other):
        if isinstance(other, Variable):
            return Mul()(self, other)
        else:
            assert not torch.isTensor(other)
            return MulConstant(other)(self)

    def mul_(self, other):
        if not isinstance(other, Variable) and not torch.isTensor(other):
            return MulConstant(other, inplace=True)(self)
        raise RuntimeError("mul_ only supports scalar multiplication")

    def div(self, other):
        if isinstance(other, Variable):
            return Div()(self, other)
        else:
            assert not torch.isTensor(other)
            return DivConstant(other)(self)

    def div_(self, other):
        if not isinstance(other, Variable) and not torch.isTensor(other):
            return DivConstant(other, inplace=True)(self)
        raise RuntimeError("mul_ only supports scalar multiplication")

    def pow(self, other):
        if isinstance(other, Variable):
            return Pow()(self, other)
        else:
            assert not torch.isTensor(other)
            return PowConstant(other)(self)

    def exp(self):
        return Exp()(self)

    def exp_(self):
        return Exp(inplace=True)(self)

    def log(self):
        return Log()(self)

    def log1p(self):
        return Log1p()(self)

    def neg(self):
        return Negate()(self)

    def neg_(self):
        return Negate(inplace=True)(self)

    def tanh(self):
        return Tanh()(self)

    def tanh_(self):
        return Tanh(True)(self)

    def sigmoid(self):
        return Sigmoid()(self)

    def sigmoid_(self):
        return Sigmoid(True)(self)

    def sin(self):
        return Sin()(self)

    def cos(self):
        return Cos()(self)

    def tan(self):
        return Tan()(self)

    def asin(self):
        return Asin()(self)

    def acos(self):
        return Acos()(self)

    def atan(self):
        return Atan()(self)

    def sinh(self):
        return Sinh()(self)

    def cosh(self):
        return Cosh()(self)

    def abs(self):
        return Abs()(self)

    def clamp(self, min_val, max_val):
        return Clamp(min_val, max_val)(self)

    def cinv(self):
        return Cinv()(self)

    def cmax(self, other):
        if isinstance(other, Variable):
            return Cmax()(self, other)
        else:
            return CmaxConstant(other)(self)

    def cmin(self, other):
        if isinstance(other, Variable):
            return Cmin()(self, other)
        else:
            return CminConstant(other)(self)

    def floor(self):
        return Floor()(self)

    def ceil(self):
        return Ceil()(self)

    def frac(self):
        return Frac()(self)

    def sqrt(self):
        return Sqrt()(self)

    def round(self):
        return Round()(self)

    def sign(self):
        return Sign()(self)

    def trunc(self):
        return Trunc()(self)

    def floor(self):
        return Floor()(self)

    def ceil(self):
        return Ceil()(self)

    def fmod(self, value):
        return Fmod(value)(self)

    def remainder(self, value):
        return Remainder(value)(self)

    def lerp(self, tensor, weight):
        return Lerp(weight)(self, tensor)

    def rsqrt(self):
        return Rsqrt()(self)

    def sum(self, dim=None):
        return Sum(dim)(self)

    def mean(self, dim=None):
        return Mean(dim)(self)

    def max(self, dim=None):
        return Max(dim)(self)

    def min(self, dim=None):
        return Min(dim)(self)

    def mode(self, dim=None):
        return Mode(dim)(self)

    def median(self, dim=None):
        return Median(dim)(self)

    def view(self, *sizes):
        return View(*sizes)(self)

    def viewAs(self, tensor):
        return View(*tensor.size())(self)

    def _blas(self, cls, args, inplace):
        num_args = len(args)
        alpha = beta = 1
        if num_args > 4:
            raise RuntimeError("too many args")
        if num_args == 4:
            alpha, beta = args[:2]
        if num_args == 3:
            alpha = args[0]
        return cls(alpha, beta, inplace)(self, *args[-2:])

    def addmm(self, *args):
        return self._blas(Addmm, args, False)

    def addmm_(self, *args):
        return self._blas(Addmm, args, True)

    def addbmm(self, *args):
        return self._blas(Addbmm, args, False)

    def addbmm_(self, *args):
        return self._blas(Addbmm, args, True)

    def baddbmm(self, *args):
        return self._blas(Baddbmm, args, False)

    def baddbmm_(self, *args):
        return self._blas(Baddbmm, args, True)

    def addmv(self, *args):
        return self._blas(Addmv, args, False)

    def addmv_(self, *args):
        return self._blas(Addmv, args, True)

    def addr(self, *args):
        return self._blas(Addr, args, False)

    def addr(self, *args):
        return self._blas(Addr, args, True)

    def dot(self, other):
        return Dot()(self, other)

    def _addcop(self, op, args):
        if len(args) == 3:
            # scale, tensor1, tensor2
            return op(args[0])(self, *args[1:])
        else:
            # tensor1, tensor2
            return op()(self, *args)

    def addcmul(self, *args):
        return self._addcop(Addcmul, args)

    def addcdiv(self, *args):
        return self._addcop(Addcdiv, args)

    def norm(self, norm_type=2, dim=None):
        return Norm(norm_type, dim)(self)

    def dist(self, tensor, norm_type=2):
        return Norm(norm_type)(self - tensor)

    def indexAdd(self, dim, index, tensor):
        return IndexAdd(dim)(self, index, tensor)

    def indexCopy(self, dim, index, tensor):
        return IndexCopy(dim)(self, index, tensor)

    def indexFill(self, dim, index, value):
        return IndexFill(dim, value)(self, index)

    def indexSelect(self, dim, index):
        return IndexSelect(dim)(self, index)

    def expand(self, *sizes):
        return Expand(*sizes)(self)

    def expandAs(self, tensor):
        return Expand(*tensor.size())(self)

    def t(self):
        return Transpose(0, 1)(self)

    def transpose(self, dim1, dim2):
        return Transpose(dim1, dim2)(self)

    # TODO: permute
    # TODO: narrow

    def __add__(self, other):
        return self.add(other)
    __radd__ = __add__

    def __sub__(self, other):
        return self.sub(other)

    def __rsub__(self, other):
        return SubConstant(other, sub_tensor=True)(self)

    def __mul__(self, other):
        return self.mul(other)
    __rmul__ = __mul__

    def __div__(self, other):
        return self.div(other)
    __truediv__ = __div__

    def __rdiv__(self, other):
        return DivConstant(other, div_by_tensor=True)(self)
    __rtruediv__ = __rdiv__

    def __pow__(self, other):
        return self.pow(other)

    def __rpow__(self, other):
        return PowConstant(other, tensor_power=True)(self)

    def __neg__(self):
        return Negate()(self)


from .leaf import Leaf
from .functions import *

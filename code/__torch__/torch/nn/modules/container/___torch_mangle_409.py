class Sequential(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  __annotations__["0"] = __torch__.torchvision.ops.misc.___torch_mangle_395.Conv2dNormActivation
  __annotations__["1"] = __torch__.torchvision.ops.misc.___torch_mangle_399.Conv2dNormActivation
  __annotations__["2"] = __torch__.torchvision.ops.misc.___torch_mangle_405.SqueezeExcitation
  __annotations__["3"] = __torch__.torchvision.ops.misc.___torch_mangle_408.Conv2dNormActivation
  def forward(self: __torch__.torch.nn.modules.container.___torch_mangle_409.Sequential,
    argument_1: Tensor) -> Tensor:
    _3 = getattr(self, "3")
    _2 = getattr(self, "2")
    _1 = getattr(self, "1")
    _0 = getattr(self, "0")
    _4 = (_1).forward((_0).forward(argument_1, ), )
    return (_3).forward((_2).forward(_4, ), )

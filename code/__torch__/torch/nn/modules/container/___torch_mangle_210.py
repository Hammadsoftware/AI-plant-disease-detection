class Sequential(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  __annotations__["0"] = __torch__.torchvision.models.efficientnet.MBConv
  __annotations__["1"] = __torch__.torchvision.models.efficientnet.___torch_mangle_129.MBConv
  __annotations__["2"] = __torch__.torchvision.models.efficientnet.___torch_mangle_149.MBConv
  __annotations__["3"] = __torch__.torchvision.models.efficientnet.___torch_mangle_169.MBConv
  __annotations__["4"] = __torch__.torchvision.models.efficientnet.___torch_mangle_189.MBConv
  __annotations__["5"] = __torch__.torchvision.models.efficientnet.___torch_mangle_209.MBConv
  def forward(self: __torch__.torch.nn.modules.container.___torch_mangle_210.Sequential,
    argument_1: Tensor) -> Tensor:
    _5 = getattr(self, "5")
    _4 = getattr(self, "4")
    _3 = getattr(self, "3")
    _2 = getattr(self, "2")
    _1 = getattr(self, "1")
    _0 = getattr(self, "0")
    _6 = (_1).forward((_0).forward(argument_1, ), )
    _7 = (_4).forward((_3).forward((_2).forward(_6, ), ), )
    return (_5).forward(_7, )

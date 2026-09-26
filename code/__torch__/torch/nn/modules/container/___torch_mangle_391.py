class Sequential(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  __annotations__["0"] = __torch__.torchvision.models.efficientnet.___torch_mangle_230.MBConv
  __annotations__["1"] = __torch__.torchvision.models.efficientnet.___torch_mangle_250.MBConv
  __annotations__["2"] = __torch__.torchvision.models.efficientnet.___torch_mangle_270.MBConv
  __annotations__["3"] = __torch__.torchvision.models.efficientnet.___torch_mangle_290.MBConv
  __annotations__["4"] = __torch__.torchvision.models.efficientnet.___torch_mangle_310.MBConv
  __annotations__["5"] = __torch__.torchvision.models.efficientnet.___torch_mangle_330.MBConv
  __annotations__["6"] = __torch__.torchvision.models.efficientnet.___torch_mangle_350.MBConv
  __annotations__["7"] = __torch__.torchvision.models.efficientnet.___torch_mangle_370.MBConv
  __annotations__["8"] = __torch__.torchvision.models.efficientnet.___torch_mangle_390.MBConv
  def forward(self: __torch__.torch.nn.modules.container.___torch_mangle_391.Sequential,
    argument_1: Tensor) -> Tensor:
    _8 = getattr(self, "8")
    _7 = getattr(self, "7")
    _6 = getattr(self, "6")
    _5 = getattr(self, "5")
    _4 = getattr(self, "4")
    _3 = getattr(self, "3")
    _2 = getattr(self, "2")
    _1 = getattr(self, "1")
    _0 = getattr(self, "0")
    _9 = (_1).forward((_0).forward(argument_1, ), )
    _10 = (_4).forward((_3).forward((_2).forward(_9, ), ), )
    _11 = (_7).forward((_6).forward((_5).forward(_10, ), ), )
    return (_8).forward(_11, )

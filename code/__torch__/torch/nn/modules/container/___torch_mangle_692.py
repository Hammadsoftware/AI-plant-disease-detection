class Sequential(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  __annotations__["0"] = __torch__.torchvision.models.efficientnet.___torch_mangle_411.MBConv
  __annotations__["1"] = __torch__.torchvision.models.efficientnet.___torch_mangle_431.MBConv
  __annotations__["2"] = __torch__.torchvision.models.efficientnet.___torch_mangle_451.MBConv
  __annotations__["3"] = __torch__.torchvision.models.efficientnet.___torch_mangle_471.MBConv
  __annotations__["4"] = __torch__.torchvision.models.efficientnet.___torch_mangle_491.MBConv
  __annotations__["5"] = __torch__.torchvision.models.efficientnet.___torch_mangle_511.MBConv
  __annotations__["6"] = __torch__.torchvision.models.efficientnet.___torch_mangle_531.MBConv
  __annotations__["7"] = __torch__.torchvision.models.efficientnet.___torch_mangle_551.MBConv
  __annotations__["8"] = __torch__.torchvision.models.efficientnet.___torch_mangle_571.MBConv
  __annotations__["9"] = __torch__.torchvision.models.efficientnet.___torch_mangle_591.MBConv
  __annotations__["10"] = __torch__.torchvision.models.efficientnet.___torch_mangle_611.MBConv
  __annotations__["11"] = __torch__.torchvision.models.efficientnet.___torch_mangle_631.MBConv
  __annotations__["12"] = __torch__.torchvision.models.efficientnet.___torch_mangle_651.MBConv
  __annotations__["13"] = __torch__.torchvision.models.efficientnet.___torch_mangle_671.MBConv
  __annotations__["14"] = __torch__.torchvision.models.efficientnet.___torch_mangle_691.MBConv
  def forward(self: __torch__.torch.nn.modules.container.___torch_mangle_692.Sequential,
    argument_1: Tensor) -> Tensor:
    _14 = getattr(self, "14")
    _13 = getattr(self, "13")
    _12 = getattr(self, "12")
    _11 = getattr(self, "11")
    _10 = getattr(self, "10")
    _9 = getattr(self, "9")
    _8 = getattr(self, "8")
    _7 = getattr(self, "7")
    _6 = getattr(self, "6")
    _5 = getattr(self, "5")
    _4 = getattr(self, "4")
    _3 = getattr(self, "3")
    _2 = getattr(self, "2")
    _1 = getattr(self, "1")
    _0 = getattr(self, "0")
    _15 = (_1).forward((_0).forward(argument_1, ), )
    _16 = (_4).forward((_3).forward((_2).forward(_15, ), ), )
    _17 = (_7).forward((_6).forward((_5).forward(_16, ), ), )
    _18 = (_10).forward((_9).forward((_8).forward(_17, ), ), )
    _19 = (_12).forward((_11).forward(_18, ), )
    _20 = (_14).forward((_13).forward(_19, ), )
    return _20

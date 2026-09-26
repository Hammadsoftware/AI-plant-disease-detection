class Conv2dNormActivation(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  __annotations__["0"] = __torch__.torch.nn.modules.conv.Conv2d
  __annotations__["1"] = __torch__.torch.nn.modules.batchnorm.BatchNorm2d
  __annotations__["2"] = __torch__.torch.nn.modules.activation.SiLU
  def forward(self: __torch__.torchvision.ops.misc.Conv2dNormActivation,
    x: Tensor) -> Tensor:
    _2 = getattr(self, "2")
    _1 = getattr(self, "1")
    _0 = getattr(self, "0")
    _3 = (_2).forward((_1).forward((_0).forward(x, ), ), )
    return _3
class SqueezeExcitation(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  avgpool : __torch__.torch.nn.modules.pooling.AdaptiveAvgPool2d
  fc1 : __torch__.torch.nn.modules.conv.___torch_mangle_102.Conv2d
  fc2 : __torch__.torch.nn.modules.conv.___torch_mangle_103.Conv2d
  activation : __torch__.torch.nn.modules.activation.___torch_mangle_104.SiLU
  scale_activation : __torch__.torch.nn.modules.activation.Sigmoid
  def forward(self: __torch__.torchvision.ops.misc.SqueezeExcitation,
    argument_1: Tensor) -> Tensor:
    scale_activation = self.scale_activation
    fc2 = self.fc2
    activation = self.activation
    fc1 = self.fc1
    avgpool = self.avgpool
    _1 = (fc1).forward((avgpool).forward(argument_1, ), )
    _2 = (fc2).forward((activation).forward(_1, ), )
    input = torch.mul((scale_activation).forward(_2, ), argument_1)
    return input

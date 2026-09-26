class SqueezeExcitation(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  avgpool : __torch__.torch.nn.modules.pooling.___torch_mangle_480.AdaptiveAvgPool2d
  fc1 : __torch__.torch.nn.modules.conv.___torch_mangle_481.Conv2d
  fc2 : __torch__.torch.nn.modules.conv.___torch_mangle_482.Conv2d
  activation : __torch__.torch.nn.modules.activation.___torch_mangle_483.SiLU
  scale_activation : __torch__.torch.nn.modules.activation.___torch_mangle_484.Sigmoid
  def forward(self: __torch__.torchvision.ops.misc.___torch_mangle_485.SqueezeExcitation,
    argument_1: Tensor) -> Tensor:
    scale_activation = self.scale_activation
    fc2 = self.fc2
    activation = self.activation
    fc1 = self.fc1
    avgpool = self.avgpool
    _0 = (fc1).forward((avgpool).forward(argument_1, ), )
    _1 = (fc2).forward((activation).forward(_0, ), )
    input = torch.mul((scale_activation).forward(_1, ), argument_1)
    return input

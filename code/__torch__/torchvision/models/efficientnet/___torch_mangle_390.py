class MBConv(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  block : __torch__.torch.nn.modules.container.___torch_mangle_388.Sequential
  stochastic_depth : __torch__.torchvision.ops.stochastic_depth.___torch_mangle_389.StochasticDepth
  def forward(self: __torch__.torchvision.models.efficientnet.___torch_mangle_390.MBConv,
    argument_1: Tensor) -> Tensor:
    stochastic_depth = self.stochastic_depth
    block = self.block
    _0 = (block).forward(argument_1, )
    _1 = (stochastic_depth).forward()
    return torch.add_(_0, argument_1)

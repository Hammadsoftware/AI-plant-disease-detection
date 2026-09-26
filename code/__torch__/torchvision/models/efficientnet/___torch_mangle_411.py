class MBConv(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  block : __torch__.torch.nn.modules.container.___torch_mangle_409.Sequential
  stochastic_depth : __torch__.torchvision.ops.stochastic_depth.___torch_mangle_410.StochasticDepth
  def forward(self: __torch__.torchvision.models.efficientnet.___torch_mangle_411.MBConv,
    argument_1: Tensor) -> Tensor:
    block = self.block
    return (block).forward(argument_1, )

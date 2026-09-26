class Sequential(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  __annotations__["0"] = __torch__.torchvision.ops.misc.___torch_mangle_3.Conv2dNormActivation
  def forward(self: __torch__.torch.nn.modules.container.Sequential,
    argument_1: Tensor) -> Tensor:
    _0 = getattr(self, "0")
    return (_0).forward(argument_1, )

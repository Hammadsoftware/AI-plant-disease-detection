class Sigmoid(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  def forward(self: __torch__.torch.nn.modules.activation.___torch_mangle_202.Sigmoid,
    argument_1: Tensor) -> Tensor:
    return torch.sigmoid(argument_1)

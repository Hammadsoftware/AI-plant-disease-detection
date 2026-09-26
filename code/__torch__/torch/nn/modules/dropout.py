class Dropout(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  def forward(self: __torch__.torch.nn.modules.dropout.Dropout,
    input: Tensor) -> Tensor:
    input0 = torch.dropout_(input, 0.20000000000000001, False)
    return input0

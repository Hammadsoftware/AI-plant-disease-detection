class BatchNorm2d(Module):
  __parameters__ = ["weight", "bias", ]
  __buffers__ = ["running_mean", "running_var", "num_batches_tracked", ]
  weight : Tensor
  bias : Tensor
  running_mean : Tensor
  running_var : Tensor
  num_batches_tracked : Tensor
  training : bool
  _is_full_backward_hook : Optional[bool]
  def forward(self: __torch__.torch.nn.modules.batchnorm.___torch_mangle_205.BatchNorm2d,
    argument_1: Tensor) -> Tensor:
    running_var = self.running_var
    running_mean = self.running_mean
    bias = self.bias
    weight = self.weight
    result = torch.batch_norm(argument_1, weight, bias, running_mean, running_var, False, 0.10000000000000001, 0.001, True)
    return result

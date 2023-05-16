# -*- coding: utf-8 -*-
#
#  Copyright 2021-2023 Ramil Nugmanov <nougmanoff@protonmail.com>
#  This file is part of chytorch.
#
#  chytorch is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, see <https://www.gnu.org/licenses/>.
#
from torch import Tensor, cat
from torch.nn import Dropout, GELU, LayerNorm, Module
from typing import Tuple, Optional
from .attention import MultiheadAttention
from .linear import Linear


class EncoderLayer(Module):
    r"""EncoderLayer based on torch.nn.TransformerEncoderLayer, but batch always first and returns also attention.

    :param d_model: the number of expected features in the input (required).
    :param nhead: the number of heads in the multiheadattention models (required).
    :param dim_feedforward: the dimension of the feedforward network model (required).
    :param dropout: the dropout value (default=0.1).
    :param activation: the activation function of the intermediate layer. Default: GELU.
    :param layer_norm_eps: the eps value in layer normalization components (default=1e-5).
    :param norm_first: if `True`, layer norm is done prior to self attention, multihead
        attention and feedforward operations, respectively. Otherwise, it's done after.
    :param lora_r: LoRA factorization dimension
    :param lora_alpha: LoRA scaling factor
    :param lora_dropout: LoRA input dropout
    """
    def __init__(self, d_model, nhead, dim_feedforward, dropout=0.1, activation=GELU, layer_norm_eps=1e-5,
                 norm_first: bool = False, lora_r: int = 0, lora_alpha: float = 1., lora_dropout: float = 0.):
        super().__init__()
        self.self_attn = MultiheadAttention(d_model, nhead, dropout=dropout,
                                            lora_r=lora_r, lora_alpha=lora_alpha, lora_dropout=lora_dropout)

        self.linear1 = Linear(d_model, dim_feedforward, lora_r=lora_r, lora_alpha=lora_alpha, lora_dropout=lora_dropout)
        self.linear2 = Linear(dim_feedforward, d_model, lora_r=lora_r, lora_alpha=lora_alpha, lora_dropout=lora_dropout)
        self.norm1 = LayerNorm(d_model, eps=layer_norm_eps)
        self.norm2 = LayerNorm(d_model, eps=layer_norm_eps)
        self.dropout1 = Dropout(dropout)
        self.dropout2 = Dropout(dropout)
        self.dropout3 = Dropout(dropout)
        self.activation = activation()
        self.norm_first = norm_first

    def forward(self, x: Tensor, attn_mask: Tensor, *, hidden: Optional[Tensor] = None,
                need_embedding: bool = True, need_weights: bool = False) -> Tuple[Optional[Tensor], Optional[Tensor]]:
        nx = self.norm1(x) if self.norm_first else x  # pre-norm or post-norm
        if hidden is None:
            kv = nx
        else:  # inference of next token with cached embedding
            if self.norm_first:
                hidden = self.norm1(hidden)
            kv = cat([hidden, nx], dim=0)  # create the whole sequence for key-value
        e, a = self.self_attn(nx, kv, attn_mask=attn_mask, need_weights=need_weights)

        if need_embedding:
            x = x + self.dropout1(e)
            if self.norm_first:
                return x + self._ff(self.norm2(x)), a
            # else: post-norm
            x = self.norm1(x)
            return self.norm2(x + self._ff(x)), a
        return None, a

    def merge_lora(self):
        """
        Transform LoRA Encoder to normal
        """
        self.self_attn.merge_lora()
        self.linear1.merge_lora()
        self.linear2.merge_lora()

    def _ff(self, x):
        return self.dropout3(self.linear2(self.dropout2(self.activation(self.linear1(x)))))


__all__ = ['EncoderLayer']

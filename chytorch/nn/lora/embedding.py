# -*- coding: utf-8 -*-
#
#  Copyright 2023 Ramil Nugmanov <nougmanoff@protonmail.com>
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
from math import inf
from torch import empty, no_grad, addmm, Tensor
from torch.nn import Embedding as tEmbedding, Parameter, init
from torch.nn.functional import embedding
from typing import Optional


class Embedding(tEmbedding):
    """
    LoRA wrapped Embedding layer.
    """
    def __init__(self, num_embeddings: int, embedding_dim: int, *args,
                 lora_r: int = 0, lora_alpha: float = 1., neg_inf_idx: Optional[int] = None, **kwargs):
        """
        :param lora_r: LoRA factorization dimension
        :param lora_alpha: LoRA scaling factor
        :param neg_inf_idx: -inf frozen embedding vector

        See torch.nn.Embedding for other params
        """
        super().__init__(num_embeddings, embedding_dim, *args, **kwargs)
        self.neg_inf_idx = neg_inf_idx
        self.lora_r = lora_r
        if neg_inf_idx is not None:
            with no_grad():
                self.weight[neg_inf_idx].fill_(-inf)
        if lora_r:  # enable lora
            self.weight.requires_grad = False  # freeze main weights
            self.lora_a = Parameter(init.zeros_(empty(num_embeddings, lora_r)))
            self.lora_b = Parameter(init.normal_(empty(embedding_dim, lora_r)))
            self.lora_alpha = lora_alpha
            self._lora_scaling = lora_alpha / lora_r

    def forward(self, x: Tensor) -> Tensor:
        emb = super().forward(x)
        if self.lora_r:
            a = embedding(x, self.lora_a, self.padding_idx, self.max_norm,
                          self.norm_type, self.scale_grad_by_freq, self.sparse)
            return addmm(emb.flatten(end_dim=-2), a.flatten(end_dim=-2), self.lora_b.transpose(0, 1),
                         alpha=self._lora_scaling).view(emb.shape)
        return emb

    def merge_lora(self):
        """
        Transform LoRA embedding to normal
        """
        if not self.lora_r:
            return
        self.weight.data += (self.lora_a @ self.lora_b.transpose(0, 1)) * self._lora_scaling
        self.weight.requires_grad = True
        self.lora_r = 0
        del self.lora_a, self.lora_b, self.lora_alpha, self._lora_scaling

    def extra_repr(self) -> str:
        r = super().extra_repr()
        if self.lora_r:
            return  r + f', lora_r={self.lora_r}, lora_alpha={self.lora_alpha}'
        return r


__all__ = ['Embedding']

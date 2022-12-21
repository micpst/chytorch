# -*- coding: utf-8 -*-
#
#  Copyright 2021, 2022 Ramil Nugmanov <nougmanoff@protonmail.com>
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
from .lmdb import *
from .molecule import *
from .pandas import *
from .reaction import *
from .sampler import *
from .tokenizer import *
from ._utils import *


def chained_collate(*collate_fns):
    """
    Collate batch of tuples with different data structures by different collate functions.
    """
    def w(batch):
        sub_batches = [[] for _ in collate_fns]
        for x in batch:
            for y, s in zip(x, sub_batches):
                s.append(y)
        return [f(x) for x, f in zip(sub_batches, collate_fns)]
    return w


__all__ = ['MoleculeDataset', 'ContrastiveDataset', 'ContrastiveMethylDataset',
           'ReactionEncoderDataset', 'ReactionDecoderDataset',  'PermutedReactionDataset', 'FakeReactionDataset',
           'SMILESDataset', 'MappedReactionDataset',
           'StructureSampler', 'DistributedStructureSampler',
           'SizedList', 'LMDBMapper', 'LMDBProperties', 'LMDBStructure',
           'PandasStructureDataset', 'PandasPropertiesDataset',
           'collate_molecules', 'contrastive_collate', 'collate_encoded_reactions', 'collate_decoded_reactions',
           'collate_permuted_reactions', 'collate_faked_reactions', 'collate_mapped_reactions',
           'collate_sequences', 'chained_collate']

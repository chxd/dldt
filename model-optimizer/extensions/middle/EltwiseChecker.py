"""
 Copyright (c) 2018-2019 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import numpy as np

from mo.graph.graph import Node, Graph
from mo.middle.replacement import MiddleReplacementPattern


class EltwiseChecker(MiddleReplacementPattern):
    # This pass checks for each eltwise, can it be ScaleShift or not
    enabled = True

    def run_after(self):
        from extensions.middle.EltwiseInputReshape import Eltwise1DInputReshape
        return [Eltwise1DInputReshape]

    def run_before(self):
        from extensions.middle.pass_separator import MiddleFinish
        return [MiddleFinish]

    def find_and_replace_pattern(self, graph: Graph):
        eltwise_nodes = [Node(graph, node) for node in graph.node if Node(graph, node).soft_get('type') == 'Eltwise']
        for node in eltwise_nodes:
            raw_inputs = [(inp, attr) for inp, attr in node.get_sorted_inputs()
                          if 'control_flow_edge' not in attr or not attr['control_flow_edge']]
            shapes = [node.graph.node[inp]['shape'] for inp, attr in raw_inputs]

            max_dims = None
            max_dims_id = None
            input_shape = None
            for id, s in enumerate(shapes):
                if max_dims is None or len(s) > max_dims:
                    max_dims = len(s)
                    input_shape = s
                    max_dims_id = id

            feature_dim = 1 if node.graph.graph['layout'] == 'NCHW' else (max_dims - 1)

            def check_shape(shape):
                # Check that value has shape like 1,N,1,1
                return np.prod(shape) == np.max(shape) and (max_dims - feature_dim) <= len(shape) and \
                       (input_shape[feature_dim] == shape[-1 * (max_dims - feature_dim)] or
                        (shape[-1 * (max_dims - feature_dim)] == 1 and np.max(shape) == 1))

            # Make all input shapes of the same size by adding 1's
            axis = node.axis if node.has_valid('axis') else None
            for id, shape in enumerate(shapes):
                if id != max_dims_id and len(shape) > 0 and not check_shape(shapes[id]) and np.prod(shape) != 1:
                    node['can_be_fused'] = False
                    node['can_be_scaleshift'] = False

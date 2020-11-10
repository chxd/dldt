# ******************************************************************************
# Copyright 2017-2020 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ******************************************************************************

"""Factory functions for all ngraph ops."""
from typing import Callable, Iterable, List, Optional, Set, Union

import numpy as np
from functools import partial

from ngraph.impl import Node, Shape
from ngraph.impl.op import Constant, Parameter
from ngraph.opset_utils import _get_node_factory
from ngraph.utils.decorators import binary_op, nameable_op, unary_op
from ngraph.utils.input_validation import (
    assert_list_of_ints,
    check_valid_attributes,
    is_non_negative_value,
    is_positive_value,
)
from ngraph.utils.node_factory import NodeFactory
from ngraph.utils.tensor_iterator_types import (
    GraphBody,
    TensorIteratorSliceInputDesc,
    TensorIteratorMergedInputDesc,
    TensorIteratorInvariantInputDesc,
    TensorIteratorBodyOutputDesc,
    TensorIteratorConcatOutputDesc,
)
from ngraph.utils.types import (
    NodeInput,
    NumericData,
    NumericType,
    ScalarData,
    TensorShape,
    as_node,
    as_nodes,
    get_dtype,
    get_element_type,
    get_element_type_str,
    make_constant_node,
)

_get_node_factory_opset5 = partial(_get_node_factory, "opset5")

# -------------------------------------------- ops ------------------------------------------------


@nameable_op
def batch_norm_inference(
    data: NodeInput,
    gamma: NodeInput,
    beta: NodeInput,
    mean: NodeInput,
    variance: NodeInput,
    epsilon: float,
    name: Optional[str] = None,
) -> Node:
    """Perform layer normalizes a input tensor by mean and variance with appling scale and offset.

    :param data: The input tensor with data for normalization.
    :param gamma: The scalar scaling for normalized value.
    :param beta: The bias added to the scaled normalized value.
    :param mean: The value for mean normalization.
    :param variance: The value for variance normalization.
    :param epsilon: The  number to be added to the variance to avoid division
                    by zero when normalizing a value.
    :param name: The optional name of the output node.
    :return: The new node which performs BatchNormInference.
    """
    inputs = as_nodes(data, gamma, beta, mean, variance)
    return _get_node_factory_opset5().create("BatchNormInference", inputs, {"epsilon": epsilon})


@nameable_op
def gather_nd(
    data: NodeInput,
    indices: NodeInput,
    batch_dims: Optional[int] = 0,
    name: Optional[str] = None,
) -> Node:
    """Return a node which performs GatherND.

    :param data:       N-D tensor with data for gathering
    :param indices:    K-D tensor of tuples with indices by which data is gathered
    :param batch_dims: Scalar value of batch dimensions
    :return: The new node which performs GatherND
    """
    inputs = as_nodes(data, indices)

    attributes = {
        "batch_dims": batch_dims
    }

    return _get_node_factory_opset5().create("GatherND", inputs, attributes)


@nameable_op
def log_softmax(data: NodeInput, axis: int, name: Optional[str] = None) -> Node:
    """Apply LogSoftmax operation on each element of input tensor.

    :param data: The tensor providing input data.
    :param axis: An axis along which LogSoftmax should be calculated
    :return: The new node with LogSoftmax operation applied on each element.
    """
    return _get_node_factory_opset5().create("LogSoftmax", [as_node(data)], {"axis": axis})


@nameable_op
def non_max_suppression(
    boxes: NodeInput,
    scores: NodeInput,
    max_output_boxes_per_class: Optional[NodeInput] = None,
    iou_threshold: Optional[NodeInput] = None,
    score_threshold: Optional[NodeInput] = None,
    soft_nms_sigma: Optional[NodeInput] = None,
    box_encoding: str = "corner",
    sort_result_descending: bool = True,
    output_type: str = "i64",
    name: Optional[str] = None,
) -> Node:
    """Return a node which performs NonMaxSuppression.

    :param boxes: Tensor with box coordinates.
    :param scores: Tensor with box scores.
    :param max_output_boxes_per_class: Tensor Specifying maximum number of boxes
                                        to be selected per class.
    :param iou_threshold: Tensor specifying intersection over union threshold
    :param score_threshold: Tensor specifying minimum score to consider box for the processing.
    :param soft_nms_sigma: Tensor specifying the sigma parameter for Soft-NMS.
    :param box_encoding: Format of boxes data encoding.
    :param sort_result_descending: Flag that specifies whenever it is necessary to sort selected
                                   boxes across batches or not.
    :param output_type: Output element type.
    :return: The new node which performs NonMaxSuppression
    """
    if max_output_boxes_per_class is None:
        max_output_boxes_per_class = make_constant_node(0, np.int64)
    if iou_threshold is None:
        iou_threshold = make_constant_node(0, np.float32)
    if score_threshold is None:
        score_threshold = make_constant_node(0, np.float32)
    if soft_nms_sigma is None:
        inputs = as_nodes(
            boxes, scores, max_output_boxes_per_class, iou_threshold, score_threshold
        )
    else:
        inputs = as_nodes(
            boxes, scores, max_output_boxes_per_class, iou_threshold, score_threshold, soft_nms_sigma
        )

    attributes = {
        "box_encoding": box_encoding,
        "sort_result_descending": sort_result_descending,
        "output_type": output_type,
    }

    return _get_node_factory_opset5().create("NonMaxSuppression", inputs, attributes)


@nameable_op
def round(data: NodeInput, mode: str = "half_to_even", name: Optional[str] = None) -> Node:
    """Apply Round operation on each element of input tensor.

    :param data: The tensor providing input data.
    :param mode: Rule to round halfway cases. If set to 'half_to_even' then halfs round to the nearest even
        integer or rounding in such a way that the result heads away from zero if `mode` attribute is
        'half_away_from_zero`.
    :param name: An optional name of the output node.
    :return: The new node with Round operation applied on each element.
    """
    return _get_node_factory_opset5().create("Round", as_nodes(data), {"mode": mode.upper()})


@nameable_op
def hsigmoid(data: NodeInput, name: Optional[str] = None,) -> Node:
    """Return a node which performs HSigmoid.

    :param data: Tensor with input data floating point type.
    :return: The new node which performs HSigmoid
    """
    return _get_node_factory_opset5().create("HSigmoid", as_nodes(data), {})


@nameable_op
def gru_sequence(
    X: NodeInput,
    H_t: NodeInput,
    sequence_lengths: NodeInput,
    W: NodeInput,
    R: NodeInput,
    B: NodeInput,
    hidden_size: int,
    direction: str,
    activations: List[str] = None,
    activations_alpha: List[float] = None,
    activations_beta: List[float] = None,
    clip: float = 0.0,
    linear_before_reset: bool = False,
    name: Optional[str] = None,
) -> Node:
    """Return a node which performs GRUSequence.

    :param X: 3D tensor, input data.
    :param H_t: 3D tensor, input hidden state data.
    :param sequence_lengths: 1D tensor, specifies sequence lenghts
        for each batch element.
    :param W: 3D tensor, weights matrix.
    :param R: 3D tensor, recurrence weights matrix.
    :param B: 2D tensor, sum of biases.
    :param hidden_size: Size of the hidden state.
    :param direction: Specify if the RNN is forward, reverse, or bidirectional.
    :param activations: Activation functions for gates.
    :param activations_alpha: Attributes of function; applicability and meaning
        of these attributes depends on choosen activation function.
    :param activations_beta: Attributes of function; applicability and meaning
        of these attributes depends on choosen activation function.
    :param clip: Specifies bound values *[-clip, clip]* for tensor clipping.
    :param linear_before_reset: During the computation of the output of
        the hidden gate, apply the linear transformation.
    :return: The new node which performs GRUSequence
    """
    if activations is None:
        activations = ["sigmoid", "tanh"]
    if activations_alpha is None:
        activations_alpha = []
    if activations_beta is None:
        activations_beta = []

    inputs = as_nodes(X, H_t, sequence_lengths, W, R, B)

    attributes = {
        "hidden_size": hidden_size,
        "activations": activations,
        "activations_alpha": activations_alpha,
        "activations_beta": activations_alpha,
        "clip": clip,
        "linear_before_reset": linear_before_reset,
    }

    return _get_node_factory_opset5().create("GRUSequence", inputs, attributes)


@nameable_op
def rnn_sequence(
    X: NodeInput,
    H_t: NodeInput,
    sequence_lengths: NodeInput,
    W: NodeInput,
    R: NodeInput,
    B: NodeInput,
    hidden_size: int,
    direction: str,
    activations: List[str] = None,
    activations_alpha: List[float] = None,
    activations_beta: List[float] = None,
    clip: float = 0.0,
    name: Optional[str] = None,
) -> Node:
    """Return a node which performs RNNSequence.

    :param X: 3D tensor, input data.
    :param H_t: 3D tensor, input hidden state data.
    :param sequence_lengths: 1D tensor, specifies sequence lenghts
        for each batch element.
    :param W: 3D tensor, weights matrix.
    :param R: 3D tensor, recurrence weights matrix.
    :param B: 2D tensor, sum of biases.
    :param hidden_size: Size of the hidden state.
    :param direction: Specify if the RNN is forward, reverse, or bidirectional.
    :param activations: Activation functions for gates.
    :param activations_alpha: Attributes of function; applicability and meaning
        of these attributes depends on choosen activation function.
    :param activations_beta: Attributes of function; applicability and meaning
        of these attributes depends on choosen activation function.
    :param clip: Specifies bound values *[-clip, clip]* for tensor clipping.
    :return: The new node which performs RNNSequence
    """
    if activations is None:
        activations = ["tanh"]
    if activations_alpha is None:
        activations_alpha = []
    if activations_beta is None:
        activations_beta = []

    inputs = as_nodes(X, H_t, sequence_lengths, W, R, B)

    attributes = {
        "hidden_size": hidden_size,
        "activations": activations,
        "activations_alpha": activations_alpha,
        "activations_beta": activations_alpha,
        "clip": clip,
    }

    return _get_node_factory_opset5().create("RNNSequence", inputs, attributes)


@nameable_op
def loop(
    trip_count: NodeInput,
    execution_condition: NodeInput,
    name: Optional[str] = None,
) -> Node:
    """Return a node which performs Loop.

    :param trip_count: A scalar or 1D tensor with 1 element specifying
        maximum number of iterations.
    :param execution_condition: A scalar or 1D tensor with 1 element
        specifying whether to execute the first iteration or not.
    :return: The new node which performs Loop.
    """
    inputs = as_nodes(trip_count, execution_condition)

    return _get_node_factory_opset5().create("Loop", inputs)
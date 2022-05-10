from rich.console import Console
from rich.table import Table
import numpy as np
from numpy import linalg
import sys
import os
from pathlib import Path
sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent))
from utils import softmax, line_search

class MaxEntropy:
    def __init__(self, epsilon=1e-6, max_steps=1000, verbose=True):
        self.epsilon = epsilon
        self.max_steps = max_steps
        self.verbose = verbose

    def _p_w(self, w):
        """
        calculate probability table according to w
        """
        logit = (w[:, None, None] * self.feature).sum(axis=0)
        return softmax(logit, axis=-1)

    def _f(self, w):
        """
        object function
        """
        return \
            (
                np.log(
                    np.exp(
                        (w[:, None, None] * self.feature
                         ).sum(axis=0)
                    ).sum(axis=-1)) * self.p_data_x
            ).sum() - \
            (
                self.p_data * (w[:, None, None] * self.feature).sum(axis=0)
            ).sum()

    def _g(self, w):
        """
        gradient of object function
        """
        p_w = self._p_w(w)
        return (self.p_data_x[None, :, None] * p_w[None, :, :] * self.feature
                ).sum(axis=(1, 2)) - self.E_feature

    def fit(self, p_data, feature):
        """
        optimize max entropy model with BFGS
        p_data: matrix of shape [nx, ny], possibility of all (x, y)
        feature: matrix of shape[nf, nx, ny], all the feature functions of all (x, y)
        """
        # nf is the number of feature functions, and the size of w
        self.nf, self.nx, self.ny = feature.shape
        self.feature = feature
        self.p_data = p_data
        self.p_data_x = p_data.sum(axis=-1)
        self.E_feature = (p_data[None, :, :] * feature).sum(axis=(1, 2))

        # initlaize optimizer
        self.w = np.random.rand(self.nf)
        B = np.eye(self.nf)
        g_next = self._g(self.w)
        g_norm = linalg.norm(g_next)
        # optimize
        for i in range(self.max_steps):
            g = g_next
            if self.verbose:
                print(f"Step {i}, L2 norm of gradient is {g_norm}")
            if g_norm < self.epsilon:
                break
            p = linalg.solve(B, -g)
            f_lambda = lambda x: self._f(self.w + x * p)
            lamda = line_search(f_lambda, 0, 100, epsilon=self.epsilon)
            delta_w = lamda * p
            self.w += delta_w
            g_next = self._g(self.w)
            g_norm = linalg.norm(g_next)
            if g_norm < self.epsilon:
                print(f"L2 norm of gradient is {g_norm}, stop training...")
                break
            delta_g = g_next - g
            B_delta_w = B @ delta_w
            B += np.outer(delta_g, delta_g) / (delta_g @ delta_w) - \
                np.outer(B_delta_w, B_delta_w) / (B_delta_w.T @ delta_w)
        self.p_w = self._p_w(self.w)

    def predict(self, x, y):
        """predict p(y|x)"""
        return self.p_w[x][y]

# The following examples are proposed by SleepyBag at
# https://www.zhihu.com/question/24094554/answer/1507080982
if __name__ == "__main__":
    console = Console(markup=False)
    def float2str(x):
        return "%.3f" % x

    def demonstrate(data, feature_functions):
        max_entropy = MaxEntropy()
        max_entropy.fit(data, feature_functions)

        # print results
        for i, ff in enumerate(feature_functions):
            table = Table(f'feature {i}', 'y=1', 'y=2', 'y=3')
            for x in range(2):
                table.add_row(f'x={x}', *map(float2str, [ff[x, y] for y in range(3)]))
            console.print(table)
        table = Table('prob', 'y=1', 'y=2', 'y=3')
        for x in range(2):
            table.add_row(f'x={x}', *map(float2str, [max_entropy.predict(x, y) for y in range(3)]))
        console.print(table)

    # ---------------------- Prepare Data -----------------------------------------
    data = np.array([[.125, .25, .125],
                    [.5, 0., 0.]])
    table = Table('data', 'y=1', 'y=2', 'y=3')
    for x in range(2):
        table.add_row(f'x={x}', *map(float2str, [data[x, y] for y in range(3)]))
    console.print(table)

    # ---------------------- Example 1---------------------------------------------
    print('Example 1: Single feature function')
    feature_functions = np.array([
        [[1, 0, 0],
        [0, 0, 0]]
    ])
    demonstrate(data, feature_functions)

    # ---------------------- Example 3---------------------------------------------
    print('Example 2: the value of feature function doesn\'t matter for feature function with only one non-zero value')
    feature_functions = np.array([
        [[0.5, 0, 0],
         [0, 0, 0]]
    ])
    demonstrate(data, feature_functions)

    # ---------------------- Example 2---------------------------------------------
    print('Example 3: double feature functions')
    feature_functions = np.array([
        [[1, 0, 0],
         [0, 0, 0]],
        [[0, 0, 0],
         [0, 1, 0]]
    ])
    demonstrate(data, feature_functions)

    # ---------------------- Example 3---------------------------------------------
    print('Example 4: single feature function with two non-zeros')
    feature_functions = np.array([
        [[0, 1, 1],
         [0, 0, 0]]
    ])
    demonstrate(data, feature_functions)

    # ---------------------- Example 3---------------------------------------------
    print('Example 5: the value of feature function matters for feature function with multiple non-zero values')
    feature_functions = np.array([
        [[0, 1, .5],
         [0, 0, 0]]
    ])
    demonstrate(data, feature_functions)

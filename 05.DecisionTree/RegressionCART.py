import numpy as np
from pprint import pprint
from rich.console import Console
from rich.table import Table
import sys
import os
from pathlib import Path
sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent))
from utils import *


class RegressionCART:
    class Node:
        def __init__(self, col, Y):
            self.col = col
            self.val = nan
            self.left, self.right = None, None
            self.label = Y.mean()

        def __hash__(self):
            return id(self)

    def __init__(self, verbose=False, max_depth=inf):
        self.verbose = verbose
        self.max_depth = max_depth

    def get_se(self, Y_cnt):
        """get square error given the count of each Y value"""
        mean = sum(y * Y_cnt[y] for y in Y_cnt) / sum(Y_cnt.values())
        return sum((y - mean) ** 2 * Y_cnt[y] for y in Y_cnt)

    def get_se_of_split(self, Y1_cnt, Y2_cnt):
        """get the square error of a split"""
        return self.get_se(Y1_cnt) + self.get_se(Y2_cnt)

    def build(self, X, Y, depth=1):
        cur = self.Node(None, Y)
        if self.verbose:
            print("Cur data:")
            pprint(X)
            print(Y)
        best_se = inf
        best_col, best_val = -1, nan
        # The orignal content of the book doesn't discuss about when to cease.
        # So I take the easiest way: cease when the data cannot be splitted,
        # i.e., there are different labels
        if depth < self.max_depth and len(set(Y)) > 1:
            for col in range(len(X[0])):
                smaller_Y_cnt = Counter()
                larger_Y_cnt = Counter(Y)
                sorted_inds = np.argsort(X[:, col])
                # try all the possible split values
                for i, ind in enumerate(sorted_inds):
                    smaller_Y_cnt[Y[ind]] += 1
                    larger_Y_cnt[Y[ind]] -= 1
                    # don't split on the largest number, otherwise the right part is empty
                    if sorted_inds[i] == sorted_inds[-1]:
                        break
                    # split only when this is the last one of consequent identical numbers
                    if i == len(X) - 1 or X[ind, col] != X[sorted_inds[i + 1], col]:
                        se = self.get_se_of_split(smaller_Y_cnt, larger_Y_cnt)
                        if se < best_se:
                            val = X[ind, col]
                            best_se, best_col, best_val = se, col, val

            # Build left and right child nodes recursively
            if self.verbose:
                print(f"Split by value {best_val} of {best_col}th column")
            smaller_ind = X[:, best_col] <= best_val
            larger_ind = X[:, best_col] > best_val
            smaller_X = X[smaller_ind]
            larger_X = X[larger_ind]
            smaller_Y = Y[smaller_ind]
            larger_Y = Y[larger_ind]

            cur.col = best_col
            cur.val = best_val
            cur.left = self.build(smaller_X, smaller_Y, depth + 1)
            cur.right = self.build(larger_X, larger_Y, depth + 1)
        elif self.verbose:
            print("No split")
        return cur

    def _query(self, root, x):
        if root.col is None:
            return root
        elif x[root.col] > root.val:
            return self._query(root.right, x)
        return self._query(root.left, x)

    def query(self, root, x):
        return self._query(root, x).label

    def fit(self, X, Y):
        self.root = self.build(X, Y)

    def _predict(self, x):
        return self.query(self.root, x)

    def predict(self, X):
        return [self._predict(x) for x in X]

if __name__ == "__main__":
    def demonstrate(cart, X, Y, test_X, test_Y, desc):
        print(desc)
        console = Console(markup=False)
        cart.fit(X, Y)

        # show in table
        pred = cart.predict(test_X)
        table = Table('x', 'y', 'pred')
        for x, y, y_hat in zip(test_X, test_Y, pred):
            table.add_row(*map(str, [x, y, y_hat]))
        console.print(table)

    # -------------------------- Example 1 ----------------------------------------
    cart = RegressionCART(verbose=True)
    X = np.arange(1, 11).reshape(-1, 1)
    Y = np.array([4.5, 4.75, 4.91, 5.34, 5.8, 7.05, 7.90, 8.23, 8.70, 9.00])
    demonstrate(cart, X, Y, X, Y, "Example 1:")

    # -------------------------- Example 2 ----------------------------------------
    # show in table
    cart = RegressionCART(verbose=True)
    test_X = X + .5
    test_Y = np.zeros_like(Y) + nan
    demonstrate(cart, X, Y, test_X, test_Y, "Example 2:")

    # -------------------------- Example 3 ----------------------------------------
    cart = RegressionCART(verbose=True, max_depth=1)
    X = np.arange(1, 11).reshape(-1, 1)
    Y = np.array([4.5, 4.75, 4.91, 5.34, 5.8, 7.05, 7.90, 8.23, 8.70, 9.00])
    demonstrate(cart, X, Y, X, Y, "Example 3: CART stump")


    # -------------------------- Example 4 ----------------------------------------
    cart = RegressionCART(verbose=True, max_depth=3)
    X = np.arange(1, 11).reshape(-1, 1)
    Y = np.array([4.5, 4.75, 4.91, 5.34, 5.8, 7.05, 7.90, 8.23, 8.70, 9.00])
    demonstrate(cart, X, Y, X, Y, "Example 4: split twice")

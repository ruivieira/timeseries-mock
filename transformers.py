from pssm.dglm import BinomialDLM, CompositeDLM
import numpy as np


class BinomialTransformer(BinomialDLM):
    def __init__(self, structure, source):
        super(BinomialTransformer, self).__init__(structure, len(source) - 1)
        self._source = source

    def _sample_obs(self, mean):
        i = np.random.binomial(n=self._categories, p=mean)
        return self._source[i]


class CompositeTransformer(CompositeDLM):

    def observation(self, state):
        lambdas = np.dot(self._Ft, state)
        ys = []
        for i in range(len(self._dglms)):
            dglm = self._dglms[i]
            eta = dglm._eta(lambdas[i])
            ys.append(dglm._sample_obs(eta))

        return ys

from pssm.dglm import BinomialDLM


class BinomialTransformer(BinomialDLM):
    def __init__(self, structure, source):
        super(BinomialTransformer, self).__init__(structure, len(source) - 1)
        self._source = source

    def observation(self, state):
        i = super(BinomialTransformer, self).observation(state)
        return self._source[i]

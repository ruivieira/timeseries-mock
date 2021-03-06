"""parser_tests

This module contains tests for configuration parser
"""
import unittest

from nose.tools import assert_equals, assert_true

from pssm.dglm import NormalDLM, CompositeDLM
from pssm.structure import UnivariateStructure, MultivariateStructure
import yaml
import sys

sys.path.append("..")  # noqa: E402

from app import parse_configuration


def _parse_string(string):
    """
    Return a dictionary from a YAML string
    :param string:
    :return:
    """
    return yaml.load(string)


class ParserTests(unittest.TestCase):
    """Test suite for the parser
    """

    def continuous_mean_test(self):
        """Test if the continuous mean structure is parsed correctly.
        """
        conf = """
name: "Continuous Mean"
period: 0.5
structure:
  - type: mean
    start: 1000.0
    noise: 4.6
observations:
  type: continuous
  noise: 5.5
        """

        d = _parse_string(conf)

        model, state, period, name, _ = parse_configuration(d)

        assert_true(isinstance(model, NormalDLM), "model must be NormalDLM")
        assert_true(isinstance(model.structure, UnivariateStructure),
                    "structure must be UnivariateStructure")
        assert_equals(model.structure.F.shape, (1, 1),
                      "F has the wrong dimensions")
        assert_equals(model.structure.G.shape, (1, 1),
                      "G has the wrong dimensions")
        assert_equals(model.structure.W.shape, (1, 1),
                      "W has the wrong dimensions")

        assert_equals(state.shape, (),
                      "initial state has the wrong dimensions")

        assert_equals(period, 0.5, "period has the wrong value")
        assert_equals(name, "Continuous Mean", "name has the wrong value")

    def http_test(self):
        """Test if the continuous mean structure is parsed correctly.
        """
        conf = """
name: "HTTP log"
period: 0.1
compose:
    - structure:
      - type: mean
        start: 0.0
        noise: 0.01
      observations:
        type: categorical
        values: GET,POST,PUT
    - structure:
      - type: mean
        start: 0.0
        noise: 0.01
      - type: season
        start: 1.0
        period: 15
        noise: 0.2
      observations:
        type: categorical
        values: /site/page.htm,/site/index.htm,/internal/example.htm
    - replicate: 4
      structure:
      - type: mean
        start: 0.0
        noise: 2.1
      observations:
        type: categorical
        categories: 255
"""

        d = _parse_string(conf)

        model, state, period, name, _ = parse_configuration(d)

        assert_true(isinstance(model, CompositeDLM),
                    "model must be CompositeDLM")
        assert_true(isinstance(model.structure, MultivariateStructure),
                    "structure must be MultivariateStructure")
        assert_equals(model.structure.F.shape, (12, 6),
                      "F has the wrong dimensions")
        assert_equals(model.structure.G.shape, (12, 12),
                      "G has the wrong dimensions")
        assert_equals(model.structure.W.shape, (12, 12),
                      "W has the wrong dimensions")

        assert_equals(state.shape, (12,),
                      "initial state has the wrong dimensions")

        assert_equals(period, 0.1, "period has the wrong value")
        assert_equals(name, "HTTP log", "name has the wrong value")

    def harmonics_default_test(self):
        """Test if the default number of harmonics is correct
        """
        conf = """
name: "Continuous Mean"
period: 0.5
structure:
  - type: season
    start: 1000.0
    period: 100
    noise: 4.6
observations:
  type: continuous
  noise: 5.5"""

        d = _parse_string(conf)

        model, state, period, name, _ = parse_configuration(d)

        assert_true(isinstance(model, NormalDLM), "model must be NormalDLM")
        assert_true(isinstance(model.structure, UnivariateStructure),
                    "structure must be UnivariateStructure")
        assert_equals(model.structure.F.shape, (6, 1),
                      "F has the wrong dimensions")
        assert_equals(model.structure.G.shape, (6, 6),
                      "G has the wrong dimensions")
        assert_equals(model.structure.W.shape, (6, 6),
                      "W has the wrong dimensions")

        assert_equals(state.shape, (6,),
                      "initial state has the wrong dimensions")

        assert_equals(period, 0.5, "period has the wrong value")
        assert_equals(name, "Continuous Mean", "name has the wrong value")

    def harmonics_test(self):
        """Test if the passed number of harmonics is correct
        """
        conf = """
name: "Continuous Mean"
period: 0.5
structure:
  - type: season
    start: 1000.0
    harmonics: 5
    period: 100
    noise: 4.6
observations:
  type: continuous
  noise: 5.5"""

        d = _parse_string(conf)

        model, state, period, name, _ = parse_configuration(d)

        assert_true(isinstance(model, NormalDLM), "model must be NormalDLM")
        assert_true(isinstance(model.structure, UnivariateStructure),
                    "structure must be UnivariateStructure")
        assert_equals(model.structure.F.shape, (10, 1),
                      "F has the wrong dimensions")
        assert_equals(model.structure.G.shape, (10, 10),
                      "G has the wrong dimensions")
        assert_equals(model.structure.W.shape, (10, 10),
                      "W has the wrong dimensions")

        assert_equals(state.shape, (10,),
                      "initial state has the wrong dimensions")

        assert_equals(period, 0.5, "period has the wrong value")
        assert_equals(name, "Continuous Mean", "name has the wrong value")

    def arma_default_test(self):
        """Test if the default ARMA dimensions are correct
        """
        conf = """
name: "ARMA"
period: 0.5
structure:
  - type: arma
    start: 1000.0
    noise: 4.6
observations:
  type: continuous
  noise: 5.5"""

        d = _parse_string(conf)

        model, state, period, name, _ = parse_configuration(d)

        assert_true(isinstance(model, NormalDLM), "model must be NormalDLM")
        assert_true(isinstance(model.structure, UnivariateStructure),
                    "structure must be UnivariateStructure")
        assert_equals(model.structure.F.shape, (1, 1),
                      "F has the wrong dimensions")
        assert_equals(model.structure.G.shape, (1, 1),
                      "G has the wrong dimensions")
        assert_equals(model.structure.W.shape, (1, 1),
                      "W has the wrong dimensions")

        assert_equals(state.shape, (),
                      "initial state has the wrong dimensions")

        assert_equals(period, 0.5, "period has the wrong value")
        assert_equals(name, "ARMA", "name has the wrong value")

    def arma_test(self):
        """Test if the ARMA(3) dimensions are correct
        """
        conf = """
name: "ARMA(3)"
period: 0.5
structure:
  - type: arma
    start: 1000.0
    coefficients: 0.1,0.3,0.5
    noise: 4.6
observations:
  type: continuous
  noise: 5.5"""

        d = _parse_string(conf)

        model, state, period, name, _ = parse_configuration(d)

        assert_true(isinstance(model, NormalDLM), "model must be NormalDLM")
        assert_true(isinstance(model.structure, UnivariateStructure),
                    "structure must be UnivariateStructure")
        assert_equals(model.structure.F.shape, (3, 1),
                      "F has the wrong dimensions")
        assert_equals(model.structure.G.shape, (3, 3),
                      "G has the wrong dimensions")
        assert_equals(model.structure.W.shape, (3, 3),
                      "W has the wrong dimensions")

        assert_equals(state.shape, (3,),
                      "initial state has the wrong dimensions")

        assert_equals(period, 0.5, "period has the wrong value")
        assert_equals(name, "ARMA(3)", "name has the wrong value")

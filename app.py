import argparse
import json
import logging
import os
import time
from functools import reduce

import numpy as np
import yaml

from kafka import KafkaProducer
from pssm.dglm import NormalDLM, PoissonDLM, BinomialDLM
from pssm.structure import UnivariateStructure
from scipy.stats import multivariate_normal as mvn

from transformers import BinomialTransformer, CompositeTransformer


def _read_conf(conf):
    """
    Convert a YAML configuration into a dictionary
    :param conf: The configuration filename
    :return: A dictionary
    """
    with open(conf, 'r') as stream:
        try:
            d = yaml.load(stream)
            return d
        except yaml.YAMLError as exc:
            print(exc)


def _parse_component(conf):
    """
    Parse an individual record of the structure configuration
    :param conf:
    :return:
    """
    type = conf['type']
    if  type == 'mean':
        print("Add a LC structure")
        W = float(conf['noise'])
        m0 = [conf['start']]
        structure = UnivariateStructure.locally_constant(W)
    elif type == 'season':
        # check if number of harmonics is defined
        if 'harmonics' in conf:
            nharmonics = conf['harmonics']
        else:
            nharmonics = 3
        W = np.identity(2 * nharmonics) * float(conf['noise'])
        m0 = [conf['start']] * W.shape[0]
        period = int(conf['period'])
        structure = UnivariateStructure.cyclic_fourier(period=period,
                                                       harmonics=nharmonics,
                                                       W=W)
    else:
        raise ValueError("Unknown component type '{}'".format(conf['type']))
    return structure, m0


def _parse_structure(conf):
    structures = []
    m0 = []

    for structure in conf:
        _structure, _m0 = _parse_component(structure)
        m0.extend(_m0)
        structures.append(_structure)

    m0 = np.array(m0)
    C0 = np.eye(len(m0))

    return reduce((lambda x, y: x + y), structures), m0, C0


def _parse_composite(conf):
    models = []
    prior_mean = []
    for element in conf:
        if 'replicate' in element:
            structure, m0, C0 = _parse_structure(element['structure'])
            prior_mean.extend([m0] * element['replicate'])
            model = _parse_observations(element['observations'], structure)
            models.extend([model] * element['replicate'])
        else:
            structure, m0, C0 = _parse_structure(element['structure'])
            prior_mean.extend(m0)
            model = _parse_observations(element['observations'], structure)
            models.append(model)
    print(models)
    model = CompositeTransformer(*models)
    m0 = np.array(prior_mean)
    C0 = np.eye(len(m0))
    return model, m0, C0


def _parse_observations(obs, structure):
    if obs['type'] == 'continuous':
        model = NormalDLM(structure=structure, V=obs['noise'])
    elif obs['type'] == 'discrete':
        model = PoissonDLM(structure=structure)
    elif obs['type'] == 'categorical':
        if 'values' in obs:
            values = obs['values'].split(',')
            model = BinomialTransformer(structure=structure, source=values)
        elif 'categories' in obs:
            model = BinomialDLM(structure=structure,
                                categories=obs['categories'])
        else:
            raise ValueError("Categorical models must have either 'values' "
                             "or 'categories'")
    else:
        raise ValueError("Model type {} is not valid".format(obs['type']))
    return model


def parse_configuration(conf):
    """
    Parse a YAML configuration string into an state-space model
    :param conf:
    :return: A state-space model
    """

    if 'compose' in conf:
        model, m0, C0 = _parse_composite(conf['compose'])
    else:
        structure, m0, C0 = _parse_structure(conf['structure'])
        model = _parse_observations(conf['observations'], structure)

    state = mvn(m0, C0).rvs()

    period = float(conf['period'])

    name = conf['name']

    return model, state, period, name


def build_message(name, value):
    return json.dumps({
        'name': name,
        'value': value
    }).encode()


def main(args):
    logging.info('brokers={}'.format(args.brokers))
    logging.info('topic={}'.format(args.topic))
    logging.info('conf={}'.format(args.conf))

    if args.conf:
        model, state, period, name = parse_configuration(_read_conf(args.conf))
    else:
        state = np.array([0])
        lc = UnivariateStructure.locally_constant(1.0)
        model = NormalDLM(structure=lc, V=1.4)
        period = 2.0
        name = 'data'

    logging.info('creating kafka producer')
    producer = KafkaProducer(bootstrap_servers=args.brokers)

    logging.info('sending lines (frequency = {})'.format(period))
    while True:
        y = model.observation(state)
        state = model.state(state)
        message = build_message(name, y)
        print("message = {}".format(message))
        producer.send(args.topic, message)
        time.sleep(period)


def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') is not '' else default


def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.topic = get_arg('KAFKA_TOPIC', args.topic)
    args.conf = get_arg('CONF', args.conf)
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('starting timeseries-mock emitter')
    parser = argparse.ArgumentParser(
        description='timeseries data simulator for Kafka')
    parser.add_argument(
        '--brokers',
        help='The bootstrap servers, env variable KAFKA_BROKERS',
        default='localhost:9092')
    parser.add_argument(
        '--topic',
        help='Topic to publish to, env variable KAFKA_TOPIC',
        default='data')
    parser.add_argument(
        '--conf',
        type=str,
        help='Configuration file (YAML)',
        default=None)
    args = parse_args(parser)
    main(args)
    logging.info('exiting')

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


def _read_conf(conf):
    with open(conf, 'r') as stream:
        try:
            d = yaml.load(stream)
            print(d)
            return d
        except yaml.YAMLError as exc:
            print(exc)


def _parse_structure(conf):
    structures = []
    m0 = []

    for structure in conf:
        if structure['type'] == 'mean':
            print("Add a LC structure")
            W = float(structure['noise'])
            m0.append(structure['start'])
            structures.append(UnivariateStructure.locally_constant(W))
        if structure['type'] == 'season':
            W = np.identity(6) * float(structure['noise'])
            m0 += [structure['start']] * W.shape[0]
            period = int(structure['period'])
            structures.append(
                UnivariateStructure.cyclic_fourier(period=period, harmonics=3,
                                                   W=W))
    m0 = np.array(m0)
    C0 = np.eye(len(m0))

    return reduce((lambda x, y: x + y), structures), m0, C0


def _parse_observations(obs, structure):
    if obs['type'] == 'continuous':
        model = NormalDLM(structure=structure, V=obs['noise'])
    elif obs['type'] == 'discrete':
        model = PoissonDLM(structure=structure)
    elif obs['type'] == 'categorical':
        model = BinomialDLM(structure=structure, categories=obs['categories'])
    return model


def parse_configuration(conf):
    """
    Parse a YAML configuration file into an state-space model
    :param conf:
    :return: A state-space model
    """

    conf_dict = _read_conf(conf)

    print(conf_dict)

    structure, m0, C0 = _parse_structure(conf_dict['structure'])

    model = _parse_observations(conf_dict['observations'], structure)

    state = mvn(m0, C0).rvs()

    period = float(conf_dict['period'])

    name = conf_dict['name']

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
        model, state, period, name = parse_configuration(args.conf)
    else:
        state = np.array([0])
        lc = UnivariateStructure.locally_constant(1.0)
        model = NormalDLM(structure=lc, V=1.4)
        period = 2.0
        name = 'default name'

    logging.info('creating kafka producer')
    producer = KafkaProducer(bootstrap_servers=args.brokers)

    logging.info('sending lines (frequency = {})'.format(period))
    while True:
        y = model.observation(state)
        state = model.state(state)
        producer.send(args.topic, build_message(name, y))
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
        default='bones-brigade')
    parser.add_argument(
        '--conf',
        type=str,
        help='Configuration file (YAML)',
        default=None)
    args = parse_args(parser)
    main(args)
    logging.info('exiting')

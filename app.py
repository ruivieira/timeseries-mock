import argparse
import logging
import os
import time
import numpy as np

from kafka import KafkaProducer
from pssm.dglm import NormalDLM
from pssm.structure import UnivariateStructure


def parse_configuration(conf):
    state = np.array([0])
    lc = UnivariateStructure.locally_constant(1.0)
    model = NormalDLM(structure=lc, V=1.4)
    return model


def main(args):
    logging.info('brokers={}'.format(args.brokers))
    logging.info('topic={}'.format(args.topic))
    logging.info('rate={}'.format(args.rate))
    logging.info('conf={}'.format(args.conf))

    if args.conf:
        model = parse_configuration(args.conf)
    else:
        state = np.array([0])
        lc = UnivariateStructure.locally_constant(1.0)
        model = NormalDLM(structure=lc, V=1.4)

    logging.info('creating kafka producer')
    producer = KafkaProducer(bootstrap_servers=args.brokers)

    logging.info('sending lines')
    while True:
        y = model.observation(state)
        state = model.state(state)
        producer.send(args.topic, str(y).encode())
        time.sleep(1.0 / args.rate)


def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') is not '' else default


def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.topic = get_arg('KAFKA_TOPIC', args.topic)
    args.rate = get_arg('RATE', args.rate)
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
        '--rate',
        type=int,
        help='Lines per second, env variable RATE',
        default=3)
    parser.add_argument(
        '--conf',
        type=str,
        help='Configuration file (YAML)',
        default=None)
    args = parse_args(parser)
    main(args)
    logging.info('exiting')

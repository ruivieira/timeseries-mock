# timeseries-mock

## Install

To setup the data generator on OpenShift simply use the `s2i` by running:

```bash
oc new-app centos/python-36-centos7~https://github.com/ruivieira/timeseries-mock \
  -e KAFKA_BROKERS=kafka:9092 \
  -e KAFKA_TOPIC=example \
  -e CONF=examples/mean_continuous.yml
  --name=emitter
```

This will deploy the data generator, which will emit data (modelled as defined by
the configuration file `examples/mean_continuous.yml`) into the Kafka topic `example`.

## Data model configuration

To configure a data stream, you must specify both the structure of the time-series
as well and the type of observation in a `.yml` file.

### Structure

The structure can be specified by specifiying several fundamental components,
which are ultimately composed to create a single structure.
Some core components are:

#### Mean

This specifies an underlying mean. Using a single "mean" component will result
in a random-walk type time-series:

```yaml
structure:
  - type: mean
    start: 0.0
    noise: 1.5
```

All components need a `start` and `noise` value. The start specifies the general
probable area for the series start and `noise` specifies how much the component
will vary over time.

#### Seasonal

This will represent a seasonal component:

```yaml
structure:
  - type: season
    period: 200
    start: 0.0
    noise: 0.7
```

The `period` represents how often will the season repeat. Note that this is relative
to your specified `rate`.

That is, if your `rate` is `0.1` (the generator will emit new data every `0.1` seconds),
then a `period` of `20` means that the season will last `rate * period = 2` seconds.
But if your `rate` is `100` seconds, the season will repeat every `33.33` minutes.


### Composing

Structures can be composed simply by listing them under `structure` in the `.yml` file.
For instance, composing the above mean and seasonality examples would simply be:

```yaml
structure:
  - type: mean     # component 1
    start: 0.0
    noise: 1.5
  - type: season   # component 2
    period: 200
    start: 0.0
    noise: 0.7    
```

## Acknowledgements

This project is based on [elmiko](https://github.com/elmiko)'s 
[Kafka OpenShift Python Emitter](https://github.com/bones-brigade/kafka-openshift-python-emitter), 
a part of the [Bones Brigade](https://github.com/bones-brigade) set of OpenShift
application skeletons.
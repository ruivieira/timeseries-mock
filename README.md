[![Build Status](https://travis-ci.org/ruivieira/timeseries-mock.svg?branch=master)](https://travis-ci.org/ruivieira/timeseries-mock)

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

### Observations

The observation type can be configured using the `observations` key.
The main supported observation types are detailed below.

#### Continuous

Continuous observations allow to model any floating point type measure. Note that
this is not bound by upper or lower limits (range `]-inf, +inf[`<sup>[1]</sup>). If you use `continuous`
to simulate, say, temperature readings from a sensor, keep in mind that the values might drift
to very high or very low depending on the structure. <sup>[2]</sup>  

```yaml
observations:
  - type: continuous
    noise: 1.5
```

#### Discrete

Discrete observations allow to model any integer measure in the range `[0, +inf[.`
The notes about drift in the continuous section also apply.

```yaml
observations:
  - type: discrete
```

Please note that (at the moment) discrete observations only allow the `noise` to be specified
at the structure level, since they are based on a Poisson model.

#### Categorical

Categorical observations allow to model any set of categories represented by an integer.

```yaml
observations:
 - type: categorical
   categories: 16
```

The typical example would be setting `categories` to `1`. This would simulate
a stream of "binary" values `0` and `1`. In the above example, setting `categories`
to `16` would output a stream taking any value from `[0, 1, 2, ..., 16]`.

A variant of this generator consists in passing a list of values directly.
Let's assume we wanted to generate a stream of random DNA nucleotides, that is,
`C,T,A,G`. This corresponds to four categories which we can specify in the `values` field:

```yaml
observations:
 - type: categorical
   values: C,T,A,G
```

Comma-separated values are taken as the categories, without needing to specify anything else.
The output is the a random element of `values` at each timepoint, in this case the time-series
would be:

```
G -> T -> G -> T -> A -> A -> A -> C -> ...
```

### A complete example

A full configuration file would look something like this:

```yaml
name: "status"
rate: 0.1
structure:
  - type: mean
    start: 0.0
    noise: 0.5
  - type: season
    period: 600
    start: 0.0
    noise: 1.7    
observations:
  - type: categorical
    values: pass,fail
```

This configuration generate a stream of values `pass` or `fail` with a rate one value every 0.1 seconds, with a random walk like mean and a cyclic pattern every minute.

### Multivariate data

The previous example was for a univariate observation, however in a real-world application it is very likely we might need to use multivariate data.

To compose a multivariate data model we simply use the model specification above and add as many models together as we want.

## Acknowledgements

This project is based on [elmiko](https://github.com/elmiko)'s 
[Kafka OpenShift Python Emitter](https://github.com/bones-brigade/kafka-openshift-python-emitter), 
a part of the [Bones Brigade](https://github.com/bones-brigade) set of OpenShift
application skeletons.

[1] - whatever the minimum and maximum double/float values are, of course

[2] - In this case I suggest using some auto-regressive component in the structure.

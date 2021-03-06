[![Build Status](https://travis-ci.org/ruivieira/timeseries-mock.svg?branch=master)](https://travis-ci.org/ruivieira/timeseries-mock)

# timeseries-mock

## Install

To setup the data generator on OpenShift simply use the `s2i` by running:

```bash
oc new-app centos/python-36-centos7~https://github.com/ruivieira/timeseries-mock \
  -e KAFKA_BROKERS=kafka:9092 \
  -e KAFKA_TOPIC=example \
  -e CONF=examples/mean_continuous.yml \
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

The seasonal component Fourier representation consists of `n` harmonics, which can be either specified
in the configuration as:

```yaml
structure:
  - type: season
    # ...
    harmonics: 6
    # ...
```

or just default to `n=3` harmonics if not specified.



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

Continuous observations allow us to model any floating point type measure. Note that
this is not bound by upper or lower limits (range `]-inf, +inf[`<sup>[1]</sup>). If you use `continuous`
to simulate, say, temperature readings from a sensor, keep in mind that the simulated readings might drift
to very high or very low values depending on the structure. <sup>[2]</sup>  

```yaml
observations:
  - type: continuous
    noise: 1.5
```

#### Discrete

Discrete observations allow us to model any integer measure in the range `[0, +inf[.`
The notes about drift in the continuous section also apply.

```yaml
observations:
  - type: discrete
```

Please note that (at the moment) the discrete case only allows the `noise` to be specified
at the structure level, since the observations are based on a Poisson model.

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

This configuration generate a stream of values `pass` or `fail` with a rate one value every 0.1 seconds, with a random-walk-like mean and a cyclic pattern every minute.

### Multivariate data

The previous example was for a univariate observation, however in a real-world application it is very likely we might need to use multivariate data.

To compose a multivariate data model we simply use the model specification above and add as many models together as we want.

To define a multivariate model we declare the individual components inside a `compose` clause. For instance, to declare a bivariate continous stream a minimal example would be:

```yaml
name: "bivariate"
rate: 0.5
compose:
  - structure:          # component 1
    - type: mean
    start: 0.0
    noise: 0.5
  - observations:
    - type: continuous
    noise: 0.5
  - structure:          # component 2
    - type: mean
    start: 5.0
    noise: 3.7
  - observations:
    - type: continuous
    noise: 1.5
```

This would output a stream of bivariate observations such as

```
[-0.6159691811574524, 6.70524660538598]
[0.09028869591370958, 6.519194818247104]
[-0.1980867909796035, 6.503466768530726]
[0.0063771543008148135, 5.2229932206447405]
...
```

In the specific case where you wish to simulate a multivariate observation with components that follow the same structure, you can use the shorthand `replicate`. The observation is then replicated `n` times.
For example, to simulate bivariate samples where the components had the same underlying structure, we could write:

```yaml
name: "bivariate"
rate: 0.5
compose:
  - replicate: 2
    structure:
      - type: mean
        start: 0.0
        noise: 0.5
    observations:
      - type: continuous
        noise: 0.5
```

#### A more complex example

In this example we will generate a fake HTTP log stream. The multivariate data will contain a request type (`GET`, `POST` or `PUT`), a URL from a provided list and random IP address.
We want the URL to have seasonality, that is, users will tend more to a certain URL than others over time in a cyclic fashion.

We can define this model as:

```yaml
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
```

An example output would be

```
["PUT", "/internal/example.htm", 171, 158, 59, 89]
["GET", "/internal/example.htm", 171, 253, 71, 146]
["PUT", "/internal/example.htm", 224, 252, 9, 156]
["POST", "/site/index.htm", 143, 253, 6, 126]
["POST", "/site/page.htm", 238, 254, 2, 48]
["GET", "/site/page.htm", 228, 252, 52, 126]
["POST", "/internal/example.htm", 229, 234, 103, 233]
["GET", "/internal/example.htm", 185, 221, 109, 195]
...
```

## Acknowledgements

This project is based on [elmiko](https://github.com/elmiko)'s 
[Kafka OpenShift Python Emitter](https://github.com/bones-brigade/kafka-openshift-python-emitter), 
a part of the [Bones Brigade](https://github.com/bones-brigade) set of OpenShift
application skeletons.

[1] - whatever the minimum and maximum double/float values are, of course

[2] - In this case I suggest using some auto-regressive component in the structure.

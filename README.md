# ReBench: Execute and Document Benchmarks Reproducibly

[![Build Status](https://travis-ci.org/smarr/ReBench.svg?branch=master)](https://travis-ci.org/smarr/ReBench)
[![Documentation](https://readthedocs.org/projects/rebench/badge/?version=latest)](https://rebench.readthedocs.io/)
[![Codacy Quality](https://api.codacy.com/project/badge/Grade/2f7210b65b414100be03f64fe6702d66)](https://www.codacy.com/app/smarr/ReBench)
[![Coverage](https://coveralls.io/repos/github/smarr/ReBench/badge.svg?branch=master)](https://coveralls.io/github/smarr/ReBench?branch=master)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1311762.svg)](https://doi.org/10.5281/zenodo.1311762)

ReBench is a tool to run and document benchmark experiments.
Currently, it is mostly used for benchmarking language implementations,
but it can be used to monitor the performance of all
kinds of other applications and programs, too.

The ReBench [configuration format][docs] is a text format based on [YAML](http://yaml.org/).
A configuration file defines how to build and execute a set of *experiments*,
i.e. benchmarks.
It describes which executable was used, which parameters were given
to the benchmarks, and the number of iterations to be used to obtain 
statistically reliable results.

With this approach, the configuration contains all benchmark-specific
information to reproduce a benchmark run. However, it does not capture
the whole system.

The data of all benchmark runs is recorded in a data file for later analysis.
Important for long-running experiments, benchmarks can be aborted and
continued at a later time.

ReBench focuses on the execution aspect and does not provide advanced
analysis facilities itself. Instead, the recorded results should be processed
by dedicated tools such as scripts for statistical analysis in R, Python, etc,
or [Codespeed][1], for continuous performance tracking.

The documentation for ReBench is hosted at [http://rebench.readthedocs.io/][docs].

## Goals and Features

ReBench is designed to

 - enable reproduction of experiments;
 - document all benchmark parameters;
 - provide a flexible execution model,
   with support for interrupting and continuing benchmarking;
 - enable the definition of complex sets of comparisons and their flexible execution;
 - report results to continuous performance monitoring systems, e.g., [Codespeed][1];
 - provide basic support for building/compiling benchmarks/experiments on demand;
 - be extensible to parse output of custom benchmark harnesses.

## Non-Goals

ReBench isn't

 - a framework for microbenchmarks.
   Instead, it relies on existing harnesses and can be extended to parse their
   output.
 - a performance analysis tool. It is meant to execute experiments and
   record the corresponding measurements.
 - a data analysis tool. It provides only a bare minimum of statistics,
   but has an easily parseable data format that can be processed, e.g., with R.

## Installation and Usage

<a id="install"></a>

ReBench is implemented in Python and can be installed via pip:

```bash
pip install rebench
```

A minimal configuration file looks like this:

```yaml
# this run definition will be chosen if no parameters are given to rebench
default_experiment: all
default_data_file: 'example.data'

# a set of suites with different benchmarks and possibly different settings
benchmark_suites:
    ExampleSuite:
        gauge_adapter: RebenchLog
        command: Harness %(benchmark)s %(input)s %(variable)s
        input_sizes: [2, 10]
        variable_values:
            - val1
        benchmarks:
            - Bench1
            - Bench2

# a set of executables for the benchmark execution
executors:
    MyBin1:
        path: bin
        executable: test-vm1.py %(cores)s
        cores: [1]
    MyBin2:
        path: bin
        executable: test-vm2.py

# combining benchmark suites and executions
experiments:
    Example:
        suites:
          - ExampleSuite
        executions:
            - MyBin1
            - MyBin2
```

Saved as `test.conf`, this configuration could be executed with ReBench as follows:

```bash
rebench test.conf
```

See the documentation for details: [http://rebench.readthedocs.io/][docs].

## Support and Contributions

In case you encounter issues,
please feel free to [open an issue](https://github.com/smarr/rebench/issues/new)
so that we can help.

For contributions, we use the [normal Github flow](https://guides.github.com/introduction/flow/)
of pull requests, discussion, and revisions. For larger contributions,
it is likely useful to discuss them upfront in an issue first.

## Use in Academia

If you use ReBench for research and in academic publications, please consider
citing it.

The preferred citation is:

```bibtex
@misc{ReBench:2018,
  author = {Marr, Stefan},
  doi = {10.5281/zenodo.1311762},
  month = {August},
  note = {Version 1.0},
  publisher = {GitHub},
  title = {ReBench: Execute and Document Benchmarks Reproducibly},
  year = 2018
}
```

Some publications that have been using ReBench include:

 - [Fully Reflective Execution Environments: Virtual Machines for More Flexible Software](https://doi.org/10.1109%2fTSE.2018.2812715), G. Chari et al. 2018.
 - [Building efficient and highly run-time adaptable virtual machines](http://lafhis.dc.uba.ar/sites/default/files/papers/buildingEfficientReflectiveVMs.pdf), G. Chari et al. 2017.
 - [Improving live debugging of concurrent threads through thread histories](https://doi.org/10.1016/j.scico.2017.10.005), M. Leske et al. 2017.
 - [Adaptive Just-in-time Value Class Optimization for Lowering Memory Consumption and Improving Execution Time Performance](https://arxiv.org/pdf/1606.06726) T. Pape et al. 2016
 - [Cross-Language Compiler Benchmarking---Are We Fast Yet?](http://stefan-marr.de/papers/dls-marr-et-al-cross-language-compiler-benchmarking-are-we-fast-yet/), S. Marr et al. 2016.
 - [Tracing vs. Partial Evaluation: Comparing Meta-Compilation Approaches for Self-Optimizing Interpreters](http://stefan-marr.de/papers/oopsla-marr-ducasse-meta-tracing-vs-partial-evaluation/), S. Marr, S. Ducasse. 2015.
 - [Zero-Overhead Metaprogramming: Reflection and Metaobject Protocols Fast and without Compromises](http://stefan-marr.de/papers/pldi-marr-et-al-zero-overhead-metaprogramming/), S. Marr et al. 2015.
 - [Pycket: a tracing JIT for a functional language](https://www.hpi.uni-potsdam.de/hirschfeld/publications/media/BaumanBolzHirschfeldKirilichevPapeSiekTobinHochstadt_2015_PycketATracingJitForAFunctionalLanguage_AcmDL.pdf), S. Bauman et al. 2015.
 - [Adaptive just-in-time value class optimization: transparent data structure inlining for fast execution](http://hpi.uni-potsdam.de/hirschfeld/publications/media/PapeBolzHirschfeld_2015_AdaptiveJustInTimeValueClassOptimization_AcmDL.pdf), T. Pape et al. 2015. 
 - [Meta-tracing makes a fast Racket](https://www.hpi.uni-potsdam.de/hirschfeld/publications/media/BolzPapeSiekTobinHochstadt_2014_MetaTracingMakesAFastRacket_AuthorsVersion.pdf), C. F. Bolz et al. 2014.
 - [Cloud PARTE: Elastic Complex Event Processing based on Mobile Actors](http://soft.vub.ac.be/~smarr/downloads/agere13-swalens-et-al-cloud-parte-elastic-complex-event-processing-based-on-mobile-actors.pdf), J. Swalens et al. 2013.
 - [Identifying A Unifying Mechanism for the Implementation of Concurrency Abstractions on Multi-Language Virtual Machines](http://www.stefan-marr.de/downloads/tools12-smarr-dhondt-identifying-a-unifying-mechanism-for-the-implementation-of-concurrency-abstractions-on-multi-language-virtual-machines.pdf), S. Marr, T. D'Hondt. 2012.
 - [Insertion Tree Phasers: Efficient and Scalable Barrier Synchronization for Fine-grained Parallelism](http://www.stefan-marr.de/downloads/hpcc2010-marr-etal-insertion-tree-phasers.pdf), S. Marr et al. 2011.

[1]: https://github.com/tobami/codespeed/
[docs]: http://rebench.readthedocs.io/

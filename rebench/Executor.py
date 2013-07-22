# Copyright (c) 2009 Stefan Marr <http://www.stefan-marr.de/>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
from __future__ import with_statement

import logging
import subprocess
import SubprocessWithTimeout as subprocess_timeout
import time

from model.run_id import RunId

from Statistics import StatisticProperties

from contextpy import layer, activelayers, after,before
# proceed, activelayer, around, base, globalActivateLayer, globalDeactivateLayer

benchmark = layer("benchmark")
profile = layer("profile")
quick   = layer("quick")

class Executor:
    
    def __init__(self, configurator, dataAggregator, reporter = None):
        self._configurator = configurator
        self._data = dataAggregator
        self._reporter = reporter
        self._jobs = [] # the list of configurations to be executed
    
    def _construct_cmdline(self, runId, perf_reader):
        cmdline  = ""
                
        if self._configurator.options.use_nice:
            cmdline += "nice -n-20 "
        
        cmdline += perf_reader.acquire_command(runId.cmdline())
                
        return cmdline
    
    def _exec_configuration(self, runId):
        self._reporter.startConfiguration(runId)
        
        perf_reader = self._get_performance_reader_instance(runId.cfg.performance_reader)
        
        cmdline = self._construct_cmdline(runId, perf_reader)
        
        #error = (consequent_erroneous_runs, erroneous_runs)    
        terminate, error = self._check_termination_condition(runId, (0, 0))
        stats = StatisticProperties(self._data.getDataSet(runId),
                                    self._configurator.statistics['confidence_level'])
        
        # now start the actual execution
        while not terminate:
            terminate, error = self._generate_data_point(cmdline, error, perf_reader, runId)
            
            stats = StatisticProperties(self._data.getDataSet(runId),
                                        self._configurator.statistics['confidence_level'])
            
            logging.debug("Run: #%d"%(stats.numSamples))

        self._reporter.configurationCompleted(runId, stats, cmdline)
        
    @before(quick)
    def _exec_configuration(self, runId):
        self._quickStartTime = time.time()

    @before(benchmark)
    def _exec_configuration(self, runId):
        logging.debug("Statistic cfg: min_runs=%s, max_runs=%s"%(self._configurator.statistics["min_runs"],
                                                                 self._configurator.statistics["max_runs"]))
    
    def _get_performance_reader_instance(self, reader):
        # depending on how ReBench was executed, the name might one of the two 
        try:
            p = __import__("rebench.performance", fromlist=reader)
        except ImportError:
            p = __import__("performance", fromlist=reader)
        
        return getattr(p, reader)()
        
    def _generate_data_point(self, cmdline, error, perf_reader, runId):
        # execute the external program here
        (returncode, output, _) = subprocess_timeout.run(cmdline, cwd=runId.cfg.suite['location'],
                                                         stdout=subprocess.PIPE,
                                                         stderr=subprocess.STDOUT,
                                                         shell=True, timeout=runId.cfg.suite.get('max_runtime', -1))
        
        if returncode != 0:
            (consequent_erroneous_runs, erroneous_runs) = error
            
            consequent_erroneous_runs += 1
            erroneous_runs += 1
            
            error = (consequent_erroneous_runs, erroneous_runs)
            self._reporter.runFailed(runId, cmdline, returncode, output)
        else:
            error = self._eval_output(output, runId, perf_reader, error, cmdline)
        
        return self._check_termination_condition(runId, error)
    
    def _eval_output(self, output, runId, perf_reader, error, cmdline):
        return error
    
    @after(benchmark)
    def _eval_output(self, output, runId, perf_reader, error, cmdline, __result__):
        consequent_erroneous_runs, erroneous_runs = error
        
        try:
            (total, dataPoints) = perf_reader.parse_data(output)
            #self.benchmark_data[self.current_vm][self.current_benchmark].append(exec_time)
            self._data.addDataPoints(runId, dataPoints)
            consequent_erroneous_runs = 0
            logging.debug("Run %s:%s result=%s"%(runId.cfg.vm['name'], runId.cfg.name, total))
            
        except RuntimeError:
            consequent_erroneous_runs += 1
            erroneous_runs += 1
            self._reporter.runFailed(runId, cmdline, 0, output)
            
        return consequent_erroneous_runs, erroneous_runs
        
        
    def _check_termination_condition(self, runId, error):
        return False, error
    
    @after(profile)
    def _check_termination_condition(self, runId, error, __result__):
        return True, error
    
    @after(benchmark)
    def _check_termination_condition(self, runId, error, __result__):
        terminate, (consequent_erroneous_runs, erroneous_runs) = __result__
        
        numDataPoints = self._data.getNumberOfDataPoints(runId)
        cfg = runId.cfg
        
        if consequent_erroneous_runs >= 3:
            logging.error("Three runs of %s have failed in a row, benchmark is aborted"%(cfg.name))
            terminate = True
        elif erroneous_runs > numDataPoints / 2 and erroneous_runs > 6:
            logging.error("Many runs of %s are failing, benchmark is aborted."%(cfg.name))
            terminate = True
        elif numDataPoints >= self._configurator.statistics["max_runs"]:
            logging.debug("Reached max_runs for %s"%(cfg.name))
            terminate = True
        elif (numDataPoints >= self._configurator.statistics["min_runs"]
              and self._confidence_reached(runId)):
            logging.debug("Confidence is reached for %s"%(cfg.name))
            terminate = True
        
        return terminate, (consequent_erroneous_runs, erroneous_runs)
    
    @after(quick)
    def _check_termination_condition(self, runId, error, __result__):
        terminate, error = __result__
        cfg = runId.cfg
        
        numDataPoints = self._data.getNumberOfDataPoints(runId)
        
        if numDataPoints >= self._configurator.quick_runs["max_runs"]:
            logging.debug("Reached max_runs for %s"%(cfg.name))
            terminate = True
        elif (numDataPoints > self._configurator.quick_runs["min_runs"]
              and time.time() - self._quickStartTime > self._configurator.quick_runs["max_time"]):
            logging.debug("Maximum runtime is reached for %s"%(cfg.name))
            terminate = True
        
        return terminate, error
   
                
    def _confidence_reached(self, runId):
        
        stats = StatisticProperties(self._data.getDataSet(runId),
                                    self._configurator.statistics['confidence_level'])
        
        logging.debug("Run: %d, Mean: %f, current error: %f, Interval: [%f, %f]"%(
                      stats.numSamples, stats.mean,
                      stats.confIntervalSize, stats.confIntervalLow, stats.confIntervalHigh))
        
        if stats.confIntervalSize < self._configurator.statistics["error_margin"]:
            return True
        else:
            return False
    
    def _generate_all_configs(self, benchConfigs):
        configurations = set()
        
        for cfg in benchConfigs:
            for cores in cfg.suite['cores']:
                input_sizes = cfg.suite.get('input_sizes', [None])
                for input_size in input_sizes:
                    if len(cfg.suite['variable_values']):
                        for var_val in cfg.suite['variable_values']:
                            configurations.add(RunId.create(cfg, (cores, input_size, var_val)))
                    else:
                        configurations.add(RunId.create(cfg, (cores, input_size, None)))
        
        return list(configurations)
    
    def execute(self):
        benchConfigs = self._configurator.getBenchmarkConfigurations()
        configs = self._generate_all_configs(benchConfigs)
        
        self._reporter.setTotalNumberOfConfigurations(len(configs))
        
        for runId in configs:
            for action in runId.actions():
                with activelayers(layer(action)):
                    self._exec_configuration(runId)
                    
        self._reporter.jobCompleted(configs, self._data)


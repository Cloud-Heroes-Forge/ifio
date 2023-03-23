import json
from datetime import datetime
import subprocess
from typing import Any, List, Union
import pandas as pd
import logging
import configparser
from utils.atp import ATP 
from os import path

class FioBase:
    """
    
    """
    def __init__(self):
        self.read_throughput: float = 0
        self.read_latency: float = 0
        self.read_iops: float = 0

        self.write_throughput: float = 0
        self.write_latency: float = 0
        self.write_iops: float = 0

        self.read_percent: float = 0

        self.total_throughput: float = 0
        self.total_iops: float = 0

        self.avg_latency: float = 0
        self.timestamp: datetime = None
        self.duration: float = 0

        self.blocksize: str = None
        self.io_depth: int = 0
        # self.raw_stdout: str = None
        # self.ERROR_CODE = None

        self.atp: float = 0
        self.ort: float = 0
        self.summarize()

    def summarize(self) -> None:
        self.total_iops = self.write_iops + self.read_iops
        self.total_throughput = self.read_throughput + self.write_throughput
        if self.read_latency == 0:
            self.avg_latency = self.write_latency
        elif self.write_latency == 0:
            self.avg_latency = self.read_latency
        else:
            self.avg_latency = ((self.read_latency * self.read_iops) + (self.write_latency * self.write_iops)) / self.total_iops
        self.read_percent = round((self.read_iops / self.total_iops) * 100 if self.total_iops != 0 else 0)

    def to_dict(self) -> dict:
        return self.__dict__
    
    def to_json(self) -> str:
        try: 
            return json.dumps(self.__dict__)
        except json.JSONDecodeError as e:
            raise Exception(f"Error converting fio output to JSON: {e.msg}")

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.__dict__)

    def __str__(self) -> str:
        return self.to_json()

    def parse_stdout(self, raw_stdout: str) -> None:
        # logging.debug(f"raw_stdout: {raw_stdout}")
        try: 
            json_result = json.loads(raw_stdout)
            # self.raw_stdout = raw_stdout

            self.read_iops = json_result['jobs'][0]['read']['iops']
            self.write_iops = json_result['jobs'][0]['write']['iops']
            
            self.read_throughput = json_result['jobs'][0]['read']['bw']
            self.write_throughput = json_result['jobs'][0]['write']['bw']
            if 'lat' in json_result['jobs'][0]['read']:
                self.read_latency = json_result['jobs'][0]['read']['lat']['mean']
                self.write_latency = json_result['jobs'][0]['write']['lat']['mean']
            else: 
                # logging.debug(f"read: {json_result['jobs'][0]['read']}")
                self.read_latency = json_result['jobs'][0]['read']['lat_ns']['mean'] /1000
                self.write_latency = json_result['jobs'][0]['write']['lat_ns']['mean'] / 1000
            self.duration = json_result['jobs'][0]['elapsed']
            self.timestamp = json_result['time']
            self.summarize()
        except json.JSONDecodeError:
            raise RuntimeError('Failed to Parse FIO Output')

# region comparison methods
    def __lt__(self, other):
        return (self.atp < other.atp)
    
    def __le__(self, other):
        return (self.atp <= other.atp)
    
    def __eq__(self, other):
        return (self.atp == other.atp)
    
    def __ne__(self, other):
        return (self.atp != other.atp)
    
    def __gt__(self, other):
        return (self.atp > other.atp)
    
    def __ge__(self, other):
        return (self.atp >= other.atp)
# endregion comparison methods

class FioOptimizer:
    def __init__(self,
                 runs: dict = None,
                 config: dict = None, 
                 min: int = 1,
                 max: int = 256, 
                 throughputweight: int = 1):

        self.runs: dict = runs if runs else {}
        self.config: dict = config if config else {}
        self.best_run: FioBase = None
        self.optimal_queue_depth: int = None
        self.min: int = min
        self.max: int = max
        self.throughputweight: int = throughputweight
        self.tested_iodepths: list[int] = []
        self.runs_raw: dict = {}
        self.atp: ATP = None

        # store state file (csv maybe), read that state file in on load and just return data 

    def find_optimal_iodepth(self) -> FioBase:
        queue_depths = [2**x for x in range(0,10)]

        is_optimial: bool = False
        current_data: pd.DataFrame = None
        while not is_optimial: 
            # Test minimum io_depth and maximum io_depth
            # logging.info(f"min: {self.min}\t max: {self.max}")
            # self.prepare_and_run_fio(queue_depths=[self.min, self.max])    
            # Check if min and max are 1 away from each other, 
            # if so determine which of the two are better and that is the optimal io depth
            self.prepare_and_run_fio(queue_depths=queue_depths)
            throughput = [self.runs[x].total_throughput for x in self.runs.keys()]
            latency = [self.runs[x].avg_latency for x in self.runs.keys()]
            iodepth = [x for x in self.runs.keys()]
            current_data = pd.DataFrame({'iodepth': iodepth, 
                                         'total_throughput': throughput, 
                                         'avg_latency': latency})
            self.atp = ATP(data=current_data, alpha=self.throughputweight) 
            # what is the maximum io depth where the latency is less than the throughput (x) value (which is ATP)
            optimal_iodepth = max(self.atp.j, 1)
            logging.info(f"Best IO Depth: {optimal_iodepth}")
            # build a new list of queue depths to test
            queue_depths = [x for x in range(optimal_iodepth - 1, optimal_iodepth + 2) if x > 0]
            
            if all(queue_depth in self.tested_iodepths for queue_depth in queue_depths):
                retest_df = self.__validate_optimal_iodepth(optimal_iodepth)
                retest_df['normlized_throughput'] = retest_df['total_throughput'] / retest_df['total_throughput'].max()
                retest_df['normlized_latency'] = retest_df['avg_latency'] / retest_df['avg_latency'].max()
                retest_df_stddev = retest_df.std()
                # logging.debug(f"Retest Dataframe: {retest_df}")
                if retest_df_stddev['normlized_throughput'] > 0.05 or retest_df_stddev['normlized_latency'] > 0.05:
                    logging.warning(f"Standard Deviation of Retest Dataframe is greater than 0.05: {retest_df_stddev}")
                    self.config['runtime'] = self.config['runtime'] + 2
                    logging.info(f"Runtime increased to {self.config['runtime']} seconds")
                    self.__reset()
                    queue_depths = [2**x for x in range(0,10) if 2**x]
                else:
                    is_optimial = True
                    self.optimal_queue_depth = optimal_iodepth
                    self.best_run = self.runs[optimal_iodepth]
                    logging.info(f"Optimal IO Depth: {self.best_run.io_depth}")
                    logging.info(f"IOPS            : {self.best_run.total_iops:.03f} \t(std dev: {retest_df_stddev['total_iops']:.03f})")
                    logging.info(f"Latency         : {self.best_run.avg_latency:.03f} µs \t(std dev: {retest_df_stddev['avg_latency']:.03f})")
                    logging.info(f"Throughput      : {self.best_run.total_throughput:.02f} KiBps \t(std dev: {retest_df_stddev['total_throughput']:.03f})")
                    return self.best_run
            # if (self.max - self.min) <= 1:
            #     sorted_runs = sorted(self.runs.items(), key=lambda item: item[1], reverse=True)[0]
            #     self.best_run = sorted_runs[1]
            #     # self.best_run = self.runs[self.max] if self.runs[self.max] > self.runs[self.min]else self.runs[self.min] 
            #     is_optimial: bool = True
            #     logging.info(f"Optimal IO Depth: {self.best_run.io_depth}")
            #     logging.info(f"IOPS            : {self.best_run.total_iops}")
            #     logging.info(f"Latency         : {self.best_run.avg_latency} µs")
            #     logging.info(f"Throughput      : {self.best_run.total_throughput} KiBps")
            # else:
            #     # take a range of values spaced equally between minimum and maximum and test each one
            #     next_iodepths = range(self.min, self.max, max(abs((self.max - self.min)//self.slices),1))
            #     self.prepare_and_run_fio(queue_depths=next_iodepths)
            #     sorted_runs = sorted(self.runs.items(), key=lambda item: item[1], reverse=True)
            #     self.max = self.max if sorted_runs[0][0] == self.max else self.max - max(1, ((self.max + (sorted_runs[0][0])) // self.slices))
            #     self.min = self.min if sorted_runs[0][0] == self.min else self.min + max(1, ((self.min + (sorted_runs[0][0])) // self.slices))
        return self.best_run

    def prepare_and_run_fio(self, queue_depths: List[int]) -> None:
        logging.debug(f"Preparing to run FIO with IO Depths: {queue_depths}")
        for io_depth in queue_depths:
            if io_depth in self.tested_iodepths or io_depth < 1:
                logging.debug(f"Skipping IO Depth = {io_depth}")
                continue
            logging.info(f"Start Test IO Depth = {io_depth}")
            self.config['iodepth'] = io_depth
            
            param_list: list = self.__prepare_args()
            
            fio_run_process: subprocess.CompletedProcess = self.run_fio(param_list)
            
            fio_run: FioBase = self.__process_run(io_depth=io_depth, stdout=fio_run_process.stdout)
            # store current iteration in the "runs" dictionary
            logging.debug(f"End Test IO Depth: {io_depth}, {fio_run.total_iops} IOPS, {fio_run.avg_latency} µs, {fio_run.total_throughput} KiBps")

    def __process_run(self, io_depth: int, stdout: str) -> FioBase:
        fio_run: FioBase = FioBase()
        fio_run.io_depth = io_depth
        fio_run.blocksize = self.config['bs']
        fio_run.parse_stdout(raw_stdout=stdout)
        self.runs[io_depth] = fio_run
        self.tested_iodepths.append(io_depth)
        self.runs_raw[io_depth] = stdout.decode('utf-8')
        return fio_run

    def to_DataFrame(self) -> pd.DataFrame:
        df = pd.DataFrame([x.__dict__ for x in self.runs.values()])
        df.set_index('io_depth', inplace=True)
        return df
    
    def __prepare_args(self) -> list:
        self.config['output-format'] = 'json'
        param_list: list = [f"--{k}={v}" if v else f"--{k}" for k, v in self.config.items()]
        return param_list

    def run_fio(self, params: list) -> Union[subprocess.CompletedProcess, RuntimeError]:
        logging.debug(f"Running FIO with params: {params}")
        fio_process = subprocess.run(['fio'] + params, capture_output=True)
        logging.debug(f"Fio Return code: {fio_process.returncode}")
        if fio_process.returncode != 0:
            logging.error(f"Error code: {fio_process.returncode}. Error Message: {fio_process.stderr}")
            raise RuntimeError(f"Error code: {fio_process.returncode}. Error Message: {fio_process.stderr}")
        return fio_process

    def __validate_optimal_iodepth(self, optimal_iodepth: int) -> pd.DataFrame:
        logging.info(f"Validating optimal IO Depth: {optimal_iodepth}")
        temp_runs: list = []
        self.config['iodepth'] = optimal_iodepth
        self.config['runtime'] = int(self.config['runtime']) + 2
        param_list: list = self.__prepare_args()
        for i in range(0,5):
            fio_run_process: subprocess.CompletedProcess = self.run_fio(param_list)
            fio_run: FioBase = FioBase()
            fio_run.parse_stdout(fio_run_process.stdout)
            temp_runs.append(fio_run)
        return pd.DataFrame([x.__dict__ for x in temp_runs])
        
    def __reset(self) -> None:
        self.runs = {}
        self.runs_raw = {}
        self.best_run = None
        self.tested_iodepths = []

    def to_csv(self) -> str:
        # call the to_DataFrame function and return a csv
        return self.to_DataFrame().to_csv()

    def to_json(self) -> str:
        # call the to_DataFrame function and return a json
        return self.to_DataFrame().to_json()
    

# create a class that access a configuration ini file and returns a dictionary of the configuration
def parse_fio_config(config_file: str) -> dict:
    if not path.isfile(config_file):
        logging.error(f"File {config_file} not found")
        raise FileNotFoundError(f"File {config_file} not found")
    config_parser = configparser.ConfigParser(allow_no_value=True)
    config_parser.read(config_file)
    if not config_parser.has_section('global'):
        logging.error("Config file does not have a [global] section")
        raise ValueError("Config file does not have a [global] section")
    return config_parser.items('global')

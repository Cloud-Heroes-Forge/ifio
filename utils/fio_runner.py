# from os import popen
import subprocess
import json
from .models import FioBase

class FioRunner:
    def __init__(self):
        return

    @staticmethod
    def prepare_args(params: list) -> list:
        param_list: list = ['--output-format=json']
        for param in params:
            param_list.append(param[0])
            if param[1]:
                param_list.append(param[1])
        return param_list

    @staticmethod
    def run_fio(params: list) -> object:
        param_list: list = FioRunner.prepare_args(params)
# command = "sudo fio --minimal -name=temp-fio --bs="+str(blocksize)+" --ioengine=libaio 
# --iodepth="+str(iodepth)+" --size="+fio_size+" --direct=1 --rw="+str(run)+" --filename=/dev/"+str(device)+" 
# --numjobs="+str(numjobs)+" --time_based --runtime="+fio_runtime+" --group_reporting"
           
        # os_stream = popen('fio {}'.format(param_string))
        fio_process = subprocess.run(['fio'] + param_list, capture_output=True)
        return fio_process

    @staticmethod
    def stdout_to_FioBase(raw_stdout: str) -> FioBase:
        try: 
            json_result = json.loads(raw_stdout)
            fiobase = FioBase()
            fiobase.read_iops = json_result['jobs'][0]['read']['iops']
            fiobase.read_throughput = json_result['jobs'][0]['read']['bw']
            fiobase.read_latency = json_result['jobs'][0]['read']['lat']['mean']
            fiobase.write_iops = json_result['jobs'][0]['write']['iops']
            fiobase.write_throughput = json_result['jobs'][0]['write']['bw']
            fiobase.write_latency = json_result['jobs'][0]['write']['lat']['mean']
            fiobase.duration = json_result['jobs'][0]['elapsed']
            fiobase.timestamp = json_result['time']
            fiobase.summarize()
            return fiobase
        except json.JSONDecodeError:
            raise RuntimeError('Failed to Parse FIO Output')

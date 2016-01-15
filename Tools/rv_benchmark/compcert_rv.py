__author__ = 'manasvi'
from Tools.tool import Tool
import os
import subprocess32 as subprocess
import signal
from tabulate import tabulate


class TimeoutException(Exception):
    pass


class CompcertRV(Tool):
    def signal_handler(self, signum, frame):
        raise TimeoutException("Timed out!")

    def run(self, verbose=False, log_location=None):
        output_dict = {"TP": 0, "FP": 0}
        error_code_dict = {}
        total = 0
        os.chdir(self.benchmark_path)
        for dir in filter(lambda x: os.path.isdir(x), os.listdir(os.getcwd())):
            os.chdir(dir)
            print "In Directory: " + os.getcwd()
            file_list = os.listdir(os.getcwd())
            for c_file in filter(lambda y: y.endswith(".c"), file_list):
                if "link" in c_file:
                    continue

                total += 1
                if "-good" in c_file:
                    error_code = c_file.split("-good")[0]
                    is_bad = False
                else:
                    error_code = c_file.split("-bad")[0]
                    is_bad = True
                if error_code not in error_code_dict:
                    error_code_dict[error_code] = {"TP": " ", "FP": " "}
                signal.signal(signal.SIGALRM, self.signal_handler)
                signal.alarm(5)
                try:
                    command = ["ccomp", "-fstruct-passing", "-interp", "-trace", c_file]
                    # print command
                    output = subprocess.check_output(command, stderr=subprocess.STDOUT)
                    if "warning" in output and c_file in output:
                        print output
                        if is_bad:
                            output_dict["TP"] += 1
                            error_code_dict[error_code]["TP"] = self.name
                        else:
                            output_dict["FP"] += 1
                            error_code_dict[error_code]["FP"] = self.name
                except subprocess.CalledProcessError as error:
                    # Problem with the plugin
                    pass
                except TimeoutException:
                    pass
                finally:
                    signal.alarm(0)
            os.chdir(self.benchmark_path)

        self.numbers_dict = output_dict
        self.errors_dict = error_code_dict
        self.total = total

    def get_numbers(self):
        return {
            "TP": str(float(self.numbers_dict["TP"]) / (self.total / 2) * 100),
            "FP": str(float(self.numbers_dict["FP"]) / (self.total / 2) * 100)
        }

    def get_tool_name(self):
        return self.name

    def get_errors(self):
        return self.errors_dict

    def __init__(self, benchmark_path):
        self.benchmark_path = os.path.expanduser(benchmark_path)
        self.numbers_dict = {}
        self.errors_dict = {}
        self.total = None
        self.name = "CompCert"

    def analyze(self):
        pass

    def cleanup(self):
        Tool.cleanup(self)
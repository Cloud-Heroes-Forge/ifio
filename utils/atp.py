import numpy as np
from typing import Callable, Dict, List, Tuple
from numpy.typing import ArrayLike
from numpy.polynomial.polynomial import Polynomial
import scipy.integrate as spi
import pandas as pd
import logging

def calculate_latency_curve(throughput, latency) -> Polynomial:
    """
    Generates a polynomial curve that fits the latency values for a given throughput range
    """
    if throughput.size > 0: 
        latency_curve: Polynomial = Polynomial.fit(x=throughput, y=latency, deg=2, w=1/throughput)
        logging.info(f"Latency Curve: {latency_curve}")
        return latency_curve
    raise ZeroDivisionError("Throughput is 0")

class ATP():
    """
    Reference: https://dl.acm.org/doi/abs/10.1145/2825236.2825248
        Half-Latency Rule for Finding the Knee of the Latency Curve by Naresh M Patel
        
    """
    def __init__(self, 
                 data: pd.DataFrame,
                 alpha: int = 1) -> None:
        self.data: pd.DataFrame = data
        self.generated_data: pd.DataFrame = pd.DataFrame()
        self.generated_data['throughput']: np.ndarray = np.linspace(start=self.data['total_throughput'].min(), 
                                                                    stop=self.data['total_throughput'].max(), 
                                                                    num=self.data['iodepth'].max())
        self.data: pd.DataFrame = data.set_index('iodepth')
        self.data.sort_index(inplace=True)
        self.data['through_normalized']: np.ArrayLike = self.data['total_throughput'] / self.data['total_throughput'].max()
        self.alpha: int = alpha
        self.latency_curve: Polynomial = calculate_latency_curve(self.data['total_throughput'], self.data['avg_latency'])   # w(x)
        
        self.latency_mathed = self.latency_curve(self.data['total_throughput'])
        self.data['ORT']: np.ArrayLike = np.array([self.__calculate_ort(x=x, curve=self.latency_curve) for x in self.data['total_throughput']])
        # self.data['ORT'] is now the values of the r(x) curve at each value of 'total_throughput'
        # ATP is (latency(x) * alpha) / ORT(x)
        self.data['ATP']: np.ArrayLike = np.array([self.__calculate_atp(x=x, curve=self.latency_curve) for x in self.data['total_throughput']])
        
        # Find the smallest index where ort * 2 - avg_latency is negative
        new_index: pd.DataFrame = pd.DataFrame()
        while new_index.dropna().empty:
            self.generated_data['avg_latency']: np.ndarray = self.latency_curve(self.generated_data['throughput'])
            self.generated_data['ORT']: np.ndarray = np.array([self.__calculate_ort(x=x, curve=self.latency_curve) for x in self.generated_data['throughput']])
            self.generated_data['ATP']: np.ndarray = np.array([self.__calculate_atp(x=x, curve=self.latency_curve) for x in self.generated_data['throughput']])
            new_index: pd.DataFrame = self.generated_data[((2 * self.generated_data['ORT']) - self.generated_data['avg_latency']) < 0].sort_values(by='ATP', ascending=True)
            # handle the case where the two lines do not intersect.
            # This solution redraws the curves with a smaller range of throughput values by dropping the top 10% quantile of latency values
            # another possible solution would be to use np.interp to find the intersection point
            if new_index.dropna().empty:
                logging.warning(f"Could not find a value of j, dropping top 10% of latency data set: {self.generated_data.size} ")
                self.generated_data = self.generated_data[self.generated_data['avg_latency'] < self.generated_data['avg_latency'].quantile(0.90)]
                self.latency_curve = calculate_latency_curve(self.generated_data['throughput'], self.generated_data['avg_latency'])
            else: 
                new_index = new_index.idxmin()

        # return the iodepth (index) of the generated_data that has the lowest ATP
        self.j = self.generated_data.loc[new_index, ['throughput', 'avg_latency']].index[0]
        # logging.info(f"j: {self.j}")
    
    def __calculate_ort(self, x: float, curve: Polynomial) -> float:
        """
        Computes the integral (1 / x) * integral(from 0 to x) of { curve(u) du }
        
        Args:
            x (float): upper limit of integration
            curve (function): a function that returns the value of w(u) for a given u
        
        Returns:
            float: The value of the integral (the area under the latency curve from 0 to x)
        """
        numerator, abserr = spi.quad(curve, 0, x)
        return numerator / x
    
    def __calculate_atp(self, x: float, curve: Polynomial) -> float:
        """
        Computes the Accelerated Throughput Power (ATP) for a given set of data

        Args:
            x (float): upper limit of integration
            curve (function): a function that returns the value of w(u) for a given u
        
        Returns:
            float: The Accelerated Throughput Power (ATP) for x
        """
        atp = ((x**self.alpha) / (self.__calculate_ort(x=x, curve=curve)))
        return atp

    def __str__(self) -> str:
        return str(self.j)
    
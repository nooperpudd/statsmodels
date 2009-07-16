"""
Robust linear models
"""
import numpy as np

from models.regression import WLS
from models.robust import norms, scale

class Model(WLS):

    niter = 20
    scale_est = 'MAD'

    def __init__(self, endog, exog, M=norms.Hampel()):
        self.M = M
        self.weights = 1
        self.initialize()   # is this still needed

    def __iter__(self):
        self.iter = 0
        self.dev = np.inf
        return self

    def deviance(self, results=None):
        """
        Return (unnormalized) log-likelihood from M estimator.

        Note that self.scale is interpreted as a variance in OLSModel, so
        we divide the residuals by its sqrt.
        """
        if results is None:
            results = self.results
        return self.M((results.Y - results.predict) / np.sqrt(results.scale)).sum()

    def next(self):
        results = self.results
        self.weights = self.M.weights((results.Y - results.predict) / np.sqrt(results.scale))
        self.initialize(self.design)
        results = WLS.fit(self, results.Y)
        self.scale = results.scale = self.estimate_scale(results)
        self.iter += 1
        return results

    def cont(self, results, tol=1.0e-5):
        """
        Continue iterating, or has convergence been obtained?
        """
        if self.iter >= Model.niter:
            return False

        curdev = self.deviance(results)
        if np.fabs((self.dev - curdev) / curdev) < tol:
            return False
        self.dev = curdev

        return True

    def estimate_scale(self, results):
        """
        Note that self.scale is interpreted as a variance in OLSModel, so
        we return MAD(resid)**2 by default.
        """
        resid = results.Y - results.predict
        if self.scale_est == 'MAD':
            return scale.MAD(resid)**2
        elif self.scale_est == 'Huber2':
            return scale.huber(resid)**2
        else:
            return scale.scale_est(self, resid)**2

    def fit(self, Y):

        iter(self)
        self.results = WLS.fit(self, Y)
        self.scale = self.results.scale = self.estimate_scale(self.results)

        while self.cont(self.results):
            self.results = self.next()

        return self.results
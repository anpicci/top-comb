import torch
import uproot
import json
import math
import sys
from torch.nn import Linear, MSELoss
from torch.optim import SGD, Adam
from torch.optim.lr_scheduler import ExponentialLR
import pandas as pd
import numpy as np
from collections import OrderedDict
import re
import os
import csv
import glob
import matplotlib.pyplot as plt
from pathlib import Path

if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} <infile.root> <outdir>")
    sys.exit(1)

infile = sys.argv[1]
outdir = sys.argv[2]
os.makedirs(outdir, exist_ok=True)

pois_list = json.loads(Path("extrapoConfigs/full_pois.json").read_text(encoding="utf-8"))
pois = [x for x in pois_list]
pois_to_remove = []  # 'cbwre', 'chtbre','clebqre', 'cleqt1re', 'cleqt3re', 'cqb1', 'cqb8', 'cqtqb1re', 'cqtqb8re', 'ctb1', 'ctb8'

# for p in pois_to_remove:
#     pois.remove(p)

class Matrix(pd.DataFrame):

    def __init__(self, matrix, columns=None, index=None, dtype=None, copy=True, eigenvalues=None):
        if index is None: index = columns
        super(Matrix, self).__init__(data=matrix, columns=columns, index=index, dtype=dtype, copy=copy)
        self.eigenvalues = pd.Series(eigenvalues, index) if eigenvalues is not None else None

    @property
    def _constructor(self):
        if self.eigenvalues is not None:
            new_ypars = [y for y in self.ypars if y in self.eigenvalues.index]
            if len(new_ypars) > 0:
                self.eigenvalues = self.eigenvalues.loc[new_ypars]
            else:
                self.eigenvalues = None
        return Matrix

    _metadata = ['eigenvalues']

    @classmethod
    def fromDict(cls, d):
        if not 'ypars' in d: d['ypars'] = d['xpars']
        if not 'eigenvalues' in d: d['eigenvalues'] = None
        return cls(d['matrix'], d['xpars'], d['ypars'], eigenvalues=d['eigenvalues'])

    @classmethod
    def fromJSON(cls, filename):
        with open(filename, 'r') as f:
            d = json.load(f)
        return cls.fromDict(d)

    @classmethod
    def fromDataFrame(cls, df, eigenvalues=None):
        return cls(df.values, df.columns, df.index, eigenvalues=eigenvalues)

    @classmethod
    def fromTMatrix(cls, tmatrix, columns=None, index=None, eigenvalues=None):
        N, M = tmatrix.GetNrows(), tmatrix.GetNcols()
        arr = np.zeros((N, M))
        for i in range(N):
            for j in range(M):
                arr[i][j] = tmatrix[i][j]
        return cls(arr, columns, index, eigenvalues=eigenvalues)

    @classmethod
    def merge(cls, matrices):
        if len(matrices) == 0:
            return cls(np.zeros((0, 0)))
        else:
            pdcat = pd.concat((m for m in matrices), sort=False).fillna(0.)
            return cls(pdcat.values, pdcat.columns, pdcat.index)

    @property
    def xpars(self): return self.columns.tolist()

    @property
    def ypars(self): return self.index.tolist()

    @property
    def matrix(self): return self.values

    def __mul__(self, other):
        if isinstance(other, pd.DataFrame):
            new_xpars = [x for x in other.index if x in self.columns]
            return Matrix(np.dot(self.loc[:, new_xpars], other.loc[new_xpars, :]), index=self.index, columns=other.columns)
        elif isinstance(other, np.ndarray) and other.shape[0] == self.shape[1]:
            return Matrix(np.dot(self, other), index=self.index, columns=['x%s' % i for i in range(other.shape[1])])
        elif isinstance(other, float) or isinstance(other, int):
            return Matrix(other * self.matrix, columns=self.columns, index=self.index)
        else:
            return super(Matrix, self).__mul__(self, other)

    def __rmul__(self, other):
        if isinstance(other, pd.DataFrame):
            new_ypars = [y for y in self.index if y in other.columns]
            return Matrix(np.dot(other.loc[:, new_ypars], self.loc[new_ypars, :]), index=other.index, columns=self.columns)
        elif isinstance(other, np.ndarray) and other.shape[1] == self.shape[0]:
            return Matrix(np.dot(other, self), columns=self.columns, index=['y%s' % i for i in range(other.shape[0])])
        elif isinstance(other, float) or isinstance(other, int):
            return Matrix(other * self.matrix, columns=self.columns, index=self.index)
        else:
            return super(Matrix, self).__rmul__(self, other)

    def __add__(self, other):
        if isinstance(other, pd.DataFrame):
            new_xpars = MergeLists([self.xpars, other.columns.tolist()], True)
            new_ypars = MergeLists([self.ypars, other.index.tolist()], True)
            return np.add(
                self.reindex(index=new_ypars, columns=new_xpars, fill_value=0.),
                other.reindex(index=new_ypars, columns=new_xpars, fill_value=0.)
            )
        else:
            return super(Matrix, self).__add__(self, other)

    def triangular(self):
        if not self.xpars == self.ypars:
            print('Matrix.triangular(): xpars != ypars')
            return self
        else:
            res = Matrix(np.zeros(self.shape), self.xpars)
            for i in range(self.shape[0]):
                res.iloc[i, i] = self.iloc[i, i]
                for j in range(i):
                    res.iloc[i, j] = self.iloc[i, j] + self.iloc[j, i]
            return res

    def symmetric(self):
        if not self.xpars == self.ypars:
            print('Matrix.symmetric(): xpars != ypars')
            return self
        else:
            res = Matrix(np.zeros(self.shape), self.xpars)
            for i in range(self.shape[0]):
                res.iloc[i, i] = self.iloc[i, i]
                for j in range(i):
                    res.iloc[i, j] = (self.iloc[i, j] + self.iloc[j, i]) / 2.
                    res.iloc[j, i] = (self.iloc[i, j] + self.iloc[j, i]) / 2.
            return res

    def writeToJSON(self, filename):
        res = OrderedDict()
        res['xpars'] = self.xpars
        if self.ypars != self.xpars: res['ypars'] = self.ypars
        if self.eigenvalues is not None: res['eigenvalues'] = self.eigenvalues.tolist()
        res['matrix'] = self.matrix.tolist()

        with open(filename, 'w') as f:
            json.dump(res, f, indent=2)

    def get_ev(self, ypars=None):
        if self.eigenvalues is None: return None
        if ypars is None: ypars = self.ypars
        return self.eigenvalues.loc[ypars]

    def remove_XorY(self, x=[], y=[]):
        keep_x = [p for p in self.xpars if not p in x]
        keep_y = [p for p in self.ypars if not p in y]
        return self.loc[keep_y, keep_x]


class QuadraticModel(torch.nn.Module):
    def __init__(self, ncoefs):
        super(QuadraticModel, self).__init__()
        self.fc1 = Linear(ncoefs, 1, bias=False)
        self.fc2 = Linear(int((ncoefs * ncoefs - ncoefs) / 2 + ncoefs), 1, bias=False)

    def forward(self, x):
        x1 = x.unsqueeze(2)
        x2 = x.unsqueeze(1)
        xx = x1 * x2
        indices = torch.triu_indices(*(xx.shape[1:]))
        xx_upper = xx[:, indices[0], indices[1]]
        return self.fc2(xx_upper)  # self.fc1(x) +


all_data = torch.Tensor(
    uproot.concatenate([f"{infile}:limit"],
                       ["2*deltaNLL", "quantileExpected"] + [x for x in pois],
                       library='pd').values
)

target = all_data[:, 0]
mask = (all_data[:, 1] > -0.5)
x = all_data[:, 2:]

x = x[mask]
target = target[mask]

model = QuadraticModel(len(pois))

mseloss = MSELoss()
optimizer = Adam(model.parameters(), lr=0.2)
scheduler = ExponentialLR(optimizer, gamma=0.9999)

nepochs = 10000

indices = {}
count = 0
for i1, op1 in enumerate(pois):
    for i2, op2 in enumerate(pois):
        if i2 < i1: continue
        indices[(op1, op2)] = count
        count = count + 1


def hessian_from_model(model):
    linears = model.fc1.weight
    quadratics = model.fc2.weight

    hessian_matrix_numpy = []

    for i1, op1 in enumerate(pois):
        hessian_matrix_row = []
        for i2, op2 in enumerate(pois):
            index = indices[(op1, op2)] if (op1, op2) in indices else indices[(op2, op1)]
            factor = 1
            if op1 != op2:
                factor = 2
            hessian_matrix_row.append(float(quadratics[0, index]) / factor)
        hessian_matrix_numpy.append(hessian_matrix_row)

    hessian_matrix_numpy = np.array(hessian_matrix_numpy)
    dfHes = pd.DataFrame(hessian_matrix_numpy, index=pois, columns=pois)
    return Matrix.fromDataFrame(dfHes)


import torch.nn as nn


class RelativeMSELoss(nn.Module):
    def __init__(self, epsilon=1e-8):
        super(RelativeMSELoss, self).__init__()
        self.epsilon = epsilon

    def forward(self, y_pred, y_true):
        numerator = torch.sum((y_pred - y_true) ** 2)
        denominator = torch.sum(y_true ** 2) + self.epsilon
        return numerator / denominator


rel_mse = RelativeMSELoss()

for epoch in range(nepochs):
    optimizer.zero_grad()
    loss = rel_mse(model(x).flatten(), target.flatten())
    epoch_loss = loss.data
    loss.backward()
    optimizer.step()
    scheduler.step()

    if not (epoch % 1000):
        print(f'Epoch: {epoch}. Loss: {epoch_loss}')

    if not (epoch % 5000):
        hessian = hessian_from_model(model)
        values, vectors = np.linalg.eig(hessian)
        min_eig = vectors[:, np.argmin(values)]
        print("Minimum eigenvector", np.min(values), min_eig)
        print("All eigenvalues", values)

        # --- minimal-change plotting fix + no hard-coded 26 + no forced ctG ---
        plot_poi = "ctG" if "ctG" in pois else pois[0]
        index_plot = pois.index(plot_poi)

        N = 1000
        grid = torch.zeros((N, len(pois)))
        grid[:, index_plot] = torch.linspace(-1, 1, steps=N)

        with torch.no_grad():
            y = model(grid).flatten().detach().cpu().numpy()
            x_plot = grid[:, index_plot].detach().cpu().numpy()

        plt.plot(x_plot, y)
        plt.savefig(os.path.join(outdir, "plot.png"))
        plt.clf()

        # csv_file=f'{outdir}/scan.ESU.Linear.fixed.Lumi{lumi}.{wps}.more_data_at_epoch_{epoch}.csv'
        # with open(csv_file, 'w', newline='') as csvfile:
        #     scanwriter = csv.writer(csvfile, delimiter=',')
        #     scanwriter.writerow(pois)
        #     for i,factor in enumerate([0.1, 0.01, -0.1, -0.01]):
        #         scanwriter.writerow( [factor*min_eig[i] for i in range(len(pois))])
        # command = f'./fits_for_pca_extra.sh {wps} {path} {lumi}  more_data_at_epoch_{epoch} {outdir}'
        # os.system(command)
        # outfiles = glob.glob(f"{outdir}/higgsCombine.ESU.Linear.fixed.Lumi{lumi}.{wps}.extra.more_data_at_epoch_0.POINT.*.MultiDimFit.mH120.root")
        # more_data=torch.Tensor( uproot.concatenate( outfiles, [ "2*deltaNLL", "quantileExpected"]+[p for p in pois], library='pd').values)
            
        # more_target = more_data[:,0]
        # more_mask   = (more_data[:,1] > -0.5)
        # more_x      = more_data[:,2:]

        # more_x      = more_x[more_mask]
        # more_target = more_target[more_mask]

        # x = torch.cat([x,more_x],dim=0)
        # target = torch.cat([target, more_target], dim=0)
        # print(f"Now our data is shape {x.shape}, {target.shape}")

dfHes = hessian_from_model(model)

outprefix = infile.replace(".MultiDimFit.mH120.root", "").split("/")[-1]
dfHes.writeToJSON(f'{outdir}/{outprefix}_hessian.json')


def do_pca(info_matrix, min_info=0., pois=None):
    remove_poi = [p for p in info_matrix.xpars if abs(info_matrix.loc[p, p]) < min_info]
    if pois is not None:
        remove_poi += [p for p in info_matrix.xpars if not (p in pois or p in remove_poi)]
    info_matrix = info_matrix.remove_XorY(x=remove_poi, y=remove_poi)

    eigenvectors, eigenvalues, vh = np.linalg.svd(info_matrix)

    assert (np.allclose(np.dot(eigenvectors, eigenvectors.T), np.identity(eigenvectors.shape[0])))

    xpars = info_matrix.xpars
    ypars = ['EV%s' % (i + 1) for i in range(len(eigenvalues))]
    return Matrix(eigenvectors.T, xpars, ypars, eigenvalues=eigenvalues)


basis_rotation = do_pca(dfHes)
basis_rotation.writeToJSON(f'{outdir}/{outprefix}_basis_rotation.json')
import numpy as np
import pandas as pd
import yaml
import json
from itertools import chain
from math import sqrt
from ROOT import TMatrixDSym, gROOT, TH2D
from collections import OrderedDict

class Measurement(object):

    def __init__(self, nbins, bin_labels, sm, sm_unc, bf, bf_unc, cov, cov_th=None, cov_hessian=None):
        self.nbins = int(nbins)
        self.bin_labels = list(bin_labels)
        self.sm = np.array(sm)
        self.sm_unc = np.array(sm_unc)
        self.bf = np.array(bf)
        self.bf_unc = np.array(bf_unc)
        self.cov = np.array(cov)
        self.cov_th = np.array(cov_th)
        self.cov_hessian = np.array(cov_hessian)

    @classmethod
    def fromJSON(cls, filename):
        with open(filename) as jsonfile:
            input = json.load(jsonfile)
        return cls.fromDict(input)

    @classmethod
    def fromYAML(cls, filename):
        with open(filename) as yamlfile:
            input = yaml.load(yamlfile)
        return cls.fromDict(input)

    @classmethod
    def fromDict(cls, d):
        nbins = d['nbins'] if 'nbins' in d else len(d['bin_labels'])
        sm_unc = np.array(d['sm_unc']) if 'sm_unc' in d else np.zeros(nbins)
        bf_unc = np.array(d['bf_unc']) if 'bf_unc' in d else np.array([np.sqrt(d['cov'][i][i]) for i in range(nbins)])
        cov_th = np.array(d['cov_th']) if 'cov_th' in d else None
        cov_hessian = np.array(d['cov_hessian']) if 'cov_hessian' in d else None
        return cls(nbins=nbins, bin_labels=d['bin_labels'], sm=np.array(d['sm']), sm_unc=sm_unc, bf=np.array(d['bf']), bf_unc=bf_unc, cov=np.array(d['cov']), cov_th=cov_th, cov_hessian=cov_hessian)

    def writeToJSON(self, filename):
        with open(filename, 'w') as outfile:
            if self.cov_th is not None and self.cov_hessian is not None:
                res = OrderedDict([
                    ('nbins', int(self.nbins)),
                    ('bf', self.bf.tolist()),
                    ('bf_unc', self.bf_unc.tolist()),
                    ('cov', self.cov.tolist()),
                    ('cov_th', self.cov_th.tolist()),
                    ('cov_hessian', self.cov_hessian.tolist()),
                    ('sm', self.sm.tolist()),
                    ('sm_unc', self.sm_unc.tolist()),
                    ('bin_labels', self.bin_labels)
                ])
            elif self.cov_th is not None:
                res = OrderedDict([
                    ('nbins', int(self.nbins)),
                    ('bf', self.bf.tolist()),
                    ('bf_unc', self.bf_unc.tolist()),
                    ('cov', self.cov.tolist()),
                    ('cov_th', self.cov_th.tolist()),
                    ('sm', self.sm.tolist()),
                    ('sm_unc', self.sm_unc.tolist()),
                    ('bin_labels', self.bin_labels)
                ])
            elif self.cov_hessian is not None:
                res = OrderedDict([
                    ('nbins', int(self.nbins)),
                    ('bf', self.bf.tolist()),
                    ('bf_unc', self.bf_unc.tolist()),
                    ('cov', self.cov.tolist()),
                    ('cov_hessian', self.cov_hessian.tolist()),
                    ('sm', self.sm.tolist()),
                    ('sm_unc', self.sm_unc.tolist()),
                    ('bin_labels', self.bin_labels)
                ])
            else :
                res = OrderedDict([
                    ('nbins', int(self.nbins)),
                    ('bf', self.bf.tolist()),
                    ('bf_unc', self.bf_unc.tolist()),
                    ('cov', self.cov.tolist()),
                    ('sm', self.sm.tolist()),
                    ('sm_unc', self.sm_unc.tolist()),
                    ('bin_labels', self.bin_labels)
                ])
            outfile.write(json.dumps(res, sort_keys=False, indent=2))

    def writeToYAML(self, filename):
        with open(filename, 'w') as outfile:
            if self.cov_th is not None and self.cov_hessian is not None:
                res = OrderedDict([
                    ('nbins', int(self.nbins)),
                    ('bf', self.bf.tolist()),
                    ('bf_unc', self.bf_unc.tolist()),
                    ('cov', self.cov.tolist()),
                    ('cov_th', self.cov_th.tolist()),
                    ('cov_hessian', self.cov_hessian.tolist()),
                    ('sm', self.sm.tolist()),
                    ('sm_unc', self.sm_unc.tolist()),
                    ('bin_labels', self.bin_labels)
                ])
            elif self.cov_th is not None:
                res = OrderedDict([
                    ('nbins', int(self.nbins)),
                    ('bf', self.bf.tolist()),
                    ('bf_unc', self.bf_unc.tolist()),
                    ('cov', self.cov.tolist()),
                    ('cov_th', self.cov_th.tolist()),
                    ('sm', self.sm.tolist()),
                    ('sm_unc', self.sm_unc.tolist()),
                    ('bin_labels', self.bin_labels)
                ])
            elif self.cov_hessian is not None:
                res = OrderedDict([
                    ('nbins', int(self.nbins)),
                    ('bf', self.bf.tolist()),
                    ('bf_unc', self.bf_unc.tolist()),
                    ('cov', self.cov.tolist()),
                    ('cov_hessian', self.cov_hessian.tolist()),
                    ('sm', self.sm.tolist()),
                    ('sm_unc', self.sm_unc.tolist()),
                    ('bin_labels', self.bin_labels)
                ])
            else :
                res = OrderedDict([
                    ('nbins', int(self.nbins)),
                    ('bf', self.bf.tolist()),
                    ('bf_unc', self.bf_unc.tolist()),
                    ('cov', self.cov.tolist()),
                    ('sm', self.sm.tolist()),
                    ('sm_unc', self.sm_unc.tolist()),
                    ('bin_labels', self.bin_labels)
                ])
            yaml.dump(res,outfile,default_flow_style=False, allow_unicode=True)

def ReadMeasurement(measurement_file):
    if measurement_file.split('.')[-1]=='yaml':
        measurement = Measurement.fromYAML(measurement_file)
    elif measurement_file.split('.')[-1]=='json':
        measurement = Measurement.fromJSON(measurement_file)
    else: 
        print('File format not supported: {}'.format(measurement_file))
    return measurement

# Matrix: a pandas dataframe with some additions
#  - matrix multiplications with '*' operator
#  - save and load from JSON files
#  - new attribute 'eigenvalues'
class Matrix(pd.DataFrame):

    def __init__(self, matrix, columns=None, index=None, dtype=None, copy=True, eigenvalues=None):
        if index is None: index=columns
        # create a pd.DataFrame and add eigenvalues
        super(Matrix, self).__init__(data=matrix, columns=columns, index=index, dtype=dtype, copy=copy)
        self.eigenvalues = pd.Series(eigenvalues, index) if eigenvalues is not None else None

    # _constructor: the result of an operation on a Matrix should also be a Matrix
    @property
    def _constructor(self):
        # apply row slicing also to eigenvalues
        if self.eigenvalues is not None:
            new_ypars = [y for y in self.ypars if y in self.eigenvalues.index]
            if len(new_ypars) > 0:
                self.eigenvalues = self.eigenvalues.loc[new_ypars]
            else:
                self.eigenvalues = None
        return Matrix

    # _metadata: keep the eigenvalues when creating a new object
    _metadata = ['eigenvalues']
    
    @classmethod
    def fromDict(cls, d):
        if not 'ypars' in d: d['ypars'] = d['xpars']
        if not 'eigenvalues' in d: d['eigenvalues'] = None
        return cls(d['matrix'], d['xpars'], d['ypars'], eigenvalues=d['eigenvalues'])

    @classmethod
    def fromJSON(cls, filename):
        with open(filename,'r') as f:
            d = json.load(f)
        return cls.fromDict(d)

    @classmethod
    def fromDataFrame(cls, df, eigenvalues=None):
        return cls(df.values, df.columns, df.index, eigenvalues=eigenvalues)

    @classmethod
    def fromTMatrix(cls, tmatrix, columns=None, index=None, eigenvalues=None):
        N, M = tmatrix.GetNrows(), tmatrix.GetNcols()
        arr = np.zeros((N,M))
        for i in range(N):
            for j in range(M):
                arr[i][j] = tmatrix[i][j]

        return cls(arr, columns, index, eigenvalues=eigenvalues)

    @classmethod
    def merge(cls, matrices):
        if len(matrices) == 0: 
            return cls(np.zeros((0,0)))
        else:
            pdcat = pd.concat((m for m in matrices), sort=False).fillna(0.)
            return cls(pdcat.values, pdcat.columns, pdcat.index)

    @property
    def xpars(self): return self.columns.tolist()

    @property
    def ypars(self): return self.index.tolist()

    @property
    def matrix(self): return self.values

    # matrix multiplication with '*' operator
    # A * B = A[:,B.x] * B[A.y,:]
    def __mul__(self, other):
        if isinstance(other, pd.DataFrame):
            new_xpars = [x for x in other.index if x in self.columns]
            return Matrix(np.dot(self.loc[:,new_xpars], other.loc[new_xpars,:]), index=self.index, columns=other.columns)
        elif isinstance(other, np.ndarray) and other.shape[0] == self.shape[1]:
            return Matrix(np.dot(self, other), index=self.index, columns=['x%s' % i for i in range(other.shape[1])])
        elif isinstance(other, float) or isinstance(other, int):
            return Matrix(other*self.matrix, columns=self.columns, index=self.index)
        else:
            return super(Matrix, self).__mul__(self, other)
    
    # right multiplication
    def __rmul__(self, other):
        if isinstance(other, pd.DataFrame):
            new_ypars = [y for y in self.index if y in other.columns]
            return Matrix(np.dot(other.loc[:,new_ypars], self.loc[new_ypars,:]), index=other.index, columns=self.columns)
        elif isinstance(other, np.ndarray) and other.shape[1] == self.shape[0]:
            return Matrix(np.dot(other, self), columns=self.columns, index=['y%s' % i for i in range(other.shape[0])])
        elif isinstance(other, float) or isinstance(other, int):
            return Matrix(other*self.matrix, columns=self.columns, index=self.index)
        else:
            return super(Matrix, self).__rmul__(self, other)

    # addition
    def __add__(self, other):
        if isinstance(other, pd.DataFrame):
            new_xpars = MergeLists([self.xpars, other.columns.tolist()], True)
            new_ypars = MergeLists([self.ypars, other.index.tolist()], True)
            return np.add(self.reindex(index=new_ypars,columns=new_xpars,fill_value=0.),
                other.reindex(index=new_ypars,columns=new_xpars,fill_value=0.))
        else:
            return super(Matrix, self).__add__(self, other)

    def triangular(self):
        if not self.xpars == self.ypars:
            print('Matrix.triangular(): xpars != ypars')
            return self
        else:
            res = Matrix(np.zeros(self.shape), self.xpars)
            for i in range(self.shape[0]):
                res.iloc[i,i] = self.iloc[i,i]
                for j in range(i):
                    res.iloc[i,j] = self.iloc[i,j]+self.iloc[j,i]
            return res

    def symmetric(self):
        if not self.xpars == self.ypars:
            print('Matrix.symmetric(): xpars != ypars')
            return self
        else:
            res = Matrix(np.zeros(self.shape), self.xpars)
            for i in range(self.shape[0]):
                res.iloc[i,i] = self.iloc[i,i]
                for j in range(i):
                    res.iloc[i,j] = (self.iloc[i,j]+self.iloc[j,i])/2.
                    res.iloc[j,i] = (self.iloc[i,j]+self.iloc[j,i])/2.
            return res

    
    def writeToJSON(self, filename):
        res = OrderedDict()
        res['xpars'] = self.xpars
        if self.ypars != self.xpars: res['ypars'] = self.ypars
        if self.eigenvalues is not None: res['eigenvalues'] = self.eigenvalues.tolist()
        res['matrix'] = self.matrix.tolist()
        
        with open(filename,'w') as f:
            json.dump(res, f, indent=2)

    def get_ev(self, ypars=None):
        if self.eigenvalues is None: return None
        if ypars is None: ypars=self.ypars
        return self.eigenvalues.loc[ypars]

    def remove_XorY(self, x=[], y=[]):
        keep_x = [p for p in self.xpars if not p in x]
        keep_y = [p for p in self.ypars if not p in y]
        return self.loc[keep_y,keep_x]


def ReadIndependent(entry, col=0):
    # Extract the bin labels / bin ranges from the hepData YAML
    values = entry['independent_variables'][col]['values']
    if 'value' in values[0]:
        return [X['value'] for X in values]
    else:
        return [(X['low'], X['high']) for X in values]


def ReadDependent(entry, col=0, error=list(), sym_errors=True):
    # Extract the central values or the uncertainties from a column in the
    # hepData YAML. To extract the errors, supply a list of error indicies
    # that should be summed in quadrature. Errors are then symmeterised by
    # default.
    vals = entry['dependent_variables'][col]['values']
    if len(error) > 0:
        res = list()
        for v in vals:
            sum_hi_sq = 0.
            sum_lo_sq = 0.
            for ecol in error:
                err = v['errors'][ecol]
                if 'symerror' in err:
                    sum_hi_sq += pow(float(err['symerror']), 2)
                    sum_lo_sq += pow(float(err['symerror']), 2)
                elif 'asymerror' in err:
                    sum_hi_sq += pow(float(err['asymerror']['plus']), 2)
                    sum_lo_sq += pow(float(err['asymerror']['minus']), 2)
            sum_hi = sqrt(sum_hi_sq)
            sum_lo = sqrt(sum_lo_sq)
            if sym_errors:
                res.append((sum_lo + sum_hi) / 2.)
            else:
                res.append((-1. * sum_lo, +1. * sum_hi))
        return np.array(res)
    else:
        return np.array([float(X['value']) for X in entry['dependent_variables'][col]['values']])


def MergeLists(lists, skip_repeated_elements=False):
    if skip_repeated_elements:
        res = list()
        for element in chain(*lists):
            if not element in res: res.append(element)
        return res
    else:
        return list(chain(*lists))


def SplitFile(in_file,split_a,split_b):
    res = list()
    i = 0
    while i < len(in_file):
        if split_a in in_file[i]:
            res.append([in_file[i]])
            while not split_b in in_file[i]:
                i+=1
                res[-1].append(in_file[i])
        i+=1
    return res


def CleanString(in_line):
    # remove spaces, tabs, newlines at beginning and end of string
    # and remove repeated spaces between words
    res = in_line.strip().replace('\t',' ')
    while '  ' in res:
        res = res.replace('  ',' ')
    return res


def ReadYodaFile(in_file,title=None,col=None):
    # read data from a 'Rivet validation plot' yoda file
    res = dict()
    for subfile in SplitFile(in_file,'# BEGIN','# END'):
        lines = [CleanString(line) for line in subfile]

        table_title = ''
        table_header, table_raw = list(), list()

        for line in lines:
            if '# END' in line: break
            if line.split('=')[0] == 'Title':
                table_title = line.split('=')[1]
                if table_title != title and title is not None:
                    break
            elif line.startswith('#') and not '# BEGIN' in line:
                table_header = line.split(' ')[1:]
            elif line[0].isdigit() or (line[0]=='-' and line[1].isdigit()):
                table_raw.append([float(nr) for nr in line.split(' ')])

        if len(table_raw) == 0: continue
        
        table = dict()
        while len(table_header) < len(table_raw[0]):
            table_header.append('col%s' % len(table_header))
        for i,h in enumerate(table_header):
            table[h] = [line[i] for line in table_raw]
        
        res[table_title] = table
    
    if col is not None:
        res = dict((k,v[col]) for k,v in res.items() if v.has_key(col))    
    if title is not None:
        res = res[title]
    return res


def CovTMatrix(cov):
    if isinstance(cov, pd.DataFrame): 
        cov = cov.values
    shape = np.shape(cov)
    assert(shape[0] == shape[1])
    N = shape[0]
    res = TMatrixDSym(N)
    for i in range(N):
        for j in range(N):
            res[i][j] = cov[i][j]
    return res

def MergeCov(covs=list()):
    # Input: list of TMatrixD
    # Output: block-diagonal TMatrixD from combination of inputs
    Ntot = sum([X.GetNcols() for X in covs])
    cov = TMatrixDSym(Ntot)
    pos = 0
    for c in covs:
        cov.SetSub(pos, pos, c)
        pos += c.GetNcols()
    # cov.Print()
    return cov

def ParameterUncerts(matrix):
    N = matrix.GetNcols()
    res = []
    for i in range(N):
        res.append(sqrt(matrix[i][i]))
    return res


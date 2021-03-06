# TODO 1. Test Top-k function   2. result decode with p   3. Test With dataset.
# TODO PO: Potential Optimization   NC: Not clear   m:nonzeroes(numedges)   Convention:'All assesments talk about a sole statement'
# TODO All the todo, may refer to similar ones, PLEASE / to FIND ALL OCCURRANCE
# TODO Remove getrow and getcol
# TODO Reevanluating P's time complexity
# TODO Kinda strange because Aij seems reverseing( Like Aji) in the origin paper
# TODO suffix array for x that b[0:i] are all ones

import math
import gzip
import time
import pickle
import itertools
import heapq
import numpy
from scipy import sparse


# A: csc
# count_row & count_col can be changed
def P(A_csc, count_row, count_col):
    visited = set()
    p = []
    n = A_csc.shape[0]
    # O(m) PO csr_matrix can reduce
    count = [0] * n
    for i in xrange(n):
        count[i] = (count_col[i], -count_row[i], i)
    heapq.heapify(count)
    while count:
    # O(n+m) REMOVE A ROW, one node could be removed more than once
        v = heapq.heappop(count)[2]
    # O(1)
        if v not in visited:
    # O(n)
            visited.add(v)
    # O(1)
            p.append(v)
            # count_row[v] = 0
            for ui in xrange(A_csc.indptr[v], A_csc.indptr[v+1]):
                u = A_csc.indices[ui]
                count_row[u] -= 1
                heapq.heappush(count, (count_col[u], -count_row[u], u))
    # O(n)
    pt = [0] * n
    # O(n)
    for i, pi in enumerate(p):
        pt[pi] = i
    return p, pt


"""
A : adjacent matrix
doesn't sacrifice time complexity,
because replace list with binomial tree
(however,array could be even better, not so handy in python)

d : seeds set
"""


def lower_bound(A_csc, d, c):
    # O(n)
    #lb = dict(itertools.izip(d.row, d.data * c))
    lb = numpy.zeros(A.shape[0])
    for i, j in itertools.izip(d.row, d.data):
        lb[i] = j * c
    # O(n)
    old_layer = set(d.row)
    visited = set(old_layer)
    # Introduce old_layer and new_layer to enable
    # transition from one WHOLE layer to another
    while old_layer:
        new_layer = set()
    # O(n)
        for u in old_layer:
    # O(m)
            for vi in xrange(A_csc.indptr[u], A_csc.indptr[u+1]):
                v = A_csc.indices[vi]
                w = A_csc.data[vi]
                if v not in visited:
    # O(n)
                    lb[v] += (1-c) * w * lb[u]
                    new_layer.add(v)
        for u in new_layer:
    # O(n)
            visited.add(u)
    # O(n)
        old_layer = new_layer
    return lb

# Shared by exact and upper_bound
exact_id1 = None
ub_id1 = None


def AD(A, pt):
    # TODO A.row , no need to tolist()
    # O(n)
    id = map(lambda i: pt[i], A.row)
    jd = map(lambda j: pt[j], A.col)
    # O(1)
    xd = A.data
    return sparse.coo_matrix((xd, (id, jd)), shape=A.shape)


def W(Ad, c):
    # O(m+n)
    return sparse.eye(Ad.shape[0]) - (1-c)*Ad


def QR(w, pt, d):
    # TODO why?????????
    w = w.tocoo()
    # print sparse.coo_matrix((d.data, (map(lambda x: pt[x], d.row), [0]*d.nnz))).todense()
    import spqr_wrapper
    # NC ASSUME it's optical
    # PO if we pass w as csc_matrix , we could avoid 2 transforms
    # g: O(|Q|)
    Z_data, Z_row, Z_col,\
    R_data, R_indptr, R_indices =\
    spqr_wrapper.qr(w.data.tolist(),
                    w.row.tolist(),
                    w.col.tolist(),
                    w.shape[0], w.shape[1],
                    d.data.tolist(), d.row.tolist())
    # TODO May not support directed-graph
    g = numpy.zeros(w.shape[0])
    for d, r in itertools.izip(Z_data, Z_row):
        g[r] = d
    R = sparse.csc_matrix((numpy.array(R_data),
                           numpy.array(R_indices),
                           numpy.array(R_indptr)), shape=w.shape)
    return g, R


# R_rev: csr_matrix
def exact(Rt, c, g, u):
    # Shared by exact and upper_bound
    global exact_id1
    exact_i = 0
    '''
    for i in xrange(R_rev.indptr[u], R_rev.indptr[u+1]):
        exact_i += c * R_rev.data[u] * g[R_rev.indices[u]]
    '''
    '''
    Rri = step_inverse(Rt, u)
    for i, d in enumerate(Rri):
        exact_i += c * d * g[i]
    '''
    exact_i = c * step_inverse(Rt, u, g)
    exact_id1 = exact_i
    return exact_i


def upper_bound(u, lbu, sum_lb, n):
    # Shared by exact and upper_bound
    global exact_id1, ub_id1
    ubi = 0
    if ub_id1 == None:
        ubi = 1 - sum_lb + lbu
    else:
        # Upper bound _ (i-1)
        ubi = lbu - exact_id1 + ub_id1
    ub_id1 = ubi
    return ubi

'''
def RevR(R):
    rev = dict()
    for c in xrange(1, R.shape[1]):
        for yi in xrange(R.indptr[c], R.indptr[c+1]):
            y = R.indices[yi]
            for xi in xrange(R.indptr[c]-1, R.indptr[c-1], -1):
                x = R.indices[xi]
                if x <= y:
                    break
                rev.setdefault(y, dict())[xi]
'''


# TODO there must be a standard function
def belong(i, l, r):
    return i < r and i >= l
# Only adapt to upper-triangle sparse matrix R, csc
# Rt: transpose of R, lower-triangle, csr
# row: num of the requested row of the inverse of A


def step_inverse(Rt, row):
    m = Rt.shape[0]
    rr = numpy.zeros(m)
    # TODO Rt.indptr[1:] is to slow
    r_i = iter(Rt.indptr)
    peekr_i = iter(Rt.indptr)
    peekr_i.next()

    for i in xrange(Rt.shape[0]):
        # Assume that the main diagnal are all one
        s = 0.0
        r = r_i.next()
        peekr = peekr_i.next()
        for x in xrange(r, peekr-1):
            s += rr[Rt.indices[x]] * Rt.data[x]
        if row == i:
            rr[i] = (1 - s)/Rt.data[peekr-1]
        else:
            rr[i] = (0 - s)/Rt.data[peekr-1]
    return rr


# R: csc_matrix
def F(R, g, c, p):
    R_csr = R.tocsr()
    f = numpy.zeros(R_csr.shape[0])
    r_i = iter(R_csr.indptr[::-1])
    r = r_i.next()
    i = R_csr.shape[0] - 1
    for peekr in r_i:
        s = 0
        for x in xrange(r-1, peekr, -1):
            s += f[p[R_csr.indices[x]]]/c * R_csr.data[x]
        f[p[i]] = c * (g[i] - s)/R_csr.data[peekr]
        r = peekr
        i -= 1
    return f


def top_k(lb, g, R, n, K, theta, c, p):
    # O(n)
    sum_lb = sum(lb)
    heaplb = [(-b, a) for a, b in enumerate(lb)]
    # O(n)
    heapq.heapify(heaplb)
    # K dummy nodes, After all, only keeps K of all
    # O(K)
    relevance = [(0, k) for k in xrange(K)]
    heapq.heapify(relevance)
    # TODO it's too slow!!!!!!!!!!!!!
    #R_rev = RevR(R)
    #R_transpose = R.transpose()

    f = F(R, g, c, p)

    result = []
    for i, fi in enumerate(f):
        result.append((fi, i))
    print sorted(result, reverse=True)[0:6]
    exit(0)

    ok_sum = 0
    t_sum = 0
    for i in xrange(n):
        # O(n)
        lbu, u = heapq.heappop(heaplb)
        lbu = -lbu
        # O(n)
        ubu = upper_bound(u, lbu, sum_lb, n)
        if ubu < theta:
            return list(relevance)
        else:
            ok_sum += 1
            # O(|Q|+|F|)
            # TODO When calc exactness, F=cPtR-1 not F=cR-1
            t1 = time.time()
            relevance_u = exact(R_transpose, c, g, u)
            t2 = time.time()
            if relevance_u == 0:
                t_sum += t2-t1
            #print u, lbu, ubu, relevance_u
            #print 'u=%d, li=%lf, ui=%lf, ei=%lf\n' % (u, lbu, ubu, relevance_u)
            if relevance_u > theta:
                # Replace v with u, whose relevance is greater
                # O(nlgn)
                heapq.heappop(relevance)
                heapq.heappush(relevance, (relevance_u, u))
                # O(n)
                # Refresh theta
                theta = relevance[0][0]
    print t_sum
    return sorted(relevance, reverse=True)


# A: coo_matrix
def count_row_col(a):
    row = a.row
    col = a.col
    count_row = numpy.zeros(a.shape[0])
    count_col = numpy.zeros(a.shape[1])
    for i in row:
        count_row[i] += 1
    for j in col:
        count_col[j] += 1
    return count_row, count_col


# A: coo_matrix
# d: coo_matrix
def pagerank(A, c, d):
    # !!!!WITH row & col reversed
    A_csc = A.tocsc()
    count_row, count_col = count_row_col(A)
    p, pt = P(A_csc, count_row, count_col)
    d.row = numpy.array(map(lambda x: pt[x], d.row))
    Ad = AD(A, pt)
    w = W(Ad, c)
    g, R = QR(w, pt, d)
    Ad_csc = Ad.tocsc()
    lb = lower_bound(Ad_csc, d, c)
    res = top_k(lb, g, R, Ad.shape[0], 3, 0.0, 0.2, p)
    return res


class Loader:
    ACTOR = 0
    REPO = 1

    def __init__(self, weighting='norm', arg=()):
        self.hash = {}
        self.re_hash = {}
        self._hash_count = 0
        self._weighting = weighting
        self._arg_ = arg

    def hash_put(self, u, hash_type):
        if u not in self.hash:
            if hash_type == Loader.ACTOR:
                self.hash[u] = self._hash_count
                self.re_hash[self._hash_count] = u
                self._hash_count += 1
            elif hash_type == Loader.REPO:
                self.hash[u] = self._hash_count
                self.re_hash[self._hash_count] = u
                self._hash_count += 1
        return self.hash[u]

    def load_train(self, days):
        db_dir = 'experiments'
        coefficient = 0
        row = []
        col = []
        data = []
        # Initialize weighting method
        if self._weighting == 'time':
            theta = self._arg_
            #mu = time.time()
            # TODO the data sets are too far from now, so it's not accurate
            mu = time.mktime(time.strptime('2012-01-08T23:59:19Z','%Y-%m-%dT%H:%M:%SZ'))
            coefficient = 1.0 / (theta * math.sqrt(math.pi * 2.0))

        for day in days:
            data_file = '{}/watch_day{}.pkl.gz'.format(db_dir, day)
            events = pickle.load(gzip.open(data_file, 'r'))
            for e in events:
                u = e['actor']
                v = e['repo']
                #print u, '-->', v
                u = self.hash_put(u, Loader.ACTOR)
                v = self.hash_put(v, Loader.REPO)
                row.append(u)
                col.append(v)
                row.append(v)
                col.append(u)

                if self._weighting == 'time':
                    # Happening time
                    x = time.mktime(time.strptime(e['created_at'], '%Y-%m-%dT%H:%M:%SZ'))
                    # Gaussian distribution
                    w = coefficient * math.exp(-(x-mu)*(x-mu)/(2.0*theta*theta))
                elif self._weighting == 'norm':
                    w = 1.0

                # TODO THE bidirected edge should have 2 different weight. At least normalized !!!!!!!!!
                data.append(w)
                data.append(w)

        sum = dict()
        for r, d in itertools.izip(row, data):
            sum.setdefault(r, 0.0)
            sum[r] += d
        for i, r in enumerate(row):
            data[i] /= sum[r]
        return sparse.coo_matrix((data, (row, col)))

    def load_test(self, days):
        test = dict()
        db_dir = 'experiments'
        for day in days:
            data_file = '{}/watch_day{}.pkl.gz'.format(db_dir, day)
            events = pickle.load(gzip.open(data_file, 'r'))
            for e in events:
                u = d['actor']
                v = d['repo']

                # Using integer as dict index is faster
                u = self.hash_put(u, Loader.ACTOR)
                v = self.hash_put(v, Loader.REPO)

                test[u].setdefault(set()).add(v)
        return test


class Checker(object):

    def __init__(self, d, recommendation, test):
        self._d = d
        self._recommendation = recommendation
        self._test = test

    # TODO recall ratio
    def check(self):
        predicted = 0
        for r, c in itertools.izip(self._recommendation.row, self._recommendation.col):
            if u in self._test and c in self._test[u]:
                predicted += 1
        precision = float(predicted) / self._recommendation.nnz


def load_data():
    loader = Loader()
    A = loader.load_train([0,1])
    #test = loader.load_train([7])
    h = loader.hash
    r_h = loader.re_hash
    return A, h, r_h


if __name__ == '__main__':
    '''
    A = sparse.coo_matrix([
        [0, 0.5, 0, 0.5, 0],
        [1, 0, 0, 0, 0],
        [0, 0, 0, 0.5, 0.5],
        [0.5, 0, 0.5, 0, 0],
        [0, 0, 1, 0, 0]
        ]
    )
    '''
    A, h, r_h = load_data()

    '''
    with open('/tmp/data', 'w') as f:
        f.write(','.join(map(str,list(A.data))))
    with open('/tmp/row', 'w') as f:
        f.write(','.join(map(str,list(A.row))))
    with open('/tmp/col', 'w') as f:
        f.write(','.join(map(str,list(A.col))))
    '''
    c = 0.2
    d = sparse.coo_matrix(([1], ([1], [0])), shape=(A.shape[0], 1))
    topks = pagerank(A, c, d)
    print topks

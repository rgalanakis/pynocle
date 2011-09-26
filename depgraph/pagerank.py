#!/usr/bin/env python
"""
Functionality ripped off from http://kraeutler.net/vincent/essays/google%20page%20rank%20in%20python and left
intact other than using 'import numpy' rather than 'from numpy import *', and fix fixing up references.

The 'link matrices' used by transposeLineMatrix and pageRank can be described as a list of lists (rows),
where the items in a row are indices to other rows in the containing list.  So:
[
  [0, 2, 2, 3], #Row 0.  Contains a link to itself, 2 to row2 (no difference from 1 to row2), and 1 to row3.
  [0], #Row 1.  Contains a link to row0.
  [3, 2], #Row 2.  Contains a link to itself and row3.
  [0], #Row 3.  Contains a link to row0.
]
would return page ranks of [ 0.36723503  0.0375      0.33665007  0.25861487]
See the site linked above for more explanation of the rankings.
"""
import pynocle.utils as utils

try:
    import numpy
except ImportError:
    numpy = utils.MissingDependencyError('Could not import numpy, cannot generate page ranking.')

def _transposeLinkMatrix(
        outGoingLinks = None
        ):
        """
        Transpose the link matrix. The link matrix contains the pages each page points to.
        However, what we want is to know which pages point to a given page. However, we
        will still want to know how many links each page contains (so store that in a separate array),
        as well as which pages contain no links at all (leaf nodes).

        @param outGoingLinks outGoingLinks[ii] contains the indices of pages pointed to by page ii
        @return a tuple of (incomingLinks, numOutGoingLinks, leafNodes)
        """
        outGoingLinks = outGoingLinks or [[]]

        nPages = len(outGoingLinks)
        # incomingLinks[ii] will contain the indices jj of the pages linking to page ii
        incomingLinks = [[] for ii in range(nPages)]
        # the number of links in each page
        numLinks = numpy.zeros(nPages, numpy.int32)
        # the indices of the leaf nodes
        leafNodes = []

        for ii in range(nPages):
                if not len(outGoingLinks[ii]):
                        leafNodes.append(ii)
                else:   
                        numLinks[ii] = len(outGoingLinks[ii])
                        # transpose the link matrix
                        for jj in outGoingLinks[ii]:
                                incomingLinks[jj].append(ii)
                        
        incomingLinks = [numpy.array(ii) for ii in incomingLinks]
        numLinks = numpy.array(numLinks)
        leafNodes = numpy.array(leafNodes)
                                
        return incomingLinks, numLinks, leafNodes

def _pageRankGenerator(
        At = None,
        numLinks = None,
        ln = None,
        alpha = 0.85,
        convergence = 0.01,
        checkSteps = 10
        ):
        """
        Compute an approximate page rank vector of N pages to within some convergence factor.
        @param At a sparse square matrix with N rows. At[ii] contains the indices of pages jj linking to ii.
        @param numLinks iNumLinks[ii] is the number of links going out from ii.
        @param ln contains the indices of pages without links
        @param alpha a value between 0 and 1. Determines the relative importance of "stochastic" links.
        @param convergence a relative convergence criterion. smaller means better, but more expensive.
        @param checkSteps check for convergence after so many steps
        """
        At = At if At is not None else [numpy.array((), numpy.int32)]
        numLinks = numLinks if numLinks is not None else numpy.array((), numpy.int32)
        ln = ln if ln is not None else numpy.array((), numpy.int32)

        # the number of "pages"
        N = len(At)

        # the number of "pages without links"
        M = ln.shape[0]

        # initialize: single-precision should be good enough
        iNew = numpy.ones((N,), numpy.float32) / N
        iOld = numpy.ones((N,), numpy.float32) / N

        done = False
        while not done:

                # normalize every now and then for numerical stability
                iNew /= sum(iNew)

                for step in range(checkSteps):

                        # swap arrays
                        iOld, iNew = iNew, iOld

                        # an element in the 1 x I vector.
                        # all elements are identical.
                        oneIv = (1 - alpha) * sum(iOld) / N

                        # an element of the A x I vector.
                        # all elements are identical.
                        oneAv = 0.0
                        if M > 0:
                                oneAv = alpha * sum(iOld.take(ln, axis = 0)) / N

                        # the elements of the H x I multiplication
                        ii = 0
                        while ii < N:
                                page = At[ii]
                                h = 0
                                if page.shape[0]:
                                        h = alpha * numpy.dot(
                                                iOld.take(page, axis = 0),
                                                1. / numLinks.take(page, axis = 0)
                                                )
                                iNew[ii] = h + oneAv + oneIv
                                ii += 1

                diff = iNew - iOld
                done = (numpy.sqrt(numpy.dot(diff, diff)) / N < convergence)

                yield iNew

def pageRank(
        linkMatrix = None,
        alpha = 0.85,
        convergence = 0.01,
        checkSteps = 10
        ):
        """Convenience wrap for the link matrix transpose and the generator."""
        if type(numpy) == utils.MissingDependencyError:
            raise numpy
        linkMatrix = linkMatrix or [[]]
        incomingLinks, numLinks, leafNodes = _transposeLinkMatrix(linkMatrix)

        final = 0
        for gr in _pageRankGenerator(incomingLinks, numLinks, leafNodes,
                                                                        alpha = alpha,
                                                                        convergence = convergence,
                                                                        checkSteps = checkSteps):
                final = gr

        return final

class _SortedDict(object):
    """Simple functionality for treating two parallel lists as a dictionary."""
    def __init__(self):
        self._keys = []
        self._values = []
    def items(self):
        return zip(self._keys, self._values)
    def keys(self):
        return self._keys
    def setdefault(self, key, default):
        try:
            idx = self._keys.index(key)
            return self._values[idx]
        except ValueError:
            self._keys.append(key)
            self._values.append(default)
            return default

class DependenciesToLinkMatrix(object):
    """Converts a collection of Dependency objects to a link matrix that can be passed into pageRank.  Call
    create_matrix() to generate the matrix.

    dependencies: A collection of Dependency instances of two-item tuples.
    
    node_to_outgoing_map: Sorted mapping of {dependencynode: set(dependencynodes)}.
    node_to_id_map: Mapping of dependencynode to an ID (their row index in the result matrix).
    id_to_node_map: node_to_id_map with keys as values and values as keys.
    """
    def __init__(self, dependencies):
        self.node_to_outgoing_map = self._create_node_to_outgoing(dependencies)
        self.node_to_id_map = self._create_node_to_id(self.node_to_outgoing_map.keys())
        self.id_to_node_map = utils.swap_keys_and_values(self.node_to_id_map)

    def _create_node_to_outgoing(self, dependencies):
        nodemap = _SortedDict()
        for start, end in dependencies:
            outgoing = nodemap.setdefault(start, set())
            nodemap.setdefault(end, set())
            outgoing.add(end)
        return nodemap

    def _create_node_to_id(self, keys):
        lastid = 0
        str_to_id = {}
        for k in keys:
            str_to_id[k] = lastid
            lastid += 1
        return str_to_id

    def create_matrix(self):
        """Convert the dependencies into a link matrix that can be used in pageRank."""
        matrix = [[] for i in range(len(self.node_to_id_map))]
        for k, v in self.node_to_outgoing_map.items():
            rowid = self.node_to_id_map[k]
            row = matrix[rowid]
            for outlnk in v:
                outrowid = self.node_to_id_map[outlnk]
                row.append(outrowid)
            row.sort()
        return matrix




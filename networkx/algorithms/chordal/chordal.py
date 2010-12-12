# -*- coding: utf-8 -*-
"""
This module implements routines related to 
<a href="http://en.wikipedia.org/wiki/Chordal_graph">chordal graphs</a>.

The routines are mainly based on the ideas described in

R. E. Tarjan and M. Yannakakis, Simple linear-time algorithms to test chordal-
ity of graphs, test acyclicity of hypergraphs, and selectively reduce acyclic hyper-
graphs, SIAM J. Comput., 13 (1984), pp. 566–579.

"""
__authors__ = "\n".join(['Jesus Cerquides <cerquide@iiia.csic.es>'])
#    Copyright (C) 2010 by 
#    Jesus Cerquides <cerquide@iiia.csic.es>
#    All rights reserved.
#    BSD license.

__all__ = ['is_chordal',
           'induced_nodes', 
           'chordal_graph_cliques',
           'chordal_graph_treewidth',
           'NetworkXTreewidthBoundExceeded',
           'NetworkXNonChordal']

import networkx as nx
import random
import sys

class NetworkXTreewidthBoundExceeded(nx.NetworkXException):
    """Exception raised when a treewidth bound has been provided and it has 
    been exceeded"""
    
class NetworkXNonChordal(nx.NetworkXError):
    """Exception raised when a non-chordal graph is received by a function that
    only accepts chordal graphs"""

def is_chordal(G):
    """Checks whether G is a chordal graph.
    
    The routine tries to go through every node following maximum cardinality 
    search. It returns False when it founds that the separator for any node 
    is not a clique.
    
    Parameters
    ----------
    G : NetworkX graph
	The graph to be tested for chordality
    
    Returns
    -------
    chordal : boolean. 
	True if G is a chordal graph and False otherwise
    
    Raises
    ------
    NetworkXError
        The algorithm does not support DiGraph, MultiGraph and MultiDiGraph. 
        If the input graph is an instance of one of these classes, a
        NetworkXError is raised.
        
    Examples
    --------
    >>> import networkx as nx
    >>> G=nx.Graph()
    >>> G.add_edges_from([(1,2),(1,3),(2,3),(2,4),(3,4),(3,5),(3,6),(4,5),(4,6),(5,6)])
    >>> nx.is_chordal(G)
    True
   
    """
    if G.is_directed():
	raise nx.NetworkXError(
		'Directed graphs not supported')
    if G.is_multigraph():
        raise nx.NetworkXError(
                'Multiply connected graphs not supported.')
                
    if len(_find_chordality_breaker(G))==0:
        return True
    else:
        return False


def induced_nodes(G,s,t,treewidth_bound=sys.maxint):
    """G is a chordal graph and s,t is an edge that is not in G. 

    Returns a pair (I,H) where I is the set of induced nodes in the
    path from s to t and H is the graph G plus (s,t) and an edge from
    s to every induced node in I. 

    If a treewidth_bound is provided, the search for induced nodes will end 
    as soon as the treewidth_bound is exceeded.
    
    The algorithm is inspired by algorithm 4 in 
    
    Learning Bounded Treewidth Bayesian Networks. Gal Elidan, Stephen Gould; 
    JMLR, 9(Dec):2699--2731, 2008. 

    A formal definition of induced node can also be found on that reference.

    Parameters
    ----------
    G : NetworkX graph
	Chordal graph where the algorithm will look for induced nodes
	
    s : node
	Source node to look for induced nodes
	
    t : node
	Destination node
	
    treewith_bound: floatMaximum treewidth acceptable for the graph H. The search 
    for induced nodes will end as soon as the treewidth_bound is exceeded.
   
    Returns
    -------
    I : Set of nodes
	The set of induced nodes in the path from s to t in G
    
    H : NetworkX graph
	A graph with every edge in G plus edge (s,t) and an edge from s to 
	each induced node in I. 
    
    Raises
    ------
    NetworkXError
        The algorithm does not support DiGraph, MultiGraph and MultiDiGraph. 
        If the input graph is an instance of one of these classes, a
        NetworkXError is raised.
    NetworkXNonChordal
        The algorithm can only be applied to chordal graphs. If
        the input graph is found to be non-chordal, a NetworNonChordal 
        error is raised.
        
    Examples
    --------
    >>> import networkx as nx
    >>> G=nx.Graph()  
    >>> G = nx.generators.classic.path_graph(10)
    >>> (I,h) = nx.induced_nodes(G,1,9,2)
    >>> I
    set([1,2,3,4,5,6,7,8,9])    
    """
    
    if not is_chordal(G):
	raise NetworkXNonChordal()
 
    H = nx.Graph(G)
    H.add_edge(s,t)
    I = set()
    triplet =  _find_chordality_breaker(H,s,treewidth_bound)
    while triplet:
        (u,v,w) = triplet
        I.update(triplet)
        for n in triplet:
            if n!=s:
                H.add_edge(s,n)
        triplet =  _find_chordality_breaker(H,s,treewidth_bound)
    if I:
        # Add t and the second node in the induced path from s to t.
        I.add(t)
        for u in G[s]: 
            if len(I & set(G[u]))==2:
                I.add(u)
                break
    return I,H


def chordal_graph_cliques(G):
    """Returns the set of maximal cliques of a chordal graph.
    
    The algorithm breaks the graph in connected components and performs a 
    maximum cardinality search in each component to get the cliques.
    
    Parameters
    ----------
    G: NetworkX graph
    
    Returns
    -------
    cliques: A set containing the maximal cliques in G.
    
    Raises
    ------
    NetworkXError
        The algorithm does not support DiGraph, MultiGraph and MultiDiGraph. 
        If the input graph is an instance of one of these classes, a
        NetworkXError is raised.
    NetworkXNonChordal
        The algorithm can only be applied to chordal graphs. If
        the input graph is found to be non-chordal, a NetworNonChordal 
        error is raised.
        
    Examples
    --------
    >>> import networkx as nx
    >>> G = nx.Graph()
    >>> G.add_edges_from([(1,2),(1,3),(2,3),(2,4),(3,4),(3,5),(3,6),(4,5),(4,6),(5,6),(7,8)])
    >>> G.add_node(9)    
    >>> nx.chordal_graph_cliques(G)
    set([frozenset([9]),frozenset([7,8]),frozenset([1,2,3]),frozenset([2,3,4]),frozenset([3,4,5,6])])
    """
    
    if not is_chordal(G):
	raise NetworkXNonChordal()
    
    cliques = set()
    for C in nx.connected.connected_component_subgraphs(G):
        cliques |= _connected_chordal_graph_cliques(C)
        
    return cliques


def chordal_graph_treewidth(G):
    """Returns the 
    <a href=" http://en.wikipedia.org/wiki/Tree_decomposition#Treewidth">
    treewidth</a> of G, where G is a chordal graph.
 
    Parameters
    ----------
    G : NetworkX graph
	The chordal graph which we want to measure its treewidth.
    
    Returns
    -------
    treewidth : int
	The size of the largest clique in the graph minus one.
    
    Raises
    ------
    NetworkXError
        The algorithm does not support DiGraph, MultiGraph and MultiDiGraph. 
        If the input graph is an instance of one of these classes, a
        NetworkXError is raised.
    NetworkXNonChordal
        The algorithm can only be applied to chordal graphs. If
        the input graph is found to be non-chordal, a NetworNonChordal 
        error is raised.
        
    Examples
    --------
    >>> import networkx as nx
    >>> G = nx.Graph()
    >>> G.add_edges_from([(1,2),(1,3),(2,3),(2,4),(3,4),(3,5),(3,6),(4,5),(4,6),(5,6),(7,8)])
    >>> G.add_node(9)    
    >>> nx.chordal_graph_treewidth(G)
    3
    """
   
    if not is_chordal(G):
	raise NetworkXNonChordal()
    
    max_clique = -1
    for clique in nx.chordal_graph_cliques(G):
        max_clique = max(max_clique,len(clique))
    return max_clique - 1

def _is_complete_graph(G):
    """Returns True if G is a complete graph."""
    if G.number_of_selfloops()>0:
        raise nx.NetworkXError("Self loop found in _is_complete_graph()")
    n = G.number_of_nodes()
    if n < 2:
        return True
    e = G.number_of_edges()
    max_edges = ((n * (n-1))/2)
    return e == max_edges


def _find_missing_edge(G):
    """ Given a non-complete graph G, returns a missing edge."""
    nodes=set(G)
    for u in G:
        missing=nodes-set(G[u].keys()+[u])
        if missing:
            return (u,missing.pop())


def _max_cardinality_node(G,choices,wanna_connect):
    """Returns a set of node in choices that has more connections in G 
    to nodes in wanna_connect.
    """
    max_number = None 
    for x in choices:
        number=len([y for y in G[x] if y in wanna_connect])
        if number > max_number:
            max_number = number
            max_cardinality_node = x 
    return max_cardinality_node


def _find_chordality_breaker(G,s=None,treewidth_bound=sys.maxint):
    """ Given a graph G, starts a max cardinality search 
    (starting from s if s is given and from a random node otherwise)
    trying to find a non-chordal cycle. 

    If it does find one, it returns (u,v,w) where u,v,w are the three
    nodes that together with s are involved in the cycle.
    """
   
    unnumbered = set(G)
    if s is None:
        s = random.choice(list(unnumbered))
    unnumbered.remove(s)
    numbered = set([s])
    current_treewidth = None
    while unnumbered:# and current_treewidth <= treewidth_bound:
        v = _max_cardinality_node(G,unnumbered,numbered)
        unnumbered.remove(v)
        numbered.add(v)
        clique_wanna_be = set(G[v]) & numbered
        sg = G.subgraph(clique_wanna_be)
        if _is_complete_graph(sg):
            # The graph seems to be chordal by now. We update the treewidth
            current_treewidth = max(current_treewidth,len(clique_wanna_be))
            if current_treewidth > treewidth_bound:
                raise nx.NetworkXTreewidthBoundExceeded(\
                    "treewidth_bound exceeded: %s"%current_treewidth)
        else:
            # sg is not a clique,
            # look for an edge that is not included in sg
            (u,w) = _find_missing_edge(sg)
            return (u,v,w)
    return ()
    

  
def _connected_chordal_graph_cliques(G):
    """Return the set of maximal cliques of a connected chordal graph."""
    if G.number_of_nodes() == 1:
        x = frozenset(G.nodes())
        return set([x])
    else:
        cliques = set()
        unnumbered = set(G.nodes())
        v = random.choice(list(unnumbered))
        unnumbered.remove(v)
        numbered = set([v])
        clique_wanna_be = set([v])
        while unnumbered:
            v = _max_cardinality_node(G,unnumbered,numbered)
            unnumbered.remove(v)
            numbered.add(v)
            new_clique_wanna_be = set(G.neighbors(v)) & numbered
            sg = G.subgraph(clique_wanna_be)
            if _is_complete_graph(sg):
                new_clique_wanna_be.add(v)
                if not new_clique_wanna_be >= clique_wanna_be:
                    cliques.add(frozenset(clique_wanna_be))
                clique_wanna_be = new_clique_wanna_be
            else:
                raise NetworkXNonChordal()
        cliques.add(frozenset(clique_wanna_be))
        return cliques





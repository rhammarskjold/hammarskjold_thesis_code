import gensim, sys, string, heapq, math
from get_links import Link, get_links
from synset import Synset, get_synsets_by_pos
import numpy as np

def cosine_similarity(v1, v2):
    """ returns the cosine similarity of 2 vectors 

    Args:
        v1 (np.array): first vector
        v2 (np.array): second vector

    Returns:
        float of the cossine similarity
    """
    sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    if math.isnan(sim):
        return 0.0
    return sim

def find_similar_synsets(word_vectors, reference, reference_id_set, possibilities, vector_dict, n=15):
    
    # average the reference vectors
    reference_vector = sum(r.vectorize1(word_vectors) for r in reference) / float(len(reference))

    # find the nbest by looking for vectors with largest cosine similarity to reference
    nbest = [(-1.0, "000")]*n
    for possibility in possibilities:
        if possibility.synsetid not in reference_id_set:
            vector = vector_dict.get(possibility.synsetid, None)
            if not type(vector) == np.ndarray:
                continue
            cos = cosine_similarity(reference_vector, vector)
            _ = heapq.heappushpop(nbest, (cos, possibility.synsetid))

    return [(sid, sim) for sim, sid in nbest]
    

def learn_new_links(links, possible_synsets_to, possible_synsets_from):
    """ Extends sets of words linked to synsets

    Args:
        links (list of Links): Links already of this type
        possible_synsets_to (list of Synset): possible synsets to link to
        possible_synsets_from (list of Synset): possible synsets to link from

    Return:
        A list of Links representing new propossed links
    """
    # open pretrained model
    print "loading model"
    model = gensim.models.KeyedVectors.load_word2vec_format('./GoogleNews-vectors-negative300.bin', binary=True)
    word_vectors = model.wv
    del model
    
    print "vectorizing synsets"
    id_to_vector = dict()
    for synset in (possible_synsets_to + possible_synsets_from):
        if synset.synsetid not in id_to_vector and synset.is_in(word_vectors):
            id_to_vector[synset.synsetid] = synset.vectorize1(word_vectors)

    # sort links into dictionaries
    print "sorting links into "
    links_to = dict() # links_to[s] should have a list of words s links to
    links_to_synsetids = dict() # links_to[s] should have a list of synset ids s links to
    links_from = dict() # links_from[s] should have a list of words linked to s
    links_from_synsetids = dict() # links_from[s] should have a list of synsets linked to s
    synset_lookup = dict()
    for link in links:
        s1, s2 = link.synset1, link.synset2
        if not s1.is_in(word_vectors) or not s2.is_in(word_vectors):
            continue
        if s1.synsetid not in synset_lookup:
            synset_lookup[s1.synsetid] = s1
        if s2.synsetid not in synset_lookup:
            synset_lookup[s2.synsetid] = s2
        if s1.synsetid not in links_to:
            links_to[s1.synsetid] = [s2]
            links_to_synsetids[s1.synsetid] = set([s2.synsetid])
        else:
            links_to[s1.synsetid].append(s2)
            links_to_synsetids[s1.synsetid].add(s2.synsetid)
        if s2.synsetid not in links_from:
            links_from[s2.synsetid] = [s1]
            links_from_synsetids[s2.synsetid] = set([s1.synsetid])
        else:
            links_from[s2.synsetid].append(s1)
            links_from_synsetids[s2.synsetid].add(s1.synsetid)

    # now find new links
    propossed_links_to = dict()
    print "looking for new links to"
    for s1id, s2s in links_to.iteritems():
        ref_set = links_to_synsetids[s1id]
        propossed_links_to[s1id] = find_similar_synsets(word_vectors, s2s, ref_set, possible_synsets_to, id_to_vector)

    print "looking for new links from"
    propossed_links_from = dict()
    for s2id, s1s in links_from.iteritems():
        ref_set = links_from_synsetids[s2id]
        propossed_links_from[s2id] = find_similar_synsets(word_vectors, s1s, ref_set, possible_synsets_from, id_to_vector)

    return (propossed_links_to, propossed_links_from, synset_lookup)

WN_FNAME = "wordnet_3.1+.db"
def main(args):
    links = get_links(args[0], WN_FNAME)
    possible_synsets_to = get_synsets_by_pos(args[2], WN_FNAME)
    possible_synsets_from = get_synsets_by_pos(args[1], WN_FNAME)
    proposed_links_to, proposed_links_from, _ = learn_new_links(links, possible_synsets_to, possible_synsets_from)

    output = open(args[3], "wb")
    for s1id, s2s in proposed_links_to.iteritems():
        for s2id, sim in s2s:
            output.write("%s,%s,%f\n" %(s1id, s2id, sim))

    for s2id, s1s in proposed_links_from.iteritems():
        for s1id, sim in s1s:
            output.write("%s,%s,%f\n" %(s1id, s2id, sim))

if __name__ == "__main__":
    main(sys.argv[1:])
from synset import Synset, get_synsets_by_pos
from get_links import Link, get_links
import sys, gensim, random, math
import numpy as np
import matplotlib.pyplot as plt
import sys, heapq, csv


def similarity(s1, s2, wv, avg_n=np.zeros(300), avg_v=np.zeros(300), mul=True):
    """ returns the cosine similarity of 2 synsets

    Returns:
        float of the cossine similarity
    """
    v1 = s1.vectorize1(wv) 
    v2 = s2.vectorize1(wv)
    if np.sum(v1) == 0 or np.sum(v2) == 0:
        return 0.0
    v2 = v2 / np.linalg.norm(v2)
    v1 = v1 / np.linalg.norm(v1)
    if mul:
        sim = np.dot(v1, v2) * np.dot(v2, avg_v) * np.dot(v1, avg_n)
    else:
        sim = np.dot(v1, v2) + np.dot(v2, avg_v) + np.dot(v1, avg_n)
    return sim

def main(args):
    sample = int(args[0])
    cuttoff = float(args[1])
    if cuttoff > 1.0 or cuttoff < 0.0:
        raise Exception("cuttoff must be between 0.0 and 1.0")
    
    model = gensim.models.KeyedVectors.load_word2vec_format('./GoogleNews-vectors-negative300.bin', binary=True)
    word_vectors = model.wv
    del model

    WN_FILE_NAME = "wordnet_3.1+.db"

    random_nouns = get_synsets_by_pos("n", WN_FILE_NAME)
    random_verbs = get_synsets_by_pos("v", WN_FILE_NAME)

    linked = get_links("action", WN_FILE_NAME)
    linked_n_vecs = [l.synset1.vectorize1(word_vectors) for l in linked if l.synset1.is_in(word_vectors)]
    linked_v_vecs = [l.synset2.vectorize1(word_vectors) for l in linked if l.synset2.is_in(word_vectors)]

    avg_v = sum(linked_v_vecs)
    avg_v = avg_v/np.linalg.norm(avg_v)
    avg_n = sum(linked_n_vecs)
    avg_n = avg_n/np.linalg.norm(avg_n)

    random_sample = [(random.choice(random_nouns), random.choice(random_verbs)) for _ in range (sample)]
    random_sample = [(similarity(n, v, word_vectors, avg_n, avg_v), n.synsetid, v. synsetid) for n, v in random_sample]

    search_sample = heapq.nlargest(int(sample * cuttoff), random_sample)

    with open(args[2], 'wb') as f:
        writer = csv.writer(f)
        for sim, nid, vid in search_sample:
            writer.writerow([nid, vid, sim])
        

if __name__ == "__main__":
    main(sys.argv[1:])
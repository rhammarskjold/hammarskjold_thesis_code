import sqlite3
import numpy as np
POS_MAP = {1: "n", 2: "v", 3:"a", 5:"s"}
class Synset:
    """ A class that represents holds relevant information for a synset 
    
    Args:
        synsetid (int): the synsetid in wn_db
        wn_db (sqlite cursor): a sqlite cursor that can access WordNet information
        get_gloss (bool, optional): boolean for if we should get the gloss from the database
        provided_gloss (str, optional): gloss of the synset
    Attributes:
        words (list of str): the words accociated with the synset
        sense_keys (list of str): the sensekeys (old) accociated with the synset
        synsetid (int): the synsetid in wn_db
        pos (str): the part of speech
    """

    def __init__(self, synsetid, wn_db, get_glosss=False, provided_gloss=None):
        wn_db.execute("SELECT old_sensekey, wordid FROM senses WHERE synsetid=?", (synsetid,))
        fetched_data = wn_db.fetchall()
        self.sense_keys = [t[0] for t in fetched_data]
        self.wordids = [t[1] for t in fetched_data]
        self.words = [s.split("%")[0] for s in self.sense_keys]
        self.synsetid = synsetid
        try:
            self.pos = POS_MAP.get(int(self.sense_keys[0].split("%")[1][0]), "?") # pos number if right after % in old sensekeys
        except:
            self.pos = "?"
        self.gloss = provided_gloss
        self.wn_db = wn_db
        self._num_senses = None
        if get_glosss:
            wn_db.execute("SELECT definition FROM synsets WHERE synsetid=?", (synsetid,))
            self.gloss = wn_db.fetchone()[0]

    def _get_number_of_senses(self):

        def f(wordid):
            self.wn_db.execute("SELECT count(1) FROM senses WHERE wordid=?", (wordid,))
            return float(self.wn_db.fetchone()[0])
        
        self._num_senses = [f(wid) for wid in self.wordids]

    def __repr__(self):
        return ",".join(self.sense_keys)

    def is_in(self, obj):
        """ Returns whether a word in the synset is included in obj. 
        
        Args:
            obj (set, dict, list): object to see if words in

        Returns:
            True if one of the words is in obj False otherwise
        """
        for w in self.words:
            if w in obj:
                return True

        return False

    def words_in(self, obj):
        """ Returns all words in synset also in obj
        
        Args:
            obj (set, dict, list): object to see if words in

        Returns:
            list of words in this synset that are also in obj
        """
        return [w for w in self.words if w in obj]

    def vectorize1(self, word_vectors):
        """ Returns from a word vector by averaging the vectors of words accociated with it
                    sum(v_w/s_w) / sum(1/s_w)
        where v_w is w's vector and s_w is the number of senses w has

        Args:
            word_vectors (gensim.KeyedVectors): gensim KeyedVecor model holding the word vectors

        Returns:
            numpy array of the resulting vector
        """
        if not self._num_senses:
            self._get_number_of_senses()
        

        if len(self.words_in(word_vectors)) == 0:
            return np.zeros_like(word_vectors[word_vectors.vocab.keys()[0]])
        # get s_ws
        sm = sum(word_vectors[w] / float(ns) for w, ns in zip(self.words, self._num_senses) if w in word_vectors) 
        return sm / np.linalg.norm(sm)
        
def get_synsets_by_pos(pos, wn_fname):
    """ Get a list of synsets belonging to a part of speech

    Args:
        pos (str): string representing the part of speech for desired synsets
    
    Returns:
        list of Synset objects with all synsets of a type
    """
    if pos not in ["n", "v", "a", "s"]:
        raise Exception("no such pos: %s, must be in {n, v, a, s}" % pos)

    con = sqlite3.connect(wn_fname)
    wn_db = con.cursor()

    wn_db.execute("SELECT synsetid, definition FROM synsets WHERE pos=?", (pos,))
    return [Synset(snid, wn_db, provided_gloss=gloss) for snid, gloss in wn_db.fetchall()]

def test():
    con = sqlite3.connect("wordnet_3.1+.db")
    wn_db = con.cursor()
    synset = Synset(113679408, wn_db, get_glosss=True)

    wv = dict()
    wv["cipher"] = np.array([1.0, 0.0, 0.0, 0.0])
    wv["cypher"] = np.array([0.0, 1.0, 0.0, 0.0])
    wv["zero"] = np.array([0.0, 0.0, 1.0, 0.0])
    wv["hi"] = np.array([0.0, 0.0, 0.0, 1.0])

    _ = get_synsets_by_pos("n", "wordnet_3.1+.db")

if __name__ == "__main__":
    test()
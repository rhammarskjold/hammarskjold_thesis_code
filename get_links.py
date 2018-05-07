
import sqlite3
from sqlite3 import Error
from synset import Synset
import sys


class Link:

    """ A class that represents two linked synsets 
    
    Args:
        synsetid1 (int): the synsetid of the first synset in wn_db
        synsetid1 (int): the synsetid of the second synset in wn_db
        linktyp (str): what kind of link it is
        wn_db (sqlite cursor): a sqlite cursor that can access WordNet information

    Attributes:
        linktyp (str): what kind of link it is
        synset1 (Synset): obj of the first synset
        synset2 (Synset): obj of the second synset
    """
    def __init__(self, synset1id, synset2id, linktyp, wn_db, with_gloss=False):
        self.synset1 = Synset(synset1id, wn_db, get_glosss=with_gloss)
        self.synset2 = Synset(synset2id, wn_db, get_glosss=with_gloss)
        self.linktyp = linktyp

    def __repr__(self):
        return self.synset1.__repr__() + "-->" + self.synset2.__repr__()

    def __str__(self):
        return self.synset1.__repr__() + "-->" + self.synset2.__repr__()

    def dif_vector(self, word_vectors):
        if not (self.synset1.is_in(word_vectors) and self.synset2.is_in(word_vectors)):
            return None
        v1 = self.synset1.vectorize1(word_vectors)
        v2 = self.synset2.vectorize1(word_vectors)
        return v1 - v2

    def as_list(self):
        l = [self.synset1.synsetid, self.synset2.synsetid, self.synset1.pos, self.synset2.pos, 
                " ".join(self.synset1.words).encode('ascii', 'ignore').decode('ascii'), 
                " ".join(self.synset2.words).encode('ascii', 'ignore').decode('ascii'),
                self.synset1.gloss.encode('ascii', 'ignore').decode('ascii'),
                self.synset2.gloss.encode('ascii', 'ignore').decode('ascii')]
        return l


def get_links(link, wn_fname, with_glosses=False):
    """ gets all the semantic links of typ link

    Attributes
        link (str): the type of link 
        wn_fname (str): the file name of the sql WordNet

    Return:
        list of Links for all the semantic links found
    """
    con = sqlite3.connect(wn_fname)
    wn_db = con.cursor()
    
    # get linkid
    wn_db.execute("SELECT linkid, linktype FROM linktypes WHERE link=?", (link,))
    linkid, linktype = wn_db.fetchone()

    # make sure looking for sem links
    if not linkid or linktype=="lex":
        raise Exception("cannot search for %s links" % link)

    # search for all links
    wn_db.execute("SELECT synset1id, synset2id FROM semlinks WHERE linkid=?", (linkid,))
    linked_synsetids = wn_db.fetchall()
    linked_wordlists = [Link(snid1, snid2, link, wn_db, with_gloss=with_glosses) for snid1, snid2 in linked_synsetids]

    return linked_wordlists
    


def main(args):
    link = args[0]
    wn_fname = args[1]
    links = get_links(link, wn_fname)
    for link in links:
        print link
    print "%d links found" % len(links)

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
import sqlite3
from Queue import Queue


class Wn_Searchable:
    def __init__(self, wn_fname):
        con = sqlite3.connect(wn_fname)
        self.wn_db = con.cursor()

    def find_synsets(self, words):
        """ given a list of words it will find synsets

            Args:
                words (list of str): list of words

            Return:
                List of synsetids
        """
        self.wn_db.execute("SELECT synsetid FROM senses WHERE wordid IN (SELECT wordid FROM words WHERE lemma in ({0}))".format(", ".join("?" for _ in words), words))
        return set([t[0] for t in self.wn_db.fetchall()])
    
    def get_synsetid_from_sensekey(self, sensekey):
        self.wn_db.execute("SELECT synsetid FROM senses WHERE old_sensekey=?", (sensekey,))
        return self.wn_db.fetchone()[0]

    def get_synsetids(self, word):
        self.wn_db.execute("SELECT synsetid FROM senses WHERE wordid IN (SELECT wordid FROM morphmaps WHERE morphid IN (SELECT morphid FROM morphs WHERE morph=?) UNION ALL SELECT wordid FROM words WHERE lemma=?)", (word,word,))
        return set([t[0] for t in self.wn_db.fetchall()])

    def get_linked_synsets(self, src, link_typ):
        self.wn_db.execute("SELECT synset2id FROM semlinks WHERE synset1id=?", (src,))
        connected = self.wn_db.fetchall()
        self.wn_db.execute("SELECT synset1id FROM semlinks WHERE synset2id=?", (src,))
        connected += self.wn_db.fetchall()
        return set([a[0] for a in connected])

    def get_gloss(self, synsetid):
        self.wn_db.execute("SELECT definition FROM synsets WHERE synsetid=?", (synsetid,))
        return self.wn_db.fetchone()[0]

    def get_dist(self, src, dst, link_typ=""):
        if dst == src:
            return 0
        to_see = Queue()
        to_see.put((src, 0))
        seen = set()
        while not to_see.empty():
            current, dist = to_see.get()
            connected = self.get_linked_synsets(current, link_typ)
            connected = connected - seen
            seen |= connected
            if dst in connected:
                return dist + 1
            for synsetid in connected:
                to_see.put((synsetid, dist + 1))

        return -1

    def get_min_dist_to_set(self, src, dst, link_typ="", max_dist=12):
        if dst == src:
            return 0
        to_see = Queue()
        to_see.put((src, 0))
        seen = set()
        while not to_see.empty():
            current, dist = to_see.get()
            connected = self.get_linked_synsets(current, link_typ)
            connected = connected - seen
            seen |= connected
            if dst & connected:
                return dist + 1
            for synsetid in connected:
                to_see.put((synsetid, dist + 1))

        return max_dist
    
    def get_dists(self, src, dsts, link_typ="", max_dist=12):
        
        dists = dict()
        if src in dsts:
            dists[src] = 0
            dsts -= set([src])
        to_see = Queue()
        to_see.put((src, 0))
        seen = set()
        while not to_see.empty() and dsts:
            current, dist = to_see.get()
            if dist == max_dist:
                for dst in dsts:
                    dists[dst] = max_dist
                break
            connected = self.get_linked_synsets(current, link_typ)
            connected = connected - seen
            seen |= connected
            found = dsts & connected
            dsts -= found
            if found:
                for s in found:
                    dists[s] = dist + 1
            for synsetid in connected:
                to_see.put((synsetid, dist + 1))

        return dists

    def get_senses(self, word, pos=""):
        self.wn_db.execute("SELECT old_sensekey FROM senses WHERE wordid IN (SELECT wordid FROM morphmaps WHERE morphid IN (SELECT morphid FROM morphs WHERE morph=?) UNION ALL SELECT wordid FROM words WHERE lemma=?)", (word,word,))
        return [t[0] for t in self.wn_db.fetchall()]

def main():
    wns = Wn_Searchable("wordnet_3.1+.db")
    print wns.get_senses("wolves")
    print wns.get_senses("wolf")
    print wns.find_synsets(["wolf", "club", "misssplng"])
    d1 = wns.get_dist(102849662, 103982640, "") # 'a motor vehicle equipped to collect blood donations' and 'a fast car that competes in races'
    d2 = wns.get_dist(102849662, 111605078, "") # 'a motor vehicle equipped to collect blood donations' and 'a plant cultivated for its blooms or blossoms'
    d3 = wns.get_dist(102849662, 202061134, "") # 'a motor vehicle equipped to collect blood donations' and 'drive in front of another vehicle leaving too little space for that vehicle to maneuver comfortably'
    print d1, d2, d3
    d4 = wns.get_dists(102849662, set([103982640, 111605078, 202061134]), "")
    print d4
    

if __name__ == "__main__":
    main()
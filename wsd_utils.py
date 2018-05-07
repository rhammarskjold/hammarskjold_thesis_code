import random as rand
from wn_searching import Wn_Searchable

WN_FILE = "wordnet_3.1+.db"

class WsdTestResults:

    def __init__(self, scores, options, corrects):
        self.scores = scores
        self.options = options
        self.corrects = [set(lst) for lst in corrects]
        self.predictions = []
        n_correct = 0
        
        for scores_i, options_i, correct in zip(self.scores, options, self.corrects):
            _, prediction = max((s, o) for s, o in zip(scores_i, options_i))
            if prediction in correct:
                n_correct += 1

        self.accuracy = float(n_correct) / len(scores)

    def dif_in_avgs(self):
        dif_avgs = []
        for scores, correct, options in zip(self.scores, self.corrects, self.options):
            sum_correct = 0.0
            sum_incorrect = 0.0
            n_correct = 0.0
            n_incorrect = 0.0
            for score, option in zip(scores, options):
                if option in correct:
                    sum_correct += score
                    n_correct += 1
                else:
                    sum_incorrect += score
                    n_incorrect += 1
            dif_avgs.append(sum_incorrect/n_incorrect - sum_correct/n_correct)
        return dif_avgs

    def dif_in_mins(self):
        dif_mins = []
        for scores, correct, options in zip(self.scores, self.corrects, self.options):
            min_correct = min(s for s, o in zip(scores, options) if o in correct)
            min_incorrect = min(s for s, o in zip(scores, options) if o not in correct)
            dif_mins.append(min_incorrect - min_correct)
        return dif_mins

POS_MAP = {
    "NOUN": "%1:",
    "VERB": "%2:",
    "ADJ": "%3:",
    "ADV": "%4:"
}

class WsdTester:

    def __init__(self, n=0):
        test_cases = open("testcases").read().splitlines()

        # parse testcases document
        def parse(test):
            args = test.split(",")
            context = args[0].split()
            target = context.pop((len(context) - 1) / 2)
            l = len(args)
            return (context, target, args[1:l-1], POS_MAP.get(args[l-1], "NONE"))
        test_cases = map(parse, test_cases)
        
        self.wn = Wn_Searchable(WN_FILE)

        # use wn to get possible sense options to choose from
        test_cases = [(c, t, a, filter(lambda s: pos in s, self.wn.get_senses(t))) for c, t, a, pos in test_cases]

        # filter out test cases where possible senses do not overlap with correct
        test_cases = filter(lambda t: len(set(t[2]) & set(t[3])) != 0, test_cases)
        test_cases = filter(lambda t: len(set(t[3]) - set(t[2])) != 0, test_cases)
        
        # pick random tests
        if n > 0:
            test_cases = rand.sample(test_cases, n)

        self.contexts, self.targets, self.answers, self.options = zip(*test_cases)
        
    def test(self, predict_function, args):

        # use prediction function on all test cases
        scores = [predict_function(c, t, o, self.wn, args) for c, t, o in zip(self.contexts, self.targets, self.options)]

        # return prediction result
        return WsdTestResults(scores, self.options, self.answers)

    def print_tests(self):
        for t, o, a in zip(self.targets, self.options, self.answers):
            print "%s: %s FROM %s" % (t, ", ".join(a), ", ".join(o))

def random_baseline(context, target, options, wn, args):
    return [rand.random() for _ in options]

def h1(context, target, options, wn, args):
    context_synsets = [wn.get_synsetids(w) for w in context]
    all_context_synsets = reduce(lambda s, x: x | s, context_synsets)

    scores = []
    for option in options:
        synsetid = wn.get_synsetid_from_sensekey(option)
        dists_map = wn.get_dists(synsetid, all_context_synsets)
        scores.append(sum(min([12] + [dists_map.get(sid, 12) for sid in s]) for s in context_synsets))
    
    return scores

def h2(context, target, options, wn, args):
    context_synsets = [wn.get_synsetids(w) for w in context]
    all_context_synsets = reduce(lambda s, x: x | s, context_synsets)

    scores = []
    for option in options:
        synsetid = wn.get_synsetid_from_sensekey(option)
        scores.append(wn.get_min_dist_to_set(synsetid, all_context_synsets))
    
    return scores


if __name__ == "__main__":
    tester = WsdTester(100)
    print "random baseline accuracy: %2.1f%%" % (tester.test(random_baseline, None).accuracy * 100)
    print "shortest distance accuracy: %2.1f%%" % (tester.test(shortest_distance, [simple_scoring_function]).accuracy * 100)

    
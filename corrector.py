
import sys
from models import extract_bigrams
from collections import defaultdict
import marshal

queries_loc = 'data/queries.txt'
gold_loc = 'data/gold.txt'
google_loc = 'data/google.txt'

alphabet = "abcdefghijklmnopqrstuvwxyz0123546789&$+_' "

class SpellCorrector:

  def __init__(self):
    self.unigram_log_probs = unserialize_data('unigramLogProbs')
    self.bigram_log_probs = unserialize_data('bigramLogProbs')
    self.bigram_index = unserialize_data('bigramIndex')

  def correct_query(self, query):
    query_words = query.rsplit()

    for word in query_words:
      candidates = self.gen_candidates(word)

    # TODO: Score in candidate set based on whether using empirical or uniform edit
    # distance model.

  # Generates list of candidates that could replace word
  def gen_candidates(self, word):
    candidates = []

    bigrams = extract_bigrams(word)

    # Counts how many bigrams a given word has in common with word
    overlap_count = defaultdict(lambda: 0)
    for bigram in bigrams:
      words_with_bigram = self.bigram_index[bigram]
      for candidate_word in words_with_bigram:
        overlap_count[candidate_word] += 1
    
    for (candidate, overlap) in overlap_count.iteritems():
      bigrams_in_candidate = extract_bigrams(candidate)
      all_bigrams = bigrams_in_candidate | bigrams
      jaccard = float(overlap) / len(all_bigrams)
      if jaccard > 0.5:
        candidates.append(candidate)

    print 'candidates for ' + word + ':' + str(candidates)
    # TODO filter candidates based on edit distance (only 1 or 2 edits allowed)
    # TODO figure out how to take care of 'space' issue (how to generate isaac
    # newton as candidate for isaacnewton) -- see helpful hint under "candidate
    # generation" section of handout
    # TODO don't forget to take care of case where there are no candidates


  def read_query_data(self, queries_loc):
    """
    all three files match with corresponding queries on each line
    NOTE: modify the signature of this method to match your program's needs
    """
    queries = []
    #gold = []
    #google = []
    with open(queries_loc) as f:
      for line in f:
        queries.append(line.rstrip())
    return queries
    #with open(gold_loc) as f:
    #  for line in f:
    #    gold.append(line.rstrip())
    #with open(google_loc) as f:
    #  for line in f:
    #    google.append(line.rstrip())
    #assert( len(queries) == len(gold) and len(gold) == len(google) )
    #return (queries, gold, google)

def unserialize_data(fname):
  """
  Reads a pickled data structure from a file named `fname` and returns it
  IMPORTANT: Only call marshal.load( .. ) on a file that was written to using marshal.dump( .. )
  marshal has a whole bunch of brittle caveats you can take a look at in teh documentation
  It is faster than everything else by several orders of magnitude though
  """
  with open(fname, 'rb') as f:
    return marshal.load(f)

# Calculates Levenshtein-Damerau edit distance between word 1 and word 2.
def find_edit_distance(word1, word2):
  # Save rows of matrix rather than whole matrix for efficiency
  last_row = None
  this_row = range(1, len(word2) + 1) + [0]
  # Cost is 0 if letters are equal, 1 otherwise
  cost = 0
  for i in range(len(word1)):
    # Row reassignment on new row
    last_last_row = last_row
    last_row = this_row
    this_row = [0] * len(word2) + [i+1]
    for j in range(len(word2)):
      if word1[i] == word2[j]:
        cost = 0
      else:
        cost = 1
      this_row[j] = min(last_row[j] + 1, this_row[j-1] + 1, last_row[j-1] +
        cost)
      # Deal with transpositions
      if i>0 and j>0 and word1[i] == word2[j-1] and word1[i-1] == word2[j]:
        this_row[j] = min(this_row[j], last_last_row[j-2] + 1)

  return this_row[len(word2) - 1]
if __name__ == '__main__':
  print(find_edit_distance('ass', 'sas'))
  #queries_loc = sys.argv[2]
  #sc = SpellCorrector()
  #queries = sc.read_query_data(queries_loc)
  #print 'done reading query data'
  #for query in queries:
  #  corrected = sc.correct_query(query)


import sys
from models import extract_bigrams
from collections import defaultdict
import marshal
import math
import itertools

queries_loc = 'data/queries.txt'
gold_loc = 'data/gold.txt'
google_loc = 'data/google.txt'

alphabet = "abcdefghijklmnopqrstuvwxyz0123546789&$+_' "

class SpellCorrector:

  def __init__(self):
    self.unigram_probs = unserialize_data('unigramProbs')
    self.bigram_probs = unserialize_data('bigramProbs')
    self.bigram_index = unserialize_data('bigramIndex')
    self.len_dict = unserialize_data('lenDict')

    self.insertion_dict = unserialize_data('insertionDict')
    self.deletion_dict = unserialize_data('deletionDict') 
    self.substitution_dict = unserialize_data('substitutionDict') 
    self.transposition_dict = unserialize_data('transpositionDict')
    self.unigram_counts = unserialize_data('unigramCounts')
    self.bigram_counts = unserialize_data('bigramCounts')


  def correct_query(self, query, edit_type):
    query_words = query.rsplit()

    new_query = []
    prevWord = None
    iterator = range(len(query_words)).__iter__()

    for i in iterator:
      word = query_words[i]

      # Check if word is misspelled (not in our dictionary)
      if word in self.unigram_probs:
        new_query.append(word)
        prevWord = word
        continue
       
      candidates = self.gen_candidates(word, edit_type)
      best_score = None
      best_candidate = word
      for (candidate, edit_dist) in candidates:
        # Not first word of query
        if prevWord is None or (prevWord, candidate) not in self.bigram_probs:
          bigram_prob = 0
        else:
          bigram_prob = self.bigram_probs[(prevWord, candidate)] 

        score = math.log10(0.2 * self.unigram_probs[candidate] + 0.8 *
          bigram_prob) 
        if edit_type == 'uniform':
          score += math.log10(
          (0.1 ** edit_dist) * (0.9 ** (len(word) - edit_dist)))
        else:
          score += edit_dist
        if best_score is None or score > best_score:
          best_score = score
          best_candidate = candidate
      new_query.append(best_candidate)
      prevWord = best_candidate
    correct_query = ' '.join(new_query)
    return correct_query

  # Generates list of candidates that could replace word
  def gen_candidates(self, word, edit_type):
    candidates = set()

    word_len = len(word)

    for i in range(word_len - 2, word_len + 3):
      if i <= 0: continue

      wordsOfLenI = self.len_dict[i]
      bigrams = extract_bigrams(word)

      for candidate in wordsOfLenI:

        #compute jaccard similarity, throw out candidates based on this for speed
        if len(word) > 3: 
          bigrams_in_candidate = extract_bigrams(candidate)
          all_bigrams = bigrams_in_candidate | bigrams
          overlap = bigrams_in_candidate & bigrams
          jaccard = float(len(overlap)) / len(all_bigrams)
          if jaccard < 0.5: continue

        edit_dist = find_edit_distance(word, candidate)
        if edit_dist <= 2:
          if edit_type == 'uniform':
            candidates.add((candidate, edit_dist))
          else:
            candidates.add((candidate, self.empirical_edit_probability(word,
              candidate)))

    return candidates

  #calculates probability of most likely empirical edit (in log space) 
  def empirical_edit_probability(self, word1, word2): 
    # Save rows of matrix rather than whole matrix for efficiency
    last_row = None
    #this_row = range(1, len(word2) + 1) + [0]
    this_row = [0] * (len(word2) + 1)
    char_1 = '#'
    # the zero row for empirical distance - uses insertion dict
    for i in range(len(word2)):
      char_2 = word2[i]
      this_row[i] = this_row[i-1] + self.dict_lookup('i', char_1, char_2)  
      char_1 = word2[i]
    
    char_1 = '#'
    for i in range(len(word1)):
      # Row reassignment on new row
      last_last_row = last_row
      last_row = this_row
      char_2 = word1[i]
      # the zero column uses deletion dict
      this_row = [0] * len(word2) + [last_row[-1] + self.dict_lookup('d', char_1, char_2)]
      row_max = -15
      for j in range(len(word2)): 
        char_1 = word1[i]
        char_2 = word2[j]
        if char_1 == char_2:
          # probability of no edit
          sub_prob = log10(.92)
        else:
          sub_prob = self.dict_lookup('s', char_1, char_2)
  
        if i == 0: char_1 = '#'
        else: char_1 = word1[i-1]
        ins_prob = self.dict_lookup('i', char_1, char_2)
        
        char_2 = word1[i]
        del_prob = self.dict_lookup('d', char_1, char_2)
        
        if i > 0 and char_1 != char_2:
          trans_prob = self.dict_lookup('t', char_1, char_2)     
        
        this_row[j] = max(last_row[j] + del_prob, this_row[j-1] + ins_prob, last_row[j-1] +
          sub_prob)
        # Deal with transpositions
        if i>0 and j>0 and char_1 != char_2 and word1[i] == word2[j-1] and word1[i-1] == word2[j]:
          this_row[j] = max(this_row[j], last_last_row[j-2] + trans_prob)
          
        if this_row[j] > row_max:
          row_max = this_row[j]
          
      char_1 = word1[i]  
      
      #cutoff threshold, for speed  
      if row_max < -10:
        return -10
    
    return this_row[len(word2) - 1]
  
  def dict_lookup(self, which, char_1, char_2):
    A = len(self.unigram_counts)
    B = len(self.bigram_counts)
    
    if which == 'i':
      if char_1 in self.insertion_dict and char_2 in self.insertion_dict[char_1]:
        return self.insertion_dict[char_1][char_2]
      else: return log10(1/float(self.unigram_counts[char_1] + A))  
      
    if which == 'd':
      if char_1 in self.deletion_dict and char_2 in self.deletion_dict[char_1]:
        return self.deletion_dict[char_1][char_2]
      else: return log10(1/float(self.bigram_counts[char_1 + char_2] + B))  
        
    if which == 's':
      if char_1 in self.substitution_dict and char_2 in self.substitution_dict[char_1]:
        return self.substitution_dict[char_1][char_2]
      else: return log10(1/float(self.unigram_counts[char_1] + A))       
      
    if which == 't':
      if char_1 in self.transposition_dict and char_2 in self.transposition_dict[char_1]:
        return self.transposition_dict[char_1][char_2]
      else: return log10(1/float(self.bigram_counts[char_1 + char_2] + B))  



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
    row_min = 100
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

      if this_row[j] < row_min:
        row_min = this_row[j]

    if row_min > 2:
      # Return early if it's impossible for a match within edit distance 2 to
      # occur
      return 3
      
  return this_row[len(word2) - 1]

if __name__ == '__main__':
  edit_type = sys.argv[1]
  queries_loc = sys.argv[2]
  sc = SpellCorrector()
  queries = sc.read_query_data(queries_loc)
  i = 1
  for query in queries:
    corrected = sc.correct_query(query, edit_type)
    print >> sys.stderr, 'query ' + str(i)
    print >> sys.stderr, 'original: ' + query + ', fixed: ' + corrected
    print corrected
    i+= 1


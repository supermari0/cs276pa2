
import sys
import os.path
#import gzip
from glob import iglob
from math import log10
import marshal

class LanguageModel:

  def __init__(self):
    # Hold the counts for unigram words and bigram words
    self.unigram_counts = dict()
    self.bigram_counts = dict()

    # Holds an index where each character bigram is the key and the value is a
    # list of words containing that character bigram. (start, c) indicates that
    # a word begins with c and (d, end) indicates that a word ends with d.
    self.bigram_index = dict()

    # Holds a count for the total number of terms in the corpus
    self.term_count = 0

  def build_language_model(self, training_corpus_dir):
    """ Computes and saves components necessary for language model (unigram and
    bigram log probabilities) to disk """

    #TODO Need to reduce amount of time this takes to <1m. Possible strategies
    # include moving probability calculations and bigram indexing for
    # correction stage.
    self.build_count_dicts(training_corpus_dir)

    unigram_log_probs = dict()
    bigram_log_probs = dict()
    for (word, count) in self.unigram_counts.iteritems():
      unigram_log_probs[word] = log10(count/float(self.term_count))
    for (bigram, count) in self.bigram_counts.iteritems():
      bigram_log_probs[bigram] = log10(count/float(self.unigram_counts[bigram[0]]))
    
    serialize_data(unigram_log_probs, 'unigramLogProbs')
    serialize_data(bigram_log_probs, 'bigramLogProbs')
    serialize_data(self.bigram_index, 'bigramIndex')

  def build_count_dicts(self, training_corpus_dir):
    """ Build dictionaries containing counts of unigrams and bigrams in training
    corpus """
    for block_fname in iglob( os.path.join( training_corpus_dir, '*.txt' ) ):
      print >> sys.stderr, 'processing dir: ' + block_fname
      with open( block_fname ) as f:
        for line in f:
          # remember to remove the trailing \n
          line = line.rstrip()
          line = line.rsplit()
          for i in range(len(line)):
            self.term_count += 1
            word = line[i]

            # Add current word to the bigram index
            word_bigrams = extract_bigrams(word)
            for bigram in word_bigrams:
              if bigram in self.bigram_index:
                self.bigram_index[bigram].add(word)
              else:
                self.bigram_index[bigram] = set(word)

            # Increment word counts
            if word in self.unigram_counts:
              self.unigram_counts[word] += 1
            else:
              self.unigram_counts[word] = 1
            if i != 0:
              bigram = (line[i-1], word)
              if bigram in self.bigram_counts:
                self.bigram_counts[bigram] += 1
              else:
                self.bigram_counts[bigram] = 1

def extract_bigrams(word):
  """Extracts all bigrams from a given word and returns them as a set."""
  word_bigrams = set()
  for j in range(len(word)):
    char = word[j]
    if j != 0:
      prevChar = word[j-1]
    else:
      prevChar = 'START'
    word_bigrams.add((prevChar, char))

  # Add end bigram
  word_bigrams.add((char, 'END'))
  return word_bigrams 

def serialize_data(data, fname):
  """
  Writes `data` to a file named `fname`
  """
  with open(fname, 'wb') as f:
    marshal.dump(data, f)

def read_edit1s():
  """
  Returns the edit1s data
  It's a list of tuples, structured as [ .. , (misspelled query, correct query), .. ]
  """
  edit1s = []
  with open(edit1s_loc) as f:
    # the .rstrip() is needed to remove the \n that is stupidly included in the line
    edit1s = [ line.rstrip().split('\t') for line in f if line.rstrip() ]
  return edit1s

if __name__ == '__main__':
  LanguageModel().build_language_model(sys.argv[1])

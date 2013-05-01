
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
    self.len_dict = dict()

    # Holds an index where each character bigram is the key and the value is a
    # list of words containing that character bigram. (start, c) indicates that
    # a word begins with c and (d, end) indicates that a word ends with d.
    self.bigram_index = dict()

    # Holds a count for the total number of terms in the corpus
    self.term_count = 0

  def build_language_model(self, training_corpus_dir):
    """ Computes and saves components necessary for language model (unigram and
    bigram log probabilities) to disk """

    self.build_count_dicts(training_corpus_dir)

    unigram_probs = dict()
    bigram_probs = dict()
    for (word, count) in self.unigram_counts.iteritems():
      unigram_probs[word] = count/float(self.term_count)
      if len(word) in self.len_dict:
        self.len_dict[len(word)].add(word)
      else:
        self.len_dict[len(word)] = set(word)
    for (bigram, count) in self.bigram_counts.iteritems():
      bigram_probs[bigram] = count/float(self.unigram_counts[bigram[0]])
    serialize_data(unigram_probs, 'unigramProbs')
    serialize_data(bigram_probs, 'bigramProbs')
    serialize_data(self.bigram_index, 'bigramIndex')
    serialize_data(self.len_dict, 'lenDict')

  def build_count_dicts(self, training_corpus_dir):
    """ Build dictionaries containing counts of unigrams and bigrams in training
    corpus """
    for block_fname in iglob( os.path.join( training_corpus_dir, '*.txt' ) ):
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

class EditModel:
  
  def __init__(self):
    # build count matrices all initialized to 1's
    self.unigram_counts = dict()
    self.bigram_counts = dict()
    self.insertion = dict()
    self.deletion = dict()
    self.substitution = dict()
    self.transposition = dict()
    
  def build_edit_model(self, edit1s_loc):
    list = read_edit1s(edit1s_loc)
    for pair in list:
      edit = self.find_edit(pair)
      if not edit: continue
      type = edit[0]
      char_1 = edit[1]
      char_2 = edit[2]
      if type == 'i':
        matrix = self.insertion
      elif type == 'd':
        matrix = self.deletion
      elif type == 's':
        matrix = self.substitution
      elif type == 't':
        matrix = self.transposition
      if not char_1 in matrix:
        matrix[char_1] = dict()
      if not char_2 in matrix[char_1]:  
        matrix[char_1][char_2] = 1
      else: matrix[char_1][char_2] += 1  
    
    logInsertion = dict()
    logDeletion = dict()
    logSubstitution = dict()
    logTransposition = dict()
    A = len(self.unigram_counts)
    B = len(self.bigram_counts)
    for (char_1, dictionary) in self.insertion.iteritems():
      logInsertion[char_1] = dict()
      for (char_2, count) in dictionary.iteritems():
        p = (count + 1)/float(self.unigram_counts[char_1] + A)
        logInsertion[char_1][char_2] = log10(p)
    for (char_1, dictionary) in self.deletion.iteritems():
      logDeletion[char_1] = dict()
      for (char_2, count) in dictionary.iteritems():
        p = (count + 1)/float(self.bigram_counts[char_1 + char_2] + B)
        logDeletion[char_1][char_2] = log10(p)    
    for (char_1, dictionary) in self.substitution.iteritems():
      logSubstitution[char_1] = dict()
      for (char_2, count) in dictionary.iteritems():
        p = (count + 1)/float(self.unigram_counts[char_1] + A)
        logSubstitution[char_1][char_2] = log10(p)  
    for (char_1, dictionary) in self.transposition.iteritems():
      logTransposition[char_1] = dict()
      for (char_2, count) in dictionary.iteritems():
        p = (count + 1)/float(self.bigram_counts[char_1 + char_2] + B)
        logTransposition[char_1][char_2] = log10(p)        
    serialize_data(logInsertion, 'insertionDict')
    serialize_data(logDeletion, 'deletionDict')  
    serialize_data(logSubstitution, 'substitutionDict')
    serialize_data(logTransposition, 'TranspositionDict')  
    serialize_data(self.unigram_counts, 'unigramCounts')
    serialize_data(self.bigram_counts, 'bigramCounts')
        
  def find_edit(self, pair): 
    right = pair[1]
    wrong = pair[0]
        
    # update unigram, bigram counts for first letter(s)   
    start_unigram = '#'
    if start_unigram in self.unigram_counts:
      self.unigram_counts[start_unigram] += 1
    else: self.unigram_counts[start_unigram] = 1 
    start_bigram = '#' + right[0] 
    if start_bigram in self.bigram_counts:
      self.bigram_counts[start_bigram] += 1
    else: self.bigram_counts[start_bigram] = 1
    
    ret = None
    for i, ch in enumerate(right): 
      if ch in self.unigram_counts:
        self.unigram_counts[ch] += 1
      else: self.unigram_counts[ch] = 1  
      if i < len(right) - 1:
        bigram = right[i:i+2] 
        if bigram in self.bigram_counts:
          self.bigram_counts[bigram] += 1
        else: self.bigram_counts[bigram] = 1
      if i < len(wrong) and right[i] == wrong[i]: continue  
      if len(right) > len(wrong):
        try_delete = right[:i] + right[i+1:]
        if try_delete == wrong:
          #edge case - first character deleted
          if i == 0: ret = ('d', '#', ch)
          else: ret = ('d', right[i-1], ch)  
      elif len(right) == len(wrong):   
        if i < len(right) - 1:
          if i < len(right) - 2:
            try_transposition = right[:i] + right[i+1] + right[i] + right[i+2:]
          else: try_transposition = right[:i] + right[i+1] + right[i]
          if try_transposition == wrong:
            ret = ('t', ch, right[i+1])   
        letter = wrong[i]
        try_substitution = right[:i] + letter + right[i+1:]
        if try_substitution == wrong:
          ret = ('s', ch, letter)
      else:
        letter = wrong[i]
        try_insert = right[:i] + letter + right[i:]
        if try_insert == wrong:
          if i == 0: ret = ('i', '#', letter)
          else: ret = ('i', right[i-1], letter)
    if ret: return ret      
    elif right == wrong: return None
    else: return ('i', right[-1], wrong[-1])

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

def read_edit1s(edit1s_loc):
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
  #LanguageModel().build_language_model(sys.argv[1])
  EditModel().build_edit_model(sys.argv[2])

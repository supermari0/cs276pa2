
import sys
import os.path
#import gzip
from glob import iglob

unigram_counts = dict()
bigram_counts = dict()
term_count = 0

def build_language_model(training_corpus_dir):
  build_count_dicts(training_corpus_dir)
  print unigram_counts

def build_count_dicts(training_corpus_dir):
  """ Build dictionaries containing counts of unigrams and bigrams in training
  corpus """
  global term_count,unigram_counts,bigram_counts
  for block_fname in iglob( os.path.join( training_corpus_dir, '*.txt' ) ):
    print >> sys.stderr, 'processing dir: ' + block_fname
    with open( block_fname ) as f:
      num_lines = 0
      for line in f:
        # remember to remove the trailing \n
        line = line.rstrip()
        line = line.rsplit()
        for i in range(len(line)):
          term_count += 1
          word = line[i]
          if word in unigram_counts:
            unigram_counts[word] += 1
          else:
            unigram_counts[word] = 1
          if i != 0:
            bigram = (line[i-1], word)
            if bigram in bigram_counts:
              bigram_counts[bigram] += 1
            else:
              bigram_counts[bigram] = 1



def scan_corpus(training_corpus_dir):
  """
  Scans through the training corpus and counts how many lines of text there are
  """
  for block_fname in iglob( os.path.join( training_corpus_dir, '*.txt' ) ):
    print >> sys.stderr, 'processing dir: ' + block_fname
    with open( block_fname ) as f:
      num_lines = 0
      for line in f:
        # remember to remove the trailing \n
        line = line.rstrip()
        num_lines += 1
      print >> sys.stderr, 'Number of lines in ' + block_fname + ' is ' + str(num_lines)

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
  build_language_model(sys.argv[1])

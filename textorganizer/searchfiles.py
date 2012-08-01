#!/usr/bin/env python
from lucene import \
    QueryParser, IndexSearcher, StandardAnalyzer, SimpleFSDirectory, File, \
    VERSION, initVM, Version, IndexReader, TermQuery, Term
import threading, sys, time, os, csv, re

"""
This script is loosely based on the Lucene (java implementation) demo class 
org.apache.lucene.demo.SearchFiles.  It will prompt for a search query, then it
will search the Lucene index in the current directory called 'index' for the
search query entered against the 'contents' field.  It will then display the
'path' and 'name' fields for each of the hits it finds in the index.  Note that
search.close() is currently commented out because it causes a stack overflow in
some cases.
"""

class Ticker(object):

    def __init__(self):
        self.tick = True

    def run(self):
        while self.tick:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1.0)


def run(searcher, analyzer, reader, command):

    """check to see whether the user specified a field"""
    m = re.match(r'([a-zA-Z]+):(.*)',command)

    if m is None:
        print "Running Lucene query \"%s\"" % (command,)
        query = QueryParser(Version.LUCENE_CURRENT, "contents",analyzer).parse(command)
    else:
        """make a TermQuery with the fieldname and value"""
        fieldname = m.group(1)
        value = m.group(2)
        print "Searching for term \"%s\" in field \"%s\"" % (value,fieldname)
        query = TermQuery(Term(fieldname,value))

    scoreDocs = searcher.search(query, reader.maxDoc()).scoreDocs

    print "%s total matching documents." % len(scoreDocs)

    allDicts = []
    allTerms = set()

    print "building unique terms"
    ticker = Ticker()
    threading.Thread(target=ticker.run).start()
    for scoreDoc in scoreDocs:
        doc = searcher.doc(scoreDoc.doc)
        vector = reader.getTermFreqVector(scoreDoc.doc,"contents")
        if vector is None: continue
        #print 'path:', doc.get("path"), 'name:', doc.get("name")
        d = dict()
        allTerms = allTerms.union(map(lambda x: x.encode('utf-8'),vector.getTerms()))
        for (t,num) in zip(vector.getTerms(),vector.getTermFrequencies()):
            d[t.encode('utf-8')] = num
        d["___path___"] = doc.get("path").encode('utf-8')
        d["___name___"] = doc.get("name").encode('utf-8')
        allDicts.append(d)
    names = set(allTerms)
    ticker.tick = False
    print "\n%s total unique terms." % len(allTerms)

    return scoreDocs, allTerms, allDicts

    # print "Ready to write TDM."
    # l = list(allTerms)
    # l.sort()
    # writeTDM(allDicts,['___name___','___path___']+l,'tdm.csv')

def writeTDM(allDicts,allTerms,fname):
    l = list(allTerms)
    l.sort()
    l = ['___name___','___path___']+l

    f = open(fname,'w')
    c = csv.DictWriter(f,l)
    print "writing header"
    dhead = dict()
    for k in l:
        dhead[k] = k
    c.writerow(dhead)
    print "iterating across dictionaries..."
    for d in allDicts:
        c.writerow(d)
    f.close()
    

if __name__ == '__main__':
    STORE_DIR = "index"
    initVM()
    print 'lucene', VERSION
    directory = SimpleFSDirectory(File(STORE_DIR))
    searcher = IndexSearcher(directory, True)
    reader = IndexReader.open(directory, True)
    analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
    run(searcher, analyzer, reader)
    searcher.close()

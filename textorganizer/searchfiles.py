#!/usr/bin/env python
from lucene import \
    QueryParser, IndexSearcher, SimpleFSDirectory, File, \
    VERSION, initVM, Version, IndexReader, TermQuery, Term, Field
import threading, sys, time, os, csv, re, codecs
from shutil import copy2

"""
This script is loosely based on the Lucene (java implementation) demo class 
org.apache.lucene.demo.SearchFiles.
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
        query = QueryParser(Version.LUCENE_CURRENT, "contents",analyzer).parse(command)
    else:
        """make a TermQuery with the fieldname and value"""
        fieldname = m.group(1)
        value = m.group(2)
        print "Searching for term \"%s\" in field \"%s\"" % (value,fieldname)
        query = TermQuery(Term(fieldname,value))

    scoreDocs = searcher.search(query, reader.maxDoc()).scoreDocs



    allDicts = []
    allTerms = set()

    for scoreDoc in scoreDocs:
        doc = searcher.doc(scoreDoc.doc)
        vector = reader.getTermFreqVector(scoreDoc.doc,"contents")
        if vector is None: continue
        
        d = dict()
        allTerms = allTerms.union(map(lambda x: x.encode('utf-8'),vector.getTerms()))
        for (t,num) in zip(vector.getTerms(),vector.getTermFrequencies()):
            d[t.encode('utf-8')] = num
        d["___path___"] = doc.get("path").encode('utf-8')
        d["___name___"] = doc.get("name").encode('utf-8')
        allDicts.append(d)
    names = set(allTerms)
    

    return scoreDocs, allTerms, allDicts

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

def write_CTM_TDM(scoreDocs, allDicts, allTerms, lucenedir, fname):
    l = list(allTerms)
    l.sort()
    
    termid_dict = {}
    for termid,term in enumerate(l):
        termid_dict[term] = termid

    # create a filename for the vocab output: tdm.csv -> tdm_vocab.csv
    split_filename_match = re.search(r'(.*)(\.[a-z0-9]+)$',fname)
    vocab_filename = split_filename_match.group(1) + '_vocab' + split_filename_match.group(2)
    md_filename = split_filename_match.group(1) + '_metadata' + split_filename_match.group(2)

    print 'Writing vocabulary list...'
    # writes vocab list in format 'termid, term'
    vocab_lines = [str(termid_dict[term]) + ',' + term for term in l]
    vocab_output = '\n'.join(['term_id,term'] + vocab_lines)
    with codecs.open(vocab_filename, 'w', encoding='UTF-8') as outf:
        outf.write(vocab_output)

    print 'Writing TDM...'
    # writes TDM in format 'filepath, name, numterms, termid1: termcount1, [termid2:termcount2], [...]'
    tdm_output = []
    for document_dict in allDicts:
        numterms = len(document_dict) - 2
        name = document_dict['___name___']
        path = document_dict['___path___']
        terms = [str(termid_dict[k]) + ':' + str(document_dict[k]) for k in document_dict.keys() if k not in ['___name___', '___path___']]
        tdm_output.append(','.join([name,path,str(numterms)] + terms))
    with codecs.open(fname, 'w', encoding='UTF-8') as outf:
        outf.write('\n'.join(tdm_output))

    print 'Writing metadata...'
    # writes metadata in CSV format
    directory = SimpleFSDirectory(File(lucenedir))
    searcher = IndexSearcher(directory, True)
    write_metadata(searcher,scoreDocs,md_filename)
    
def write_metadata(searcher,scoreDocs,fname):
    allFields = set([])
    docFields = []

    for scoreDoc in scoreDocs:
        doc = searcher.doc(scoreDoc.doc)
        df = {}
        for f in doc.getFields():
            field = Field.cast_(f)
            df[field.name()] = field.stringValue()
        docFields.append(df)
        allFields = allFields.union(set(df.keys()))

    
    fields = ['name','path'] + sorted([x for x in allFields if x not in ['name','path']])
    with codecs.open(fname, 'w', encoding='UTF-8') as outf:
        dw = csv.DictWriter(outf, fields)
        
        # writing header
        dhead = dict()
        for k in fields:
            dhead[k] = k
        dw.writerow(dhead)
        
        # writing data
        for d in docFields:
            dw.writerow(d)

def write_files(searcher,scoreDocs,outdir):

    failFlag = False

    for scoreDoc in scoreDocs:
        doc = searcher.doc(scoreDoc.doc)
        path = doc.get("path").encode('utf-8')
        try:
            copy2(path,outdir)
            print "Copied:",path
        except:
            failFlag = True
            print "Failed:",path

    if failFlag:
        "WARNING: some files failed to copy."

def print_all_files(reader):
    for i in xrange(reader.maxDoc()):
        if reader.isDeleted(i): continue
        doc = reader.document(i)
        if not os.path.isfile(doc.get("path")):
            print "%s is not a file" % (doc.get("path"),)

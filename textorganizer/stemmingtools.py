class PhraseFilter(PythonTokenFilter):
    '''
    PhraseFilter is a TokenFilter that adds in phrases (as tokens) that match
    user-defined phrases.  You can then use these tokens when exporting a TDM.
    '''
    TOKEN_TYPE_SYNONYM = "SYNONYM"
    TOKEN_TYPE_PHRASE = "PHRASE"

    def __init__(self, inStream,allPhrases):
        super(PhraseFilter, self).__init__(inStream)

        self.synonymStack = []
        self.termAttr = self.addAttribute(TermAttribute.class_)
        self.save = inStream.cloneAttributes()
        self.inStream = inStream

        revSplitPhrases = []
        for p in allPhrases:
            psplit = p.split()
            psplit.reverse()
            revSplitPhrases.append(psplit)

        self.allPhrases = revSplitPhrases
        self.lag1 = ""
        self.lag2 = ""
        self.phraseStack = []

    def incrementToken(self):

        if len(self.phraseStack) > 0:
            syn = self.phraseStack.pop()
            self.restoreState(syn)
            return True

        if not self.inStream.incrementToken():
            return False
        
        for phrase in self.allPhrases:
            addPhrase = False
            lag0 = self.termAttr.term()
            print "checking: ", self.termAttr.term()
            print phrase
            if len(phrase)==2:
                if self.lag1==phrase[1] and lag0==phrase[0]:
                    print "matched!"
                    addPhrase = True
            if len(phrase)==3:
                if self.lag2==phrase[2] and self.lag1==phrase[1] and lag0==phrase[0]:
                    print "matched!"
                    addPhrase = True
            if addPhrase:
                rPhrase = phrase
                rPhrase.reverse()
                self.addPhrase(" ".join(rPhrase))

        self.lag2 = self.lag1
        self.lag1 = self.termAttr.term()
        
        print "lag1: ", self.lag1
        print "lag2: ", self.lag2

        return True

    def addPhrase(self,arg):

        print "adding phrase", arg
        current = self.captureState()

        self.save.restoreState(current)
        AnalyzerUtils.setTerm(self.save, arg)
        AnalyzerUtils.setType(self.save, self.TOKEN_TYPE_PHRASE)
        AnalyzerUtils.setPositionIncrement(self.save, 0)
        self.phraseStack.append(self.save.captureState())


class PorterStemmerAnalyzer(PythonAnalyzer):
    '''
    An analyzer that uses the phrase filter and a list of phrases
    to add tokens for phrases as well as applying the porter stemming
    algorithm.
    '''

    def setPhrases(self, myPhrases):
        self.myPhrases = myPhrases

    def tokenStream(self, fieldName, reader):

        result = StandardTokenizer(Version.LUCENE_CURRENT, reader)
        result = StandardFilter(result)
        result = LowerCaseFilter(result)        
        result = PorterStemFilter(result)
        result = PhraseFilter(result,self.myPhrases)        
        result = StopFilter(True, result, StopAnalyzer.ENGLISH_STOP_WORDS_SET)
        return result

class QueryAnalyzer(PythonAnalyzer):
    '''
    An analyzer that uses the same filter chain as the 
    PorterStemmerAnalyzer, enabling analysis  of the individual phrases 
    using the Porter stemming algorithm and standard tokenizer.
    '''

    def tokenStream(self, fieldName, reader):

        result = StandardTokenizer(Version.LUCENE_CURRENT, reader)
        result = StandardFilter(result)
        result = LowerCaseFilter(result)
        result = PorterStemFilter(result)
        return result

def stemPhrases(allPhrases,analyzer):
    '''
    We need to porter stem the phrases in the query so that it will
    match the porterized versions.  Added benefit: if you are looking
    for the exact phrase 'buffalo wing'  you will also get 'buffalo wings'
    bug or feature?  you decide!

    sample call: stemPhrases(allPhrases,QueryAnalyzer)
    '''

    stemmedPhrases = []

    for p in allPhrases:
        query = QueryParser(Version.LUCENE_CURRENT, "removeme",
                            analyzer(Version.LUCENE_CURRENT)).parse('"'+p+'"')
        stemmedQuery = query.toString()
        stemmedPhrase = stemmedQuery.replace('removeme:','').replace('"','')
        stemmedPhrases.append(stemmedPhrase)

    return stemmedPhrases

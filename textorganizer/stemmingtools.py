from lucene import *
import codecs
from analyzerutils import AnalyzerUtils
from filters import *

class PorterStemmerAnalyzerBasic(PythonAnalyzer):
    '''
    An analyzer that stems and removes stopwords.
    '''
    
    def tokenStream(self, fieldName, reader):
        morestops = HashSet(Arrays.asList(['a','able','about','across','after','all','almost','also','am','among','an','and','any','are','as','at','be','because','been','but','by','can','cannot','could','dear','did','do','does','either','else','ever','every','for','from','get','got','had','has','have','he','her','hers','him','his','how','however','i','if','in','into','is','it','its','just','least','let','like','likely','may','me','might','most','must','my','neither','no','nor','not','of','off','often','on','only','or','other','our','own','rather','said','say','says','she','should','since','so','some','than','that','the','their','them','then','there','these','they','this','tis','to','too','twas','us','wants','was','we','were','what','when','where','which','while','who','whom','why','will','with','would','yet','you','your']))
        result = StandardTokenizer(Version.LUCENE_CURRENT, reader)
        result = NumericFilter(result)
        result = PunctuationFilter(result)        
        result = EnglishPossessiveFilter(result)                
        result = StandardFilter(result)
        result = LowerCaseFilter(result) 
        #result = StopFilter(True, result, StopAnalyzer.ENGLISH_STOP_WORDS_SET)
        result = StopFilter(True, result, morestops)
        result = PorterStemFilter(result)
	#result = StopFilter(True, result, StopAnalyzer.ENGLISH_STOP_WORDS_SET)
        return result

        
class PorterStemmerAnalyzerPhrases(PythonAnalyzer):
    '''
    An analyzer that uses the phrase filter and a list of phrases
    to add tokens for phrases as well as applying the porter stemming
    algorithm.
    '''
    def __init__(self, phrases = []): 
        PythonAnalyzer.__init__(self) 
        self.setPhrases(phrases)

    def setPhrases(self, myPhrases):
        self.myPhrases = myPhrases
        
    def tokenStream(self, fieldName, reader):

        result = StandardTokenizer(Version.LUCENE_CURRENT, reader)
        result = StandardFilter(result)
        result = LowerCaseFilter(result)        
        result = StopFilter(True, result, StopAnalyzer.ENGLISH_STOP_WORDS_SET)
        result = PorterStemFilter(result)
#       result = PhraseFilter(result,self.myPhrases)        
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


def init_PSA(phrasefile):

    print "Reading phrase definitions from %s..." % (phrasefile,)
    all_phrases = []
    try:
        with codecs.open(phrasefile,'r',encoding='UTF-8') as inf:
            for line in inf:
                all_phrases.append(line.strip())
    except:
        print "Failed. Disabling PhraseFilter"

    stemmedPhrases = stemPhrases(all_phrases,QueryAnalyzer)

    psa = PorterStemmerAnalyzer(Version.LUCENE_CURRENT)
    psa.setPhrases(stemmedPhrases)
    return psa


if __name__ == '__main__':
    print stemPhrases(['test phrase','another test'],QueryAnalyzer)

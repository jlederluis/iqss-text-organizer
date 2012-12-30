from Tkinter import *
import tkFileDialog
import math,random
import os, sys, lucene, thread, time
from lucene import Version, \
     StopAnalyzer, SimpleAnalyzer, WhitespaceAnalyzer, StandardAnalyzer
from textorganizer import stemmingtools

class analyzergui:
    def __init__(self):
        self.curlucene = lucene.initVM()
        self.root = Toplevel()
        self.root.title('txtorg')

        self.analyzers = [WhitespaceAnalyzer(),
                          SimpleAnalyzer(),
                          StopAnalyzer(Version.LUCENE_CURRENT),
                          StandardAnalyzer(Version.LUCENE_CURRENT)]
        self.analyzerliststr = ['WhitespaceAnalyzer',
                                'SimpleAnalyzer',
                                'StopAnalyzer',
                                'StandardAnalyzer']                
        
        f = PanedWindow(showhandle=True)
        lf = PanedWindow(f, relief=GROOVE, borderwidth=2,showhandle=True)
        f.pack(fill=BOTH,expand=1)
        Label(lf, text="Corpus").pack(pady=10,padx=10)

        # Items in the left frame
        self.analyzerlist = Listbox(lf, exportselection=False)
        corpusscroll = Scrollbar(lf, command=self.analyzerlist.yview)
        self.analyzerlist.configure(yscrollcommand=corpusscroll.set)
        self.analyzerlist.pack(side=LEFT,fill=BOTH, expand=1)
        corpusscroll.pack(side=LEFT, fill=Y)
        lf.pack(side=LEFT,fill=BOTH, expand=1,pady=10,padx=10)

        # Items in the right frame
        cf = PanedWindow(f, relief=GROOVE, borderwidth=2,showhandle=True)
        Label(cf, text="Sample").pack(pady=10,padx=10)

        cft = PanedWindow(cf, borderwidth=2,showhandle=True)
        cfb = PanedWindow(cf, borderwidth=2,showhandle=True)

        self.e = Entry(cft,state=DISABLED)
        self.e.pack(side=LEFT,fill=BOTH,expand=1)

        self.e.delete(0, END)
        self.e.configure(state=NORMAL)
        self.e.insert(0, "a default value")

        self.searchbutton = Button(cft, text="Tokenize",state=DISABLED,command=self.updateTokens)
        self.searchbutton.pack(side=LEFT, padx=5, pady=8)

        self.tokentext = Text(cfb)

        self.tokentext.insert(END,"Documents: 0")

        self.tokentext.pack()

        cft.pack(expand=1,fill=BOTH)
        cfb.pack(fill=X)
        cf.pack(side=LEFT,expand=1,fill=BOTH,pady=10,padx=10)


        # Pack it all into the main frame
        f.pack()

        # set up event handling

        #self.analyzerlist.bind('<ButtonRelease-1>',lambda x: self.updateMetadata()
        #self.analyzerlist.bind('<Key>',lambda x: self.updateMetadata())        

        # populate fields and run the gui
        
        self.updateAnalyzer()

        # poll for changes in the list
        self.current = None
        self.poll()
        self.root.mainloop()

    def after(self, wait, func):   # passed time in msecs, function to call.
        # run the function in a new thread, so it won't hang main script
        thread.start_new_thread(self.delay, (wait, func))

    def delay(self, wait, func):
        time.sleep(wait * .001)    # convert msecs into secs and delay this thread
        func()	                          # call the function passed as a parameter
        
    def updateAnalyzer(self):
        """update the list of items in the corpus"""
        for item in self.analyzerliststr:
            self.analyzerlist.insert(END, item)

    def getCorpus(self):        
        """return the list of selected items in the corpus"""
        items = self.analyzerlist.curselection()        
        itemstr = [self.analyzerlist.get(int(item)) for item in items]

        return itemstr
            
    def updateMetadata(self):
        """update the metadata field to reflect the tags from the selected corpus"""                        
        # enable clicking on these
        self.searchbutton.configure(state=NORMAL)
        self.e.configure(state=NORMAL)

        self.resetTokens()
        self.updateTokens()
        
    def updateTokens(self):
        """update the numbers displayed for the documents and terms"""                

        # Perform the search and return the number of terms and documents        

        # Update the GUI
        self.tokentext.configure(state=NORMAL)
        
        self.tokentext.delete(1.0,END)
        self.tokentext.insert(END,"Tokens: ")

        analyzerstr = self.analyzerlist.curselection() # was curselection
        if len(analyzerstr)==0:
            return
        analyzer = self.analyzers[int(analyzerstr[0])]

        self.curlucene.attachCurrentThread()
        
        tokenStream = analyzer.tokenStream("contents", lucene.StringReader(self.e.get()))
        term = tokenStream.addAttribute(lucene.TermAttribute.class_)

        if len(self.e.get())>0:
            while tokenStream.incrementToken():
                self.tokentext.insert(END, "[%s]" %(term.term()))
                

    def resetTokens(self):
        """reset the numbers displayed for the documents and terms"""                
        self.tokentext.configure(state=NORMAL)

        numDocs = 0
        numTerms = 0
        
        self.tokentext.delete(1.0,END)
        self.tokentext.insert(END,"Tokens: ")
                
        self.tokentext.configure(state=DISABLED)

    def poll(self):
        now = self.analyzerlist.curselection()
        if now != self.current:
            self.updateMetadata()            
            self.current = now
        self.after(250, self.poll)
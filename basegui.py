from Tkinter import *
import tkMessageBox
import tkFileDialog
import math
import random
import codecs
import os
import time
import re
from textorganizer.engine import Corpus
import Queue
import lucene

class txtorgui:
    def __init__(self):
        self.root = Tk()
        self.queue = Queue.Queue()
        lucene.initVM()
        self.update()
        self.root.title('txtorg')
        f = Frame(self.root, width=800, height=110)
        lf = Frame(f, relief=GROOVE, borderwidth=2)
        Label(lf, text="Corpus").pack(pady=10,padx=10)

        # Items in the left frame
        self.corpuslist = Listbox(lf, width=40)
        corpusscroll = Scrollbar(lf, command=self.corpuslist.yview)
        self.corpuslist.configure(yscrollcommand=corpusscroll.set)
        self.corpuslist.pack(side=LEFT, fill=Y, expand=True)
        corpusscroll.pack(side=LEFT, fill=Y)
        lf.pack(side=LEFT, fill=BOTH, expand = 1)

        # Items in the center frame
        cf = Frame(f, relief=GROOVE, borderwidth=2)
        Label(cf, text="Metadata").pack(pady=10,padx=10)

        cft = Frame(cf, borderwidth=2)
        cfb = Frame(cf, borderwidth=2)

        self.mdlist = Listbox(cft, height=8, width=15, selectmode=MULTIPLE)
        scroll = Scrollbar(cft, command=self.mdlist.yview)
        self.mdlist.configure(yscrollcommand=scroll.set)
        self.mdlist.pack(side=LEFT,fill=Y,expand=True)
        scroll.pack(side=LEFT,fill=Y)

        self.e = Entry(cfb,state=DISABLED)
        self.e.pack(side=LEFT)

        self.e.delete(0, END)
        self.e.insert(0, "a default value")

        self.searchbutton = Button(cfb, text="Search",state=DISABLED,command=self.runQuery)
        self.searchbutton.pack(side=LEFT, padx=5, pady=8)

        cft.pack()
        cfb.pack()
        cf.pack(side=LEFT, fill=BOTH, expand = 1)

        # Right frame

        rf = Frame(f, relief=GROOVE, borderwidth=2)
        Label(rf, text="Outputs").pack(pady=10,padx=10)
        self.docstext = Text(rf,height=1,width=20)
        self.termstext = Text(rf,height=1,width=20)
        self.exportbutton = Button(rf, text="Export TDM",state=DISABLED,command=self.saveTDM)
        self.docstext.insert(END,"Documents: 0")
        self.termstext.insert(END,"Terms: 0")        

        self.docstext.pack()
        self.termstext.pack()
        self.exportbutton.pack()        
        
        
        rf.pack(side=RIGHT, fill=BOTH, expand = 1)


        # Pack it all into the main frame
        f.pack()

        # set up event handling

        self.corpuslist.bind('<ButtonRelease-1>',lambda x: self.updateMetadata())

        # populate fields and run the gui
        
        self.corpora = []
        self.updateCorpus()


        self.root.mainloop()

    def write(self, data):
        self.queue.put(data)

    def update(self):
        try:
            while True:
                line = self.queue.get_nowait()
                if 'query_results' in line.keys():
                    self.updateCounts(*line['query_results'])
                if 'error' in line.keys():
                    self.show_error(line['error'])
                if 'message' in line.keys():
                    self.show_message(line['message'])

        except Queue.Empty:
            pass

        self.root.after(100, self.update)

    def show_error(self,message):
        tkMessageBox.showerror("Error", message)

    def show_message(self,message):
        tkMessageBox.showinfo("Error", message)

    def updateCorpus(self):
        """update the list of items in the corpus"""
        print "update corpus"
        print os.path.dirname(__file__)
        with codecs.open(os.path.join(os.path.dirname(__file__), "available_indices_gui"), encoding='UTF-8') as inf:
            for line in inf:
                parse_re = re.compile(r'(^.*)\{(.*)\}$')
                if parse_re.search(line) is None: continue
                c = Corpus(self, parse_re.search(line).group(1).strip(), fields = parse_re.search(line).group(2).split(','))
                self.corpora.append(c)
                self.corpuslist.insert(END, c.path)
        if len(self.corpora) == 0:
            self.write({'error': 'Corrupt available_indices_gui file. Please make sure each line has the format "filepath{field1,field2,...}"'})
            
    def getCorpus(self):        
        """return the index of selected items within self.corpora. Not strictly necessary since self.corpora should be in the 
        same order as self.corpuslist, but still a good idea."""

        items = self.corpuslist.curselection()
        selected_corpora = [c for c in range(len(self.corpora)) if self.corpora[c].path in map(lambda x: self.corpuslist.get(int(x)), items)]
        
        # multiple selection shouldn't be possible, but alex set up code to support it?
        assert len(selected_corpora) <= 1
        
        if len(selected_corpora) == 0:
            return None
        elif len(selected_corpora) == 1:
            return selected_corpora[0]
            
    def updateMetadata(self):
        """update the metadata field to reflect the tags from the selected corpus"""                

        self.corpus_idx = self.getCorpus()
        if self.corpus_idx is None:
            return

        self.mdlist.delete(0,END)
        for item in self.corpora[self.corpus_idx].fields:
            self.mdlist.insert(END, item)   
        
        # enable clicking on these
        self.searchbutton.configure(state=NORMAL)
        self.e.configure(state=NORMAL)

        self.updateCounts(0, 0)
        print "leaving update metadata"        
        
    def saveTDM(self):        
        """pop up a dialog to save the TDM"""
        print "saveTDM"                        

        myFormats = [
            ('Comma Separated Variable','*.csv')
            ]

        fileName = tkFileDialog.asksaveasfilename(parent=self.root,filetypes=myFormats ,title="Export the TDM as...")
        if fileName == "" or fileName == ():
            return

        self.corpora[self.corpus_idx].export_TDM(fileName)

    def runQuery(self):
        """runs a query using the run_searcher method of the active Corpus"""
        print "running query"
        self.corpora[self.corpus_idx].run_searcher(self.e.get().strip())


    def updateCounts(self, numDocs, numTerms):
        # Update the GUI
        self.docstext.configure(state=NORMAL)
        self.termstext.configure(state=NORMAL)
        
        self.docstext.delete(1.0,END)
        self.termstext.delete(1.0,END)
        self.docstext.insert(END,"Documents: "+str(int(numDocs)))
        self.termstext.insert(END,"Terms: "+str(int(numTerms)))        
                
        self.docstext.configure(state=DISABLED)
        self.termstext.configure(state=DISABLED)

        if (numDocs>0 and numTerms>0):
            self.exportbutton.configure(state=NORMAL)
        else:
            self.exportbutton.configure(state=DISABLED)
            
        
top = txtorgui()

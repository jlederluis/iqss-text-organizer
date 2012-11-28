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
from functools import partial

class ImportDialog:
    def __init__(self, parent, callback):
        self.parent = parent
        self.callback = callback
        top = self.top = Toplevel(parent)
        self.choice_var = IntVar()
        rb1 = Radiobutton(top, text="Import an entire directory", variable=self.choice_var, value=1)
        rb1.select()
        rb1.pack(anchor=W)
        Radiobutton(top, text="Import from a CSV file (with metadata)", variable=self.choice_var, value=2).pack(anchor=W)
        b = Button(top, text="OK", command=self.ok)
        b.pack(pady=5)

    def ok(self):

        if self.choice_var.get() == 1:
            dir_name = tkFileDialog.askdirectory(parent=self.top ,title="Choose a directory to import...")
            if dir_name == "" or dir_name == ():
                return
            self.callback({'dir': dir_name})
            
        elif self.choice_var.get() == 2:
            file_name =  tkFileDialog.askopenfilename(parent=self.parent.root ,title="Choose a CSV file containing filepaths and metadata...")
            if file_name == "" or file_name == ():
                return
            self.callback({'file': file_name})

        self.top.destroy()
        

class EntryDialog:
    def __init__(self, parent, callback, label="Enter a value:"):
        self.callback = callback
        top = self.top = Toplevel(parent)
        Label(top, text=label).pack()
        self.e = Entry(top)
        self.e.pack(padx=5)
        b = Button(top, text="OK", command=self.ok)
        b.pack(pady=5)

    def ok(self):
        self.callback(self.e.get())
        self.top.destroy()

class txtorgui:
    def __init__(self):
        self.root = Tk()
        self.queue = Queue.Queue()
        lucene.initVM()
        self.update()
        self.root.title('Text Organizer')
        f = Frame(self.root, width=800, height=110)
        lf = Frame(f, relief=GROOVE, borderwidth=2)
        Label(lf, text="Corpus").pack(pady=10,padx=10)

        # Top level Menu bar
        self.menubar = Menu(f)
        menu = Menu(self.menubar, tearoff=0)
        

        self.menubar.add_cascade(label="File", menu=menu)
        menu.add_command(label="New Corpus", command=self.new_corpus_btn_click)
        menu.add_command(label="Open Corpus", command=self.open_corpus)

        menu_c = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Corpus", menu=menu_c)
        menu_c.add_command(label="Import Documents...", command=self.import_btn_click)

        f.master.config(menu=self.menubar)
        # Items in the left frame
        self.corpuslist = Listbox(lf, width=40,exportselection=False)
        corpusscroll = Scrollbar(lf, command=self.corpuslist.yview)
        self.corpuslist.configure(yscrollcommand=corpusscroll.set)
        self.corpuslist.pack(side=LEFT, fill=BOTH, expand=True)
        corpusscroll.pack(side=LEFT, fill=Y)
        lf.pack(side=LEFT, fill=BOTH, expand = 1,padx=10,pady=10)

        # Items in the center frame
        cf = Frame(f, relief=GROOVE, borderwidth=2)
        Label(cf, text="Metadata").pack(pady=10,padx=10)

        cft = Frame(cf, borderwidth=2)
        cfb = Frame(cf, borderwidth=2)

        self.mdlist = Listbox(cft, height=8, width=15, selectmode=MULTIPLE, exportselection=False)
        scroll = Scrollbar(cft, command=self.mdlist.yview)
        self.mdlist.configure(yscrollcommand=scroll.set)
        self.mdlist.pack(side=LEFT,fill=BOTH,expand=True)
        scroll.pack(side=LEFT,fill=Y)

        self.e = Entry(cfb,state=DISABLED)
        self.e.pack(side=LEFT,fill=X,expand=1)

        self.e.delete(0, END)
        self.e.insert(0, "a default value")

        self.searchbutton = Button(cfb, text="Search",state=DISABLED,command=self.runQuery)
        self.searchbutton.pack(side=LEFT, padx=5, pady=8)

        cft.pack(fill=BOTH, expand = 1)
        cfb.pack(fill=X)
        cf.pack(side=LEFT, fill=BOTH, expand = 1,pady=10,padx=10)

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
        
        
        rf.pack(side=RIGHT, fill=BOTH, expand = 1,pady=10,padx=10)


        # Pack it all into the main frame
        f.pack(fill=BOTH,expand=1)

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

    def new_corpus_btn_click(self):

        dir_name = tkFileDialog.askdirectory(parent=self.root ,title="Choose a directory in which to save the Corpus...")
        if dir_name == "" or dir_name == ():
            return

        d = EntryDialog(self.root, partial(self.make_new_corpus, dir_name), label="Please choose a name for the index")
        self.root.wait_window(d.top)

    def make_new_corpus(self,  dir_name, corpus_name):
        # strip all non-alphanumeric characters from the corpus name
        good_corpus_name = "".join([c for c in corpus_name if c.isalnum()])
        if good_corpus_name == "": return

        new_index_path = os.path.join(dir_name, good_corpus_name)
        with codecs.open(os.path.join(os.path.dirname(__file__), "available_indices_gui"), 'a', encoding='UTF-8') as outf:
            outf.write(new_index_path+"{}\n")
        self.updateCorpus()

    def import_btn_click(self):
        d = ImportDialog(self.root, self.import_files)
        self.root.wait_window(d.top)

    def import_files(self, args_dir):
        self.corpora[self.corpus_idx].import_directory(args_dir['dir'])
        print "done!"

    def open_corpus(self):
        pass

    def updateCorpus(self):
        """update the list of items in the corpus"""
        print "update corpus list"
        self.corpora = []
        self.corpuslist.delete(0, END)
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

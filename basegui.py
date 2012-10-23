from Tkinter import *
import tkFileDialog
import math,random

class txtorgui:
    def __init__(self):
        self.root = Tk()
        self.root.title('txtorg')
        f = Frame(self.root, width=800, height=110)
        lf = Frame(f, relief=GROOVE, borderwidth=2)
        Label(lf, text="Corpus").pack(pady=10,padx=10)

        # Items in the left frame
        self.corpuslist = Listbox(lf, height=6, width=15)
        corpusscroll = Scrollbar(lf, command=self.corpuslist.yview)
        self.corpuslist.configure(yscrollcommand=corpusscroll.set)
        self.corpuslist.pack(side=LEFT)
        corpusscroll.pack(side=LEFT, fill=Y)
        lf.pack(side=LEFT)

        # Items in the center frame
        cf = Frame(f, relief=GROOVE, borderwidth=2)
        Label(cf, text="Metadata").pack(pady=10,padx=10)

        cft = Frame(cf, borderwidth=2)
        cfb = Frame(cf, borderwidth=2)

        self.mdlist = Listbox(cft, height=6, width=15, selectmode=MULTIPLE)
        scroll = Scrollbar(cft, command=self.mdlist.yview)
        self.mdlist.configure(yscrollcommand=scroll.set)
        self.mdlist.pack(side=LEFT,fill=Y)
        scroll.pack(side=LEFT,fill=Y)

        self.e = Entry(cfb,state=DISABLED)
        self.e.pack(side=LEFT)

        self.e.delete(0, END)
        self.e.insert(0, "a default value")

        self.searchbutton = Button(cfb, text="Search",state=DISABLED,command=self.updateCounts)
        self.searchbutton.pack(side=LEFT, padx=5, pady=8)

        cft.pack()
        cfb.pack()
        cf.pack(side=LEFT)

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
        
        
        rf.pack(side=RIGHT)


        # Pack it all into the main frame
        f.pack()

        # set up event handling

        self.corpuslist.bind('<ButtonRelease-1>',lambda x: self.updateMetadata())

        # populate fields and run the gui
        
        self.updateCorpus()


        self.root.mainloop()

    def updateCorpus(self):
        """update the list of items in the corpus"""
        print "update corpus"                
        for item in range(30):
            self.corpuslist.insert(END, item)

    def getCorpus(self):        
        """return the list of selected items in the corpus"""
        print "get corpus"        
        items = self.corpuslist.curselection()        
        print "getCorpus: selected ",items
        itemstr = [self.corpuslist.get(int(item)) for item in items]

        return itemstr
            
    def updateMetadata(self):
        """update the metadata field to reflect the tags from the selected corpus"""                
        print "update metadata"
        itemstr = self.getCorpus()
        print itemstr
        if len(itemstr)==0:
            return
        self.mdlist.delete(0,END)        

        # put elements in the list
        
        itemint = int(itemstr[0])

        if itemint/2:
            for item in ["articles","editorials","national","local","international"]:
                self.mdlist.insert(END, item)
        else:
            for item in ["dog","cat","fish","eel","gnu","fox","hamster"]:
                self.mdlist.insert(END, item)        
        
        # enable clicking on these
        self.searchbutton.configure(state=NORMAL)
        self.e.configure(state=NORMAL)

        self.resetCounts()
        print "leaving update metadata"        
        
    def saveTDM(self):        
        """pop up a dialog to save the TDM"""
        print "saveTDM"                        

        myFormats = [
            ('Comma Separated Variable','*.csv')
            ]

        fileName = tkFileDialog.asksaveasfilename(parent=self.root,filetypes=myFormats ,title="Export the TDM as...")

        # Actually save the TDM using the file name.

    def updateCounts(self):
        """update the numbers displayed for the documents and terms"""                
        print "update counts"

        # Perform the search and return the number of terms and documents
        numDocs = math.floor(random.uniform(100,100000))
        numTerms = math.floor(numDocs*random.uniform(2,25))


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

    def resetCounts(self):
        """reset the numbers displayed for the documents and terms"""                
        print "reset counts"                        
        self.docstext.configure(state=NORMAL)
        self.termstext.configure(state=NORMAL)

        numDocs = 0
        numTerms = 0
        
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

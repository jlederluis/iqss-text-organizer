Using txtorg on the RCE
=======================

Begin by logging on to the RCE virtual machine that has pylucene installed.  When you log in, make sure that you enable X-forwarding:

`ssh -X username@rce-2013-alpha-vm1.hmdc.harvard.edu`

Then, clone this very git repository by typing:

`git clone https://github.com/sbrother/iqss-text-organizer.git`

This should make a directory called `iqss-text-organizer`.

Now, run the install script, but specifying that it should be installed only for this user:

`python iqss-text-organizer/setup.py install --user`

In the `iqss-text-organizer/bin` directory there is an executable called `txtorg`.  You can execute this as follows:

`./iqss-text-organizer/bin/txtorg`

If you have X-forwarding enabled, a new window should pop up with the txtorg GUI.

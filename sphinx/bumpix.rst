.. $Id$
.. pyformex documentation --- install

.. include:: defines.inc
.. include:: ../website/src/links.inc

.. _cha:bumpix:

************************
BuMPix Live Linux system
************************

.. topic:: Abstract

   This document gives a short introduction on the BuMPix Live Linux
   system and how to use it to run pyFormex directly on nearly any
   computer system without having to install it.

.. _sec:bumpix-live-linux:

What is BuMPix
==============

`Bumpix Live` is a fully featured Linux system including pyFormex that
can be run from a single removable medium such as a CD or a USB key.
BuMPix is still an experimental project, but new versions are already
produced at regular intervals. While those are primarily intended for
our students, the install images are made available for download on
the `Bumpix Live Linux`_ FTP server, so that anyone can use them.


All you need to use the `Bumpix Live Linux`_ is some proper PC
hardware: the system boots and runs from the removable medium and
leaves everything that is installed on the hard disk of the computer
untouched.


Because the size of the image (since version 0.4) exceeds that of a CD, 
we no longer produce CD-images (.iso) by default, but some older
images remain avaliable on the server. New (reduced) CD
images will only be created on request.
On the other hand, USB-sticks of 2GB and larger have become very
affordable and most computers nowadays can boot from a USB stick.
USB sticks are also far more easy to work with than CD's: you can
create a persistent partition where you can save your changes, while a CD can not be changed.

You can easily take your USB stick with you wherever you go, plug it into any
available computer, and start or continue your previous pyFormex work.
Some users even prefer this way to run pyFormex for that single reason.
The Live system is also an excellent way to test and see what pyFormex can
do for you, without having to install it. Or to demonstrate pyFormex to
your friends or colleagues. 


.. _sec:obtain_bumpix:

Obtain a BuMPix Live bootable medium
====================================

Download BuMPix
---------------
The numbering scheme of the
BuMPix images is independent from the pyFormex numbering. Just pick
the `latest BuMPix image`_ to get the most recent pyFormex available
on USB stick. After you downloaded the .img file, write it to a USB
stick as an image, not as file! Below, you find instructions on how to do
this on a Linux system or on a Windows platform.

.. warning:: Make sure you've got the device designation correct, or
   you might end up overwriting your whole hard disk! 

Also, be aware that the
USB stick will no longer be usable to store your files under Windows.

Create the BuMPix USB stick under Linux
---------------------------------------

If you have an existing Linux system available, you can write the 
downloaded image to the USB-stick using the command::

  dd if=bumpix-VERSION.img of=USBDEV

where ``bumpix-VERSION.img`` is the downloaded file and USBDEV
is the device corresponding to your USB key. This should be
``/dev/sda`` or ``/dev/sdb`` or, generally, ``/dev/sd?`` where ``?``
is a single character from ``a-z``. The value you should use depends
on your hardware. You can find out the correct value by giving the command ``dmesg``
after you have plugged in the USB key. You will see messages mentioning the
correct ``[sd?]`` device.

The ``dd`` command above will overwrite everything on the specified device,
so copy your files off the stick before you start, and make sure you've got the device designation correct.


Create the BuMPix USB stick under Windows
-----------------------------------------

If you have no Linux machine available to create the USB key, there
are ways to do this under Windows as well. 
We recommend to use `dd for Windows`_. You can then proceed as follows. 

* Download `dd for Windows`_ to a folder, say ``C:\\download\ddWrite``.

* Download the `latest BuMPix image`_ to the same folder.

* Mount the target USB stick and look for the number of the mounted
  USB. This can be done with the command ``c:\\download\ddWrite dd --list``.
  Look at the description (Removable media) and the size to make sure
  you've got the correct harddisk designation (e.g. ``harddisk1``).

* Write the image to the USB stick with the command, substituting the
  harddisk designation found above::

   dd if=c:\download\ddwrite\bumpix-0.4-b1.img of=\\?\device\harddisk1\partition0 bs=1M --progress

The ``dd`` command above will overwrite everything on the specified device,
so copy your files off the stick before you start, and make sure you've got the device designation correct.


Buy a USB stick with BuMPix 
--------------------------- 

Alternatively,

* if you do not succeed in properly writing the image to a USB key, or
* if you just want an easy solution without any install troubles, or
* if you want to financially support the further development of pyFormex, or
* if you need a large number of pyFormex USB installations,

you may be happy to know that we can provide ready-made BuMPix USB
sticks with the ``pyformex.org`` logo at a cost hardly exceeding that
of production and distribution.
If you think this is the right choice for you, just `email us`_ for a quotation.

.. image:: ../website/images/pyformex_ufd.jpg
   :align: center
   :alt: pyFormex USB stick with BuMPix Live Linux


.. _sec:boot_bumpix:

Boot your BuMPix system
=======================
Once the image has been written, reboot your computer from the USB
stick. You may have to change your BIOS settings or use the boot menu
to do that. On success, you will have a full Linux system running,
containing pyFormex ready to use. There is even a start button in the 
toolbar at the bottom.

.. warning:: More detailed documentation on how to use the system is
   currently under preparation. For now, feel free to `email us`_ if
   you have any problems or urgent questions.
  

.. End
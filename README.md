Timeline
========

Timeline is a quick proof-of-concept of a WRMS activity timeline. A few features
are Catalyst specific.

Start the application by running

    python web.py


And then visit the local URL when it's presented to you.


Screenshot!
-----------

![Screenshot](http://i.imgur.com/JKiK3LF.png)


Installation
------------

Timeline requires the following Python libraries:

    requests
    bottle

Install using easy_install like so:

    sudo easy_install requests bottle

For profile images to work you also need to be able to access
http://directory.wgtn.cat-it.co.nz/


Config
------

A config file is required to supply authentication credentials.
Create a file named config.py in the same directory as web.py

Here is an example config file. Replace capitilised variables with
your own data.

    secret = 'WRMS3_SECRET_HASH'
    userid = MY_WRMS_USERID


To retrieve your WRMS3_SECRET_HASH, visit a WRMS3 report and grab the
hash contained in the 'wrms3_auth' cookie.


License
=======

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

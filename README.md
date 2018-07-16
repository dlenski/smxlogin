smxlogin
========

This is a helper script to allow you to automatically login to a Juniper VPN
that uses a [SecureMatrix](http://cse-america.com/smx/solutions.htm)
"password image pattern."

This mess:

![SMX image pattern illustration](http://cse-america.com/my_images/page__howitworks/fig03-smx.png)

Many Japanese companies use SecureMatrix logins for their VPNs. (Entry
points, such as [Mitsubishi's](https://ssl-vpn.mitsubishicorp.com/smx_sll/am),
can easily be found with a Google search.)

How to install
==============

Use [Python 3's `pip` tool](https://docs.python.org/3/installing/):

```sh
$ pip3 install git+https://github.com/dlenski/smxlogin
```

How to use
==========

Specify the login URL, and optionally your username and the
pattern of digits to pick from the random matrix.

This script will navigate the web login forms and return the `HOST`
and `COOKIE` variables in a form that can be used by
[OpenConnect](http://www.infradead.org/openconnect/juniper.html)
(equivalent to the output of `openconnect --authenticate`):

```sh
$ eval $( smxlogin.py -v -u myusername -p a1b2c3d4 https://vpn.company.com/login/matrix )
Opening login page: https://vpn.company.com/login/matrix ...
Submitting username...
Assembled password from matrix.
Submitting password...
Final form submission, expecting to get DSID cookie...

$ echo $COOKIE; echo $HOST
DSID=f65a1f512af81dd1970d96ae07c73bf6
juniper.company.com

$ openconnect --protocol=nc --cookie "$COOKIE" "$HOST"
```

With the `--password` option, it will simply output the password assembled
from the matrix — and it won't attempt to login to a Juniper VPN and fetch
the VPN authentication cookie:

```sh
$ password=$( smxlogin.py -v --password -u myusername -p a1b2c3d4 https://vpn.company.com/login/matrix )
Opening login page: https://vpn.company.com/login/matrix ...
Submitting username...
Assembled password from matrix.

$ echo $password
3497
```

How to enter your login pattern
===============================

The SecureMatrix login page displays a randomly generated array of digits (either 4-row × 12-column or 4-row × 16-column, in my experience):

      abcd efgh ijkl mnop
      -------------------
    1|3898 9695 5662 1221
    2|6024 0941 8504 9113
    3|7413 0557 1441 4467
    4|2360 0896 2467 3441

Your pattern password can be described as a series of [chessboard coordinates](https://en.wikipedia.org/wiki/Algebraic_notation_(chess)) for the digits to select from the matrix.
For example, suppose your password selects 4 locations from the pattern above, as follows:

      abcd efgh ijkl mnop
      -------------------
    1|   8
    2|            0
    3|                 6
    4|2

      a4 -> d1 -> k2 -> o3

In this case, you can use `smxlogin --pattern a4d1k2o3` to automatically enter your pattern.

TODO
====

* Add support for non-Juniper VPNs (if any of them use smxlogin?)
* Some (newer?) versions of the SecureMatrix login obfuscate the submitted password through encryption.
  It would be good to be able to detect when this obfuscation is in use, and thereby avoid submitting an incorrect
  password.

License
=======

GPLv3 or newer

#!/usr/bin/env python3

# What this is
# ============
#
# This is a helper script to allow you to login to a Juniper VPN
# that uses a SecureMatrix (http://cse-america.com/smx/solutions.htm)
# "password image pattern".
#
# You specify the login URL, and optionally your username and the
# pattern of digits to pick from the random matrix. This script will
# navigate the web login forms and return the HOST and COOKIE
# variables in a form that can be used by OpenConnect:
#
#   $ eval `smxlogin.py https://vpn.company.com/login/matrix`
#   $ openconnect --cookie "$COOKIE" "$HOST"
#
#
# How to enter your pattern
# =========================
#
#    The matrix is a randomly generated array of digits,
#    either 4-row X 12-column or 4-row X 16-column:
#
#        abcd efgh ijkl mnop
#        -------------------
#      1|3898 9695 5662 1221
#      2|6024 0941 8504 9113
#      3|7413 0557 1441 4467
#      4|2360 0896 2467 3441
#
#    The pattern consists of chessboard coordinates of the digits to
#    select from the matrix, e.g.:
#
#         a4 d1 k2 o3
#      -> smxlogin --pattern a4d1k2o3
#
#    Combining the above examples into a 4-digit password yields 2806:
#
#        abcd efgh ijkl mnop
#        -------------------
#      1|   8
#      2|            0
#      3|                 6
#      4|2
#

from sys import stderr
from getpass import getpass
import robobrowser, re, argparse

def patternize(s):
    s = s.replace(' ','')
    p = [(int(y,10)-1, ord(x.lower())-ord('a')) for x,y in zip(s[::2], s[1::2])]
    return p

def reassemble(matrix, pattern):
    matrix = [row.replace(' ','') for row in matrix]
    assert all(len(r)==len(matrix[0]) for r in matrix)
    return ''.join(matrix[y][x] for y,x in pattern)

p = argparse.ArgumentParser()
p.add_argument('login_url', help='SecureMatrix login URL')
p.add_argument('-u','--user', help='Username')
p.add_argument('-p','--pattern', type=patternize, help='Pattern to enter (series of chessboard coordinates to choose from the matrix)')
p.add_argument('-P','--proxy', help='HTTPS proxy (in any format accepted by python-requests, e.g. socks5://localhost:8080)')
p.add_argument('-v','--verbose', action='count')
args = p.parse_args()

################################################################################

# open login page as Juniper NC user-agent
br=robobrowser.RoboBrowser(user_agent='ncsvc', parser='html.parser')
br.session.headers['Accept-Language']='en'
br.session.proxies['https']=args.proxy
if args.verbose:
    print("Opening login page: %s ..." % args.login_url, file=stderr)
br.open(args.login_url)

# fill in username form
f = br.get_form(0)
assert f['PROC'].value=='doChallengeCode'
username = args.user or input('Username: ')
f['REPORT']=username
if args.verbose:
    print("Submitting username...", file=stderr)
br.submit_form(f)

# parse matrix and assemble password from pattern
f = br.get_form('SMX_FORM')
assert f['PROC'].value=='doPasswordCheck'
matrix = re.findall('(?:\d{4} )+', str(br.find('center')))
if args.pattern:
    password = reassemble(matrix, args.pattern)
    if args.verbose>1:
        print('Matrix:\n  %s\n=> Assembled password: %s' % ('\n  '.join(matrix), password), file=stderr)
    elif args.verbose:
        print("Assembled password from matrix.", file=stderr)
else:
    print("Matrix:\n  %s" % '\n  '.join(matrix), file=stderr)
    password = getpass('Password: ')
f['PASSWORD'] = password
if args.verbose:
    print("Submitting password...", file=stderr)
br.submit_form(f)

# final step
f = br.get_form('SMX_FORM')
assert f['username'].value==username
assert f['password'].value==password
if args.verbose:
    print("Final form submission, expecting to get DSID cookie...", file=stderr)
br.submit_form(f)

# output the cookie and destination URL
assert 'DSID' in br.session.cookies
print("COOKIE='DSID=%s'" % br.session.cookies['DSID'])
print("HOST='%s'" % br.url)

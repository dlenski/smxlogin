#!/usr/bin/env python3

from sys import stderr
from getpass import getpass
import robobrowser, re, argparse
from urllib.parse import urlparse
from .version import __version__

def patternize(s):
    s = s.replace(' ','')
    p = [(int(y,10)-1, ord(x.lower())-ord('a')) for x,y in zip(s[::2], s[1::2])]
    return p

def reassemble(matrix, pattern):
    matrix = [row.replace(' ','') for row in matrix]
    assert all(len(r)==len(matrix[0]) for r in matrix)
    return ''.join(matrix[y][x] for y,x in pattern)

def parse_args(args=None):
    p = argparse.ArgumentParser()
    p.version=__version__
    p.add_argument('login_url', help='SecureMatrix login URL')
    p.add_argument('-u','--user', help='Username')
    p.add_argument('-p','--pattern', type=patternize, help='Pattern to enter (series of chessboard coordinates to choose from the matrix)')
    p.add_argument('-P','--password', action='store_true', help='Just output the password and exit, instead of continuing and outputting the DSID cookie')
    p.add_argument('-v','--verbose', default=0, action='count')
    p.add_argument('--version', action='version')
    g = p.add_argument_group('Advanced')
    g.add_argument('--proxy', help='HTTPS proxy (in any format accepted by python-requests, e.g. socks5://localhost:8080)')
    x = g.add_mutually_exclusive_group()
    x.add_argument('-k','--insecure', dest='verify', default=True, action='store_false', help="Don't verify peer's SSL certificate")
    x.add_argument('--cacert', dest='verify', help='Path to CA bundle file or directory (in OpenSSL format)')
    args = p.parse_args(args)
    return p, args

def main(args=None):
    p, args = parse_args(args)

    # open login page as Juniper NC user-agent
    br=robobrowser.RoboBrowser(user_agent='ncsvc', parser='html.parser')
    br.session.headers['Accept-Language']='en'
    br.session.proxies['https']=args.proxy
    br.session.verify=args.verify
    if args.verbose:
        print("Opening login page: %s ..." % args.login_url, file=stderr)
    br.open(args.login_url)

    # fill in username form
    f = br.get_form(0)
    check_form = (f and 'PROC' in f.fields and f['PROC'].value=='doChallengeCode')
    if args.verbose>1 or not check_form:
        print("Username form:\n%s" % br.parsed, file=stderr)
    if not check_form:
        raise SystemExit("ERROR: Did not receive expected username form.")
    username = args.user or input('Username: ')
    f['REPORT']=username
    if args.verbose:
        print("Submitting username...", file=stderr)
    br.submit_form(f)

    # parse matrix and assemble password from pattern
    while True:
        f = br.get_form('SMX_FORM')
        check_form = (f and 'PROC' in f.fields and f['PROC'].value=='doPasswordCheck')
        if args.verbose>1 or not check_form:
            print("Matrix password form:\n%s" % br.parsed, file=stderr)
        if not check_form:
            raise SystemExit("ERROR: Did not receive expected matrix password form.")
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
        if args.password:
            print(password)
            return

        f['PASSWORD'] = password
        if args.verbose:
            print("Submitting password...", file=stderr)
        br.submit_form(f)

        f = br.get_form('SMX_FORM')
        if f and 'PROC' in f.fields and f['PROC'].value=='doPasswordCheck':
            if args.verbose>1 or not check_form:
                print("Unexpected form:\n%s" % br.parsed, file=stderr)
            if args.pattern:
                raise SystemExit("ERROR: Incorrect password entered. Check pattern.")
            else:
                print("ERROR: Incorrect password entered. Try again.")
                continue
        else:
            break

    # final step
    check_form = (f and 'username' in f.fields and 'password' in f.fields
                  and f['username'].value==username and f['password'].value==password)
    if args.verbose>1 or not check_form:
        print("Final form:\n%s" % br.parsed, file=stderr)
    if not check_form:
        raise SystemExit("ERROR: Did not receive expected final form.")
    if args.verbose:
        print("Final form submission, expecting to get DSID cookie...", file=stderr)
    br.submit_form(f)

    # output the cookie and destination URL
    if 'DSID' not in br.session.cookies:
        raise SystemExit("ERROR: Did not receive expected DSID cookie.")
    print("COOKIE='DSID=%s'" % br.session.cookies['DSID'])
    print("HOST='%s'" % urlparse(br.url).netloc)

################################################################################

if __name__=='__main__':
    main()

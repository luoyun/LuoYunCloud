from hashlib import md5, sha512, sha1
import crypt, random, time


def _encrypt_password(salt, raw_password):
    hsh = sha512(salt + raw_password).hexdigest()
    return hsh


def enc_login_passwd( plaintext ):
    salt = md5(str(random.random())).hexdigest()[:12]
    hsh = _encrypt_password(salt, plaintext)
    enc_password = "%s$%s" % (salt, hsh)

    return enc_password


def check_login_passwd(raw_password, enc_password):
    try:
        salt, hsh = enc_password.split('$')
    except:
        return False
    return hsh == _encrypt_password(salt, raw_password)


def enc_shadow_passwd( plaintext ):

    # get shadow passwd

    salt = crypt.crypt( str(random.random()), str(time.time()) )[:8]
    s = '$'.join( ['','6', salt,''] )
    password = crypt.crypt( plaintext, s )

    return password


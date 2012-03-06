/*
** Copyright (C) 2012 LuoYun Co. 
**
**           Authors:
**                    lijian.gnu@gmail.com 
**                    zengdongwu@hotmail.com
**  
** This program is free software; you can redistribute it and/or modify
** it under the terms of the GNU General Public License as published by
** the Free Software Foundation; either version 2 of the License, or
** (at your option) any later version.
**  
** This program is distributed in the hope that it will be useful,
** but WITHOUT ANY WARRANTY; without even the implied warranty of
** MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
** GNU General Public License for more details.
**  
** You should have received a copy of the GNU General Public License
** along with this program; if not, write to the Free Software
** Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
**  
*/
#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <gcrypt.h>
#include "lyutil.h"
#include "lyauth.h"

int lyauth_encrypt(char * secret, char * out, int outlen, char * in, int inlen)
{
    gcry_error_t e;
    gcry_cipher_hd_t hd;
    int algo = GCRY_CIPHER_ARCFOUR;
    int mode = GCRY_CIPHER_MODE_STREAM;
    int flags = 0;
    e = gcry_cipher_open(&hd, algo, mode, flags);
    if (e)
        return LY_GCRYPT_ERR_OPEN;

    e = gcry_cipher_setkey(hd, secret, strlen(secret));
    if (e)
        return LY_GCRYPT_ERR_KEY;

    e = gcry_cipher_encrypt(hd, out, outlen, in, inlen); 
    if (e)
        return LY_GCRYPT_ERR_ENCRYPT;

    gcry_cipher_close(hd);

    return 0;
}

int lyauth_decrypt(char * secret, char * out, int outlen, char * in, int inlen)
{
    gcry_error_t e;
    gcry_cipher_hd_t hd;
    int algo = GCRY_CIPHER_ARCFOUR;
    int mode = GCRY_CIPHER_MODE_STREAM;
    int flags = 0;
    e = gcry_cipher_open(&hd, algo, mode, flags);
    if (e) 
        return LY_GCRYPT_ERR_OPEN;

    e = gcry_cipher_setkey(hd, secret, strlen(secret));
    if (e) 
        return LY_GCRYPT_ERR_KEY;

    e = gcry_cipher_decrypt(hd, out, outlen, in, inlen);
    if (e) 
        return LY_GCRYPT_ERR_DECRYPT;

    gcry_cipher_close(hd);

    return 0;
}

int lyauth_init(void)
{
    if (!gcry_check_version(GCRYPT_VERSION))
        return LY_GCRYPT_ERR_INIT;

    /* Disable secure memory.  */
    gcry_control(GCRYCTL_DISABLE_SECMEM, 0);

    /* Tell Libgcrypt that initialization has completed. */
    gcry_control(GCRYCTL_INITIALIZATION_FINISHED, 0);

    return 0;
}

/* use uuid as random secret key */
char * lyauth_secret(void)
{
    return lyutil_uuid(NULL, 0);
}

/* use uuid as a random string for challenge request */
int lyauth_prepare(AuthConfig * ac)
{
    if (ac == NULL)
        return -1;
    if (ac->challenge)
        free(ac->challenge);
    ac->challenge = lyutil_uuid(NULL, 0);
    if (ac->challenge == NULL)
        return -1;
    return 0;
}

/*
** When return, data contains encrypted data
*/
int lyauth_answer(AuthConfig * ac, void * data, int data_len)
{
    if (ac == NULL || data == NULL || data_len <= 0)
        return -1;
    if (ac->secret &&
        lyauth_encrypt(ac->secret, data, data_len, NULL, 0) < 0) {
        return -1;
    }
    return 0;
}

/*
** Return: -1, error
**          0, verification failed
**          1, verification succeeded
**
** When return, data contains decrypted data
*/
int lyauth_verify(AuthConfig * ac, void * data, int data_len)
{
    if (ac == NULL || ac->challenge == NULL || data == NULL || data_len <= 0)
        return -1;
    if (ac->secret && 
        lyauth_decrypt(ac->secret, data, data_len, NULL, 0) < 0) {
        return -1; 
    }
    if (strcasecmp(ac->challenge, (char *)data) == 0)
        return 1;
    return 0;
}

/* free AuthConfig struct */
void lyauth_free(AuthConfig * ac)
{
    if (ac == NULL)
        return;
    if (ac->secret) {
        free(ac->secret);
        ac->secret = NULL;
    }
    if (ac->challenge) {
        free(ac->challenge);
        ac->challenge = NULL;
    }
    return;
}

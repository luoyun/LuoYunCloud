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
#ifndef __LY_INCLUDE_OSMANAGER_LYAUTH_H
#define __LY_INCLUDE_OSMANAGER_LYAUTH_H

/*
** encryption/decryption with libgcrypt
*/
#define LY_GCRYPT_ERR_INIT  -1
#define LY_GCRYPT_ERR_OPEN  -2
#define LY_GCRYPT_ERR_KEY   -3
#define LY_GCRYPT_ERR_ENCRYPT   -4
#define LY_GCRYPT_ERR_DECRYPT   -5
int lyauth_encrypt(char * secret, char * out, int outlen, char * in, int inlen);
int lyauth_decrypt(char * secret, char * out, int outlen, char * in, int inlen);
int lyauth_init(void);

/* a secret string */
char * lyauth_secret(void);

/* authtication struct */
typedef struct AuthConfig_t {
    char * secret;
    char * challenge;
} AuthConfig;

/* prepare/verifiy authentication */
int lyauth_prepare(AuthConfig * ac);
int lyauth_verify(AuthConfig * ac, void * data, int data_len);
int lyauth_answer(AuthConfig * ac, void * data, int data_len);
void lyauth_free(AuthConfig * ac);

#endif

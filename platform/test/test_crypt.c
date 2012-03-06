#include <stdio.h>
#include <gcrypt.h>

char * message = "hello";
char encrypted[100];
const char * secret = "a1afe1fb56194ad8bcf316c30c79e4f3";

int encrypt(void)
{
    gcry_error_t e;
    gcry_cipher_hd_t hd;
    int algo = GCRY_CIPHER_ARCFOUR;
    int mode = GCRY_CIPHER_MODE_STREAM;
    int flags = 0;
    e = gcry_cipher_open(&hd, algo, mode, flags);
    if (e) {
        perror("open");
        return 0;
    }

    int l = strlen(secret);
    e = gcry_cipher_setkey(hd, secret, l);
    if (e) {
        perror("setkey");
        return 0;
    }

    bzero(encrypted, 100);
    e = gcry_cipher_encrypt(hd, encrypted, 100, message, strlen(message));
    if (e) {
        perror("encrypt");
        return 0;
    }

    printf("encrypted message\n");
    int i;
    for (i=0; i<strlen(message); i++)
        printf("%02x ", (unsigned char)encrypted[i]);
    printf("\n");
    encrypted[i] = 0;

    gcry_cipher_close(hd);

    return 0;
}

int decrypt()
{
    gcry_error_t e;
    gcry_cipher_hd_t hd;
    int algo = GCRY_CIPHER_ARCFOUR;
    int mode = GCRY_CIPHER_MODE_STREAM;
    int flags = 0;
    e = gcry_cipher_open(&hd, algo, mode, flags);
    if (e) {
        perror("open");
        return 0;
    }

    int l = strlen(secret);
    e = gcry_cipher_setkey(hd, secret, l);
    if (e) {
        perror("setkey");
        return 0;
    }

    char o2[100];
    e = gcry_cipher_decrypt(hd, o2, 100, encrypted, 100);
    if (e) {
        perror("decrypt");
        return 0;
    }
    printf("decrypted message\n");
    printf("%x %x %x %x %x\n", o2[0], o2[1], o2[2], o2[3], o2[4]);
    o2[strlen(message)] = 0;
    printf("%s\n", o2);
    if (strcmp(message, o2) == 0)
        printf("test passed\n");

    gcry_cipher_close(hd);
    return 0;
}

int main(void)
{
    /* Version check should be the very first call because it
       makes sure that important subsystems are intialized. */
    if (!gcry_check_version(GCRYPT_VERSION)) {
        fputs("libgcrypt version mismatch\n", stderr);
        exit(2);
    }

    /* Disable secure memory.  */
    gcry_control(GCRYCTL_DISABLE_SECMEM, 0);

    /* ... If required, other initialization goes here.  */

    /* Tell Libgcrypt that initialization has completed. */
    gcry_control(GCRYCTL_INITIALIZATION_FINISHED, 0);

    encrypt();
    decrypt();
    return 0;
}

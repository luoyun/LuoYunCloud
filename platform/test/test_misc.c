#include <stdio.h>
#include <uuid/uuid.h>

void generate_uuid()
{
    char c[40];
    uuid_t u;
    uuid_generate(u);
    uuid_unparse(u, c);
    printf("%s\n", c);
}

int main(void)
{
    generate_uuid();
    return 0;
}

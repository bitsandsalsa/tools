#include <stdio.h>
#include <libgen.h>
#include <sys/mman.h>

void usage(char* prog)
{
    printf("USAGE: %s <raw_bin_file>\n", basename(prog));
    printf("Execute a raw binary file.\n");
    printf("\n");
}

int main(int argc, char* argv[])
{
    if (argc != 2) {
        usage(argv[0]);
        return 1;
    }

    FILE* fp = fopen(argv[1], "rb");
    if (!fp) {
        perror("fopen");
        return 1;
    }

    if (fseek(fp, 0, SEEK_END)) {
        perror("fseek");
    }

    int file_size = ftell(fp);
    if (!file_size) {
        fprintf(stderr, "[!] Empty file\n");
        return 1;
    }
    if (file_size < 0) {
        perror("ftell");
        return 1;
    }

    void* buf_ptr = mmap(
        NULL,
        file_size,
        PROT_READ | PROT_EXEC,
        MAP_PRIVATE,
        fileno(fp),
        0);
    if (MAP_FAILED == buf_ptr) {
        perror("mmap");
        return 1;
    }
    fclose(fp);

    void (*buf)(void) = buf_ptr;
    buf();
    // probably won't come back here

    return 0;
}

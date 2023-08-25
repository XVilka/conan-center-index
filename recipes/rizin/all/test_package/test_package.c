#include <stdio.h>
#include <rz_core.h>

int main(void) {
	RzCore *core = rz_core_new();
	rz_cons_printf("Conan Package Manager\n");
	rz_cons_flush();

    printf("RIZIN VERSION: %s\n", rz_version_str(NULL));

	rz_core_free(core);
    return EXIT_SUCCESS;
}

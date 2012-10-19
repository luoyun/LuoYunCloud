#include <stdio.h>
#include <signal.h>
#include <uuid/uuid.h>

#define logsimple printf

typedef struct LYSignal_t {
    int signo;
    char * name;
    struct sigaction * old_sa;
} LYSignal;

static LYSignal g_signals_all[] = {
    { SIGHUP, "SIGHUP", NULL },
    { SIGINT, "SIGINT", NULL },
    { SIGQUIT, "SIGQUIT", NULL },
    { SIGILL, "SIGILL", NULL },
    { SIGABRT, "SIGABRT", NULL },
    { SIGFPE, "SIGFPE", NULL },
    { SIGKILL, "SIGKILL", NULL },
    { SIGSEGV, "SIGSEGV", NULL },
    { SIGPIPE, "SIGPIPE", NULL },
    { SIGALRM, "SIGALRM", NULL },
    { SIGTERM, "SIGTERM", NULL },
    { SIGUSR1, "SIGUSR1", NULL },
    { SIGUSR2, "SIGUSR2", NULL },
    { SIGCHLD, "SIGCHLD", NULL },
    { SIGCONT, "SIGCONT", NULL },
    { SIGSTOP, "SIGSTOP", NULL },
    { SIGTSTP, "SIGTSTP", NULL },
    { SIGTTIN, "SIGTTIN", NULL },
    { SIGTTOU, "SIGTTOU", NULL },
    { SIGBUS, "SIGBUS", NULL },
    { SIGPROF, "SIGPROF", NULL },
    { SIGTRAP, "SIGTRAP", NULL },
    { SIGURG, "SIGURG", NULL },
    { SIGVTALRM, "SIGVTALRM", NULL },
    { SIGXCPU, "SIGXCPU", NULL },
    { SIGXFSZ, "SIGXFSZ", NULL },
    { SIGIOT, "SIGIOT", NULL },
    { SIGSTKFLT, "SIGSTKFLT", NULL },
    { SIGIO, "SIGIO", NULL },
    { SIGPWR, "SIGPWR", NULL },
    { SIGWINCH, "SIGWINCH", NULL },
    { SIGUNUSED, "SIGUNUSED", NULL },
    { 0, NULL, NULL }
};

void __signal_handler_default(int signo)
{
    return;
}

/* init default behavior of handling signals */
int lyutil_signal_init()
{
    LYSignal *s;
    for (s = g_signals_all; s->signo != 0; s++) {
#if 0
        struct sigaction sa;
        s->old_sa = malloc(sizeof(struct sigaction));
        if (s->old_sa == NULL)
            return -1;
        bzero(&sa, sizeof(struct sigaction));
        sa.sa_handler = __signal_handler_default;
        sigemptyset(&sa.sa_mask);
        if (sigaction(s->signo, &sa, s->old_sa) == -1) {
            logerror(_("sigaction(%s) failed\n"), s->name);
            return -1;
        }
#else
        sighandler_t old = signal(s->signo, __signal_handler_default);
        if (old == SIG_IGN) {
            logsimple("%d is IGN\n", s->signo);
            signal(s->signo, SIG_IGN);
        }
        else if (old == SIG_DFL)
            logsimple("%d is DFL\n", s->signo);
        else if (old == SIG_ERR)
            logsimple("%d is ERR\n", s->signo);
        else
            logsimple("%d is %p\n", s->signo, old);
#endif
    }

    return 0;
}

int lyutil_signal_cleanup()
{
    LYSignal *s;
    for (s = g_signals_all; s->signo != 0; s++) {
        if (s->old_sa)
            free(s->old_sa);
    }

    return 0;
}

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

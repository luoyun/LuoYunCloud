/* mount to a temp dir */
int system_loop_mount(const char *src, const char *dest, const char *options)
{
    int ret = -1;

    char nametemp[32] = "/tmp/LuoYun_XXXXXX";
    char * mount_path = NULL;
    if (dest == NULL) {
        mount_path = mkdtemp(nametemp);
        if (mount_path == NULL) {
            logerror(_("can not get a tmpdir for mount\n"));
            return -1;
        }
        dest = mount_path;
    }

    char * tmp4k = malloc(4096);
    if (tmp4k == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto out;
    }

    if (snprintf(tmp4k, 4096, "mount %s %s -o %s", src, dest, options)
        >= 4096) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto out;
    }
    if (system(tmp4k)) {
        logerror(_("failed executing %s\n"), tmp4k);
        goto out;
    }

    ret = 0;
out:
    if (ret < 0 && mount_path)
        remove(mount_path);
    if (tmp4k)
        free(tmp4k);
    return ret;
}

/* umount */
int system_loop_umount(const char *src, const char *dest)
{
    if (src == NULL && dest == NULL)
        return -1;

    int ret = -1;

    char * tmp4k = malloc(4096);
    if (tmp4k == NULL) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        return -1;
    }
    if (snprintf(tmp4k, 4096, "umount %s", src ? src : dest)
        >= 4096) {
        logerror(_("error in %s(%d)\n"), __func__, __LINE__);
        goto out;
    }
    if (system(tmp4k)) {
        logerror(_("failed executing %s\n"), tmp4k);
        goto out;
    }

    ret = 0;
out:
    free(tmp4k);
    return ret;
}


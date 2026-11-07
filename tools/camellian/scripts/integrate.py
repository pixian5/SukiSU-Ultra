import pathlib
K = pathlib.Path('/workspace/camellian-kernel')

def patch(rel, old, new, label):
    p = K / rel
    s = p.read_text()
    if new.strip() in s:
        print('  [skip] %s already applied' % label); return
    assert old in s, 'ANCHOR NOT FOUND: ' + label
    p.write_text(s.replace(old, new, 1))
    print('  [ok] ' + label)

# 1) symlink kernel side into drivers/
link = K / 'drivers/kernelsu'
if not link.exists():
    link.symlink_to('/workspace/SukiSU-Ultra/kernel', target_is_directory=True)
print('[1] symlink:', link, '->', link.resolve())

# 2) drivers/Makefile
p = K/'drivers/Makefile'; s = p.read_text()
if 'kernelsu' not in s:
    p.write_text(s.rstrip('\n') + '\n\nobj-$(CONFIG_KSU) += kernelsu/\n'); print('[2] drivers/Makefile patched')
else: print('[2] drivers/Makefile already has entry')

# 3) drivers/Kconfig (insert before the LAST endmenu)
p = K/'drivers/Kconfig'; s = p.read_text()
if 'drivers/kernelsu/Kconfig' not in s:
    i = s.rfind('endmenu'); assert i > 0
    p.write_text(s[:i] + 'source "drivers/kernelsu/Kconfig"\n\n' + s[i:]); print('[3] drivers/Kconfig patched')
else: print('[3] drivers/Kconfig already has entry')

# 4) fs/exec.c
patch('fs/exec.c',
 'static int do_execveat_common(int fd, struct filename *filename,',
 '''#ifdef CONFIG_KSU
/* SukiSU-Ultra：执行程序前的挂钩入口，实现位于 drivers/kernelsu */
extern int ksu_handle_execveat(int *fd, struct filename **filename_ptr,
                               void *argv, void *envp, int *flags);
#endif

static int do_execveat_common(int fd, struct filename *filename,''',
 'fs/exec.c extern declaration')
patch('fs/exec.c',
 '''\tif (IS_ERR(filename))\n\t\treturn PTR_ERR(filename);\n''',
 '''\tif (IS_ERR(filename))\n\t\treturn PTR_ERR(filename);\n\n#ifdef CONFIG_KSU\n\t/* SukiSU-Ultra：接管 su 请求，把执行路径重定向到 ksud 或 sh */\n\tksu_handle_execveat(&fd, &filename, &argv, &envp, &flags);\n#endif\n''',
 'fs/exec.c hook call')

# 5) fs/open.c
patch('fs/open.c',
 'SYSCALL_DEFINE3(faccessat, int, dfd, const char __user *, filename, int, mode)\n{',
 '''#ifdef CONFIG_KSU
/* SukiSU-Ultra：faccessat 挂钩，把对 su 的访问探测重定向到 sh */
extern int ksu_handle_faccessat(int *dfd, const char __user **filename_user,
                                int *mode, int *__unused_flags);
#endif

SYSCALL_DEFINE3(faccessat, int, dfd, const char __user *, filename, int, mode)
{''',
 'fs/open.c extern declaration')
patch('fs/open.c',
 '\tunsigned int lookup_flags = LOOKUP_FOLLOW;\n\n\tif (mode & ~S_IRWXO)',
 '''\tunsigned int lookup_flags = LOOKUP_FOLLOW;\n\n#ifdef CONFIG_KSU\n\t/* SukiSU-Ultra：接管 su 的 access 探测 */\n\tksu_handle_faccessat(&dfd, &filename, &mode, NULL);\n#endif\n\n\tif (mode & ~S_IRWXO)''',
 'fs/open.c hook call')

# 6) fs/stat.c
patch('fs/stat.c',
 'int vfs_statx(int dfd, const char __user *filename, int flags,',
 '''#ifdef CONFIG_KSU
/* SukiSU-Ultra：stat 挂钩，把对 su 的状态探测重定向到 sh */
extern int ksu_handle_stat(int *dfd, const char __user **filename_user, int *flags);
#endif

int vfs_statx(int dfd, const char __user *filename, int flags,''',
 'fs/stat.c extern declaration')
patch('fs/stat.c',
 '\tunsigned int lookup_flags = LOOKUP_FOLLOW | LOOKUP_AUTOMOUNT;\n',
 '''\tunsigned int lookup_flags = LOOKUP_FOLLOW | LOOKUP_AUTOMOUNT;\n\n#ifdef CONFIG_KSU\n\t/* SukiSU-Ultra：接管 su 的 stat 探测 */\n\tksu_handle_stat(&dfd, &filename, &flags);\n#endif\n''',
 'fs/stat.c hook call')

# 7) fs/read_write.c
patch('fs/read_write.c',
 'ssize_t vfs_read(struct file *file, char __user *buf, size_t count, loff_t *pos)\n{\n\tssize_t ret;\n',
 '''#ifdef CONFIG_KSU
/* SukiSU-Ultra：读取挂钩，用于安装 ksud 的配置文件读取钩子 */
extern int ksu_handle_vfs_read(struct file **file_ptr, char __user **buf_ptr,
                               size_t *count_ptr, loff_t **pos);
#endif

ssize_t vfs_read(struct file *file, char __user *buf, size_t count, loff_t *pos)
{
\tssize_t ret;

#ifdef CONFIG_KSU
\t/* SukiSU-Ultra：在读取前安装配置钩子 */
\tksu_handle_vfs_read(&file, &buf, &count, &pos);
#endif
''',
 'fs/read_write.c extern + hook call')

# 8) kernel/reboot.c：给 ksud 子进程保留申请内核通道的入口
#    缺这一步时管理器能显示「工作中」，但授权会失败并报
#    "could not retrieve kernelsu driver fd"。
patch('kernel/reboot.c',
 '''SYSCALL_DEFINE4(reboot, int, magic1, int, magic2, unsigned int, cmd,
\t\tvoid __user *, arg)
{
\tstruct pid_namespace *pid_ns = task_active_pid_ns(current);
\tchar buffer[256];
\tint ret = 0;
''',
 '''SYSCALL_DEFINE4(reboot, int, magic1, int, magic2, unsigned int, cmd,
\t\tvoid __user *, arg)
{
\tstruct pid_namespace *pid_ns = task_active_pid_ns(current);
\tchar buffer[256];
\tint ret = 0;

#ifdef CONFIG_KSU
\t{
\t\t/* SukiSU-Ultra：给 ksud 子进程一个申请内核通道的入口。
\t\t * 管理器注入的匿名 fd 带 exec 关闭标志，子进程继承不到，
\t\t * 因此 ksud 通过带魔数的 reboot 系统调用重新申请。 */
\t\textern int ksu_handle_sys_reboot(int magic1, int magic2, unsigned int cmd, void __user **arg);
\t\tint ksu_ret = ksu_handle_sys_reboot(magic1, magic2, cmd, &arg);
\t\tif (ksu_ret == 0)
\t\t\treturn 0;
\t}
#endif
''',
 'kernel/reboot.c ksu hook')

# 9) 模块侧 supercall/dispatch.c：读取不存在的应用配置时返回默认 profile
#    官方 release 管理器把 -ENOENT 当成失败，会中止授权流程。
#    路径经由 drivers/kernelsu 软链接落在 SukiSU 仓库里。
patch('drivers/kernelsu/supercall/dispatch.c',
 '''    if (!profile) {
        ret = -ENOENT;
    } else {
''',
 '''    if (!profile) {
        /* SukiSU-Ultra：官方 release 管理器把「配置不存在」当成失败，
         * 授权流程会中止（界面提示「更新 app profile 失败」）。
         * 这里返回一份允许默认配置的空白 profile，让授权能继续。 */
        struct app_profile fallback;

        memset(&fallback, 0, sizeof(fallback));
        fallback.version = KSU_APP_PROFILE_VER;
        fallback.curr_uid = uid;
        fallback.allow_su = false;
        fallback.nrp_config.use_default = true;
        fallback.nrp_config.profile.umount_modules = true;
        if (copy_to_user((char __user *)arg + offsetof(struct ksu_get_app_profile_cmd, profile),
                         &fallback, sizeof(fallback))) {
            pr_err("get_app_profile: copy_to_user fallback failed\\n");
            ret = -EFAULT;
        }
    } else {
''',
 'dispatch.c app_profile fallback')
print('[done]')

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
print('[done]')

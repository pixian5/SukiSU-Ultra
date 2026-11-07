#!/usr/bin/env python3
"""在 camellian 4.14 内核树里接入 SukiSU + SUSFS v2.3.0 兼容层。

用法：
    python3 tools/camellian-susfs/scripts/integrate-susfs.py /path/to/camellian-kernel

做四件事：
  1. 应用上游 susfs4ksu kernel-4.14 v1.5.5 补丁（含两处本内核需要的手工适配）
  2. 用 v2.3.0 ABI 兼容层替换核心与头文件（fs/susfs.c、fs/susfs_abi.c、include/linux/susfs*.h）
  3. 接入 SukiSU 手动挂钩（若尚未接入）
  4. 在 kernel/sys.c 补 ksu_handle_setresuid（SUSFS 模式下 LSM 钩子不注册）

IDEMPOTENT：重复执行只会打印 skip。
"""
import argparse
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve()
BUNDLE = HERE.parent.parent                      # tools/camellian-susfs
REPO = BUNDLE.parent.parent                      # repository root
SUSFS_PATCH = BUNDLE / 'patches' / '50_add_susfs_in_kernel-4.14.patch'
KERNEL_FILES = BUNDLE / 'kernel'

CONFIGS = [
    'CONFIG_KSU=y',
    'CONFIG_KSU_SUSFS=y',
    'CONFIG_KSU_SUSFS_SUS_PATH=y',
    'CONFIG_KSU_SUSFS_SUS_MOUNT=y',
    'CONFIG_KSU_SUSFS_SUS_KSTAT=y',
    'CONFIG_KSU_SUSFS_SPOOF_UNAME=y',
    'CONFIG_KSU_SUSFS_ENABLE_LOG=y',
    'CONFIG_KSU_SUSFS_HIDE_KSU_SUSFS_SYMBOLS=y',
    'CONFIG_KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG=y',
    'CONFIG_KSU_SUSFS_OPEN_REDIRECT=y',
    'CONFIG_KSU_SUSFS_SUS_MAP=y',
]


def patch_file(k: pathlib.Path, rel: str, old: str, new: str, label: str) -> None:
    p = k / rel
    s = p.read_text()
    if new.strip() in s:
        print('  [skip]', label)
        return
    if old not in s:
        raise SystemExit(f'ANCHOR NOT FOUND: {label} ({rel})')
    p.write_text(s.replace(old, new, 1))
    print('  [ok]', label)


def apply_susfs_patch(k: pathlib.Path) -> None:
    if (k / 'fs' / 'susfs.c').exists():
        print('[1] susfs 补丁已应用，跳过')
        return
    print('[1] 应用上游 susfs4ksu kernel-4.14 补丁')
    r = subprocess.run(['patch', '-p1', '-i', str(SUSFS_PATCH)], cwd=k,
                       capture_output=True, text=True)
    print('   ', r.stdout.strip().splitlines()[-1] if r.stdout.strip() else '')
    # 本内核的 inotify_fdinfo 没有 file 参数，fdinfo 隐藏块跳过；
    # compat_fillonedir 的上下文与上游不同，单独补。
    for rej in k.rglob('*.rej'):
        print('    skip hunk:', rej.relative_to(k))
        rej.unlink()
    patch_file(k, 'fs/readdir.c',
               """	struct compat_old_linux_dirent __user *dirent;
	compat_ulong_t d_ino;

	if (buf->result)
		return -EINVAL;
	d_ino = ino;
""",
               """	struct compat_old_linux_dirent __user *dirent;
	compat_ulong_t d_ino;

	if (buf->result)
		return -EINVAL;
#ifdef CONFIG_KSU_SUSFS_SUS_PATH
	if (likely(current->susfs_task_state & TASK_STRUCT_NON_ROOT_USER_APP_PROC) && susfs_sus_ino_for_filldir64(ino)) {
		return 0;
	}
#endif
	d_ino = ino;
""",
               'fs/readdir.c compat_fillonedir')


def install_v2_layer(k: pathlib.Path) -> None:
    print('[2] 安装 SUSFS v2.3.0 ABI 兼容层')
    shutil.copy2(KERNEL_FILES / 'fs' / 'susfs.c', k / 'fs' / 'susfs.c')
    shutil.copy2(KERNEL_FILES / 'fs' / 'susfs_abi.c', k / 'fs' / 'susfs_abi.c')
    shutil.copy2(KERNEL_FILES / 'include' / 'linux' / 'susfs.h', k / 'include' / 'linux' / 'susfs.h')
    shutil.copy2(KERNEL_FILES / 'include' / 'linux' / 'susfs_def.h', k / 'include' / 'linux' / 'susfs_def.h')
    p = k / 'fs' / 'Makefile'
    s = p.read_text()
    if 'susfs_abi.o' not in s:
        s = s.replace('obj-$(CONFIG_KSU_SUSFS) += susfs.o',
                      'obj-$(CONFIG_KSU_SUSFS) += susfs.o susfs_abi.o')
        p.write_text(s)
    print('  [ok] fs/susfs.c, fs/susfs_abi.c, include/linux/susfs*.h')


def install_sukisu_hooks(k: pathlib.Path, ksu: pathlib.Path) -> None:
    print('[3] 接入 SukiSU 手动挂钩')
    link = k / 'drivers' / 'kernelsu'
    if not link.exists():
        link.symlink_to(ksu, target_is_directory=True)

    p = k / 'drivers' / 'Makefile'
    s = p.read_text()
    if 'kernelsu' not in s:
        p.write_text(s.rstrip('\n') + '\n\nobj-$(CONFIG_KSU) += kernelsu/\n')

    p = k / 'drivers' / 'Kconfig'
    s = p.read_text()
    if 'drivers/kernelsu/Kconfig' not in s:
        i = s.rfind('endmenu')
        p.write_text(s[:i] + 'source "drivers/kernelsu/Kconfig"\n\n' + s[i:])

    patch_file(k, 'fs/exec.c',
               'static int do_execveat_common(int fd, struct filename *filename,',
               '''#ifdef CONFIG_KSU
extern int ksu_handle_execveat(int *fd, struct filename **filename_ptr,
                               void *argv, void *envp, int *flags);
#endif

static int do_execveat_common(int fd, struct filename *filename,''',
               'fs/exec.c extern')
    patch_file(k, 'fs/exec.c',
               '\tif (IS_ERR(filename))\n\t\treturn PTR_ERR(filename);\n',
               '\tif (IS_ERR(filename))\n\t\treturn PTR_ERR(filename);\n\n'
               '#ifdef CONFIG_KSU\n\tksu_handle_execveat(&fd, &filename, &argv, &envp, &flags);\n#endif\n',
               'fs/exec.c hook')
    patch_file(k, 'fs/open.c',
               'SYSCALL_DEFINE3(faccessat, int, dfd, const char __user *, filename, int, mode)\n{',
               '''#ifdef CONFIG_KSU
extern int ksu_handle_faccessat(int *dfd, const char __user **filename_user,
                                int *mode, int *__unused_flags);
#endif

SYSCALL_DEFINE3(faccessat, int, dfd, const char __user *, filename, int, mode)
{''',
               'fs/open.c extern')
    patch_file(k, 'fs/open.c',
               '\tunsigned int lookup_flags = LOOKUP_FOLLOW;\n\n\tif (mode & ~S_IRWXO)',
               '\tunsigned int lookup_flags = LOOKUP_FOLLOW;\n\n'
               '#ifdef CONFIG_KSU\n\tksu_handle_faccessat(&dfd, &filename, &mode, NULL);\n#endif\n\n'
               '\tif (mode & ~S_IRWXO)',
               'fs/open.c hook')
    patch_file(k, 'fs/stat.c',
               'int vfs_statx(int dfd, const char __user *filename, int flags,',
               '''#ifdef CONFIG_KSU
extern int ksu_handle_stat(int *dfd, const char __user **filename_user, int *flags);
#endif

int vfs_statx(int dfd, const char __user *filename, int flags,''',
               'fs/stat.c extern')
    patch_file(k, 'fs/stat.c',
               '\tunsigned int lookup_flags = LOOKUP_FOLLOW | LOOKUP_AUTOMOUNT;\n',
               '\tunsigned int lookup_flags = LOOKUP_FOLLOW | LOOKUP_AUTOMOUNT;\n\n'
               '#ifdef CONFIG_KSU\n\tksu_handle_stat(&dfd, &filename, &flags);\n#endif\n',
               'fs/stat.c hook')
    patch_file(k, 'fs/read_write.c',
               'ssize_t vfs_read(struct file *file, char __user *buf, size_t count, loff_t *pos)\n{\n\tssize_t ret;\n',
               '''#ifdef CONFIG_KSU
extern int ksu_handle_vfs_read(struct file **file_ptr, char __user **buf_ptr,
                               size_t *count_ptr, loff_t **pos);
#endif

ssize_t vfs_read(struct file *file, char __user *buf, size_t count, loff_t *pos)
{
	ssize_t ret;

#ifdef CONFIG_KSU
	ksu_handle_vfs_read(&file, &buf, &count, &pos);
#endif
''',
               'fs/read_write.c hook')
    patch_file(k, 'kernel/reboot.c',
               '''SYSCALL_DEFINE4(reboot, int, magic1, int, magic2, unsigned int, cmd,
		void __user *, arg)
{
	struct pid_namespace *pid_ns = task_active_pid_ns(current);
	char buffer[256];
	int ret = 0;
''',
               '''SYSCALL_DEFINE4(reboot, int, magic1, int, magic2, unsigned int, cmd,
		void __user *, arg)
{
	struct pid_namespace *pid_ns = task_active_pid_ns(current);
	char buffer[256];
	int ret = 0;

#ifdef CONFIG_KSU
	{
		extern int ksu_handle_sys_reboot(int magic1, int magic2, unsigned int cmd, void __user **arg);
		int ksu_ret = ksu_handle_sys_reboot(magic1, magic2, cmd, &arg);
		if (ksu_ret == 0)
			return 0;
	}
#endif
''',
               'kernel/reboot.c hook')


def fix_vendor_quirks(k: pathlib.Path) -> None:
    """本内核树里与 SUSFS 无关但会阻断链接的两处厂商问题。"""
    print('[5] 厂商树编译修复')
    p = k / 'drivers' / 'media' / 'platform' / 'mtk-vcu' / 'Makefile'
    s = p.read_text()
    old = 'obj-$(CONFIG_VIDEO_MEDIATEK_VCU) += mtk-vcu.o mtk_vcodec_mem.o'
    if old in s:
        p.write_text(s.replace(old, 'obj-$(CONFIG_VIDEO_MEDIATEK_VCU) += mtk-vcu.o', 1))
        print('  [ok] mtk-vcu 重复目标文件（thin archive/LTO 下会报 duplicate symbol）')
    else:
        print('  [skip] mtk-vcu Makefile')


def install_setresuid_hook(k: pathlib.Path) -> None:
    print('[4] kernel/sys.c 补 ksu_handle_setresuid')
    p = k / 'kernel' / 'sys.c'
    s = p.read_text()
    if 'ksu_handle_setresuid' in s:
        print('  [skip] 已存在')
        return
    old = '''SYSCALL_DEFINE3(setresuid, uid_t, ruid, uid_t, euid, uid_t, suid)
{
	struct user_namespace *ns = current_user_ns();
	const struct cred *old;
	struct cred *new;
	int retval;
	kuid_t kruid, keuid, ksuid;

	kruid = make_kuid(ns, ruid);
'''
    new = '''SYSCALL_DEFINE3(setresuid, uid_t, ruid, uid_t, euid, uid_t, suid)
{
#if defined(CONFIG_KSU) && defined(CONFIG_KSU_SUSFS)
	extern int ksu_handle_setresuid(uid_t ruid, uid_t euid, uid_t suid);
#endif
	struct user_namespace *ns = current_user_ns();
	const struct cred *old;
	struct cred *new;
	int retval;
	kuid_t kruid, keuid, ksuid;

#if defined(CONFIG_KSU) && defined(CONFIG_KSU_SUSFS)
	/* SUSFS 模式下 LSM task_fix_setuid 不注册，这里补上调用：
	 * zygote fork 应用时标记 umounted、关闭 seccomp、安装驱动 fd。 */
	ksu_handle_setresuid(ruid, euid, suid);
#endif

	kruid = make_kuid(ns, ruid);
'''
    if old not in s:
        raise SystemExit('ANCHOR NOT FOUND: kernel/sys.c setresuid')
    p.write_text(s.replace(old, new, 1))
    print('  [ok]')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('kernel_tree', help='camellian 内核源码根目录')
    ap.add_argument('--ksu-kernel', default=str(REPO / 'kernel'),
                    help='SukiSU kernel/ 目录（默认本仓库）')
    args = ap.parse_args()
    k = pathlib.Path(args.kernel_tree).resolve()
    ksu = pathlib.Path(args.ksu_kernel).resolve()
    if not (k / 'Makefile').exists():
        sys.exit(f'不是内核源码树: {k}')

    apply_susfs_patch(k)
    install_v2_layer(k)
    install_sukisu_hooks(k, ksu)
    fix_vendor_quirks(k)
    install_setresuid_hook(k)

    print('\n[config] 在 defconfig/.config 里确认以下选项：')
    for c in CONFIGS:
        print('   ', c)


if __name__ == '__main__':
    main()

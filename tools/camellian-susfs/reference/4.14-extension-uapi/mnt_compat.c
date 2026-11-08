// SPDX-License-Identifier: GPL-2.0
/*
 * 4.14 挂载编号兼容层：为公开的 SuSFS 扩展接口实现补上两个外部函数。
 *
 * 来源：iput-object/kernel_xiaomi_sm6250 @ 9700db640bbb5b27dca74ea06450d4c59550ebcc
 *       的 fs/namespace.c（函数体原样，仅补齐 include 与中文注释）。
 *
 * 作用：SuSFS 会给「由 root 后台进程创建或克隆」的挂载分配一个很大的
 * 挂载编号（>= DEFAULT_KSU_MNT_ID）。这两个函数沿挂载父链向上回溯，
 * 取回未被伪装的原始编号 / 原始 vfsmount，供隐藏挂载功能使用。
 *
 * 边界：这是**编译与链接验证用的适配层**，功能没有在真机验证过，
 * 不要把它当成已经可用的隐藏能力；也不要用它替换主线 v0.0.6 的实现。
 */
#include <linux/kernel.h>
#include <linux/mount.h>
#include <linux/dcache.h>
#include <linux/err.h>
#include <linux/susfs_def.h>
#include "mount.h"   // struct mount / real_mount / 挂载哈希锁是 fs/ 目录私有定义

#ifdef CONFIG_KSU_SUSFS

/* 取回未被伪装的挂载编号 */
int susfs_get_non_sus_mnt_id_from_mnt(struct mount *orig_mnt)
{
	struct mount *mnt = orig_mnt;
	int mnt_id;

	if (mnt->mnt_id < DEFAULT_KSU_MNT_ID)
		return mnt->mnt_id;

	lock_mount_hash();
	for (; mnt && mnt->mnt_parent && mnt != mnt->mnt_parent &&
	       mnt->mnt_id >= DEFAULT_KSU_MNT_ID; mnt = mnt->mnt_parent) { }
	mnt_id = mnt->mnt_id;
	unlock_mount_hash();
	return mnt_id;
}

/* 取回未被伪装的 vfsmount，并对 mnt 与根 dentry 增加引用 */
struct vfsmount *susfs_get_non_sus_vfsmnt_from_vfsmnt(struct vfsmount *vfsmnt)
{
	struct mount *mnt = real_mount(vfsmnt);

	if (mnt->mnt_id < DEFAULT_KSU_MNT_ID) {
		mntget(&mnt->mnt);
		dget(mnt->mnt.mnt_root);
		return &mnt->mnt;
	}

	lock_mount_hash();
	for (; mnt && mnt->mnt_parent && mnt != mnt->mnt_parent &&
	       mnt->mnt_id >= DEFAULT_KSU_MNT_ID; mnt = mnt->mnt_parent) { }
	mntget(&mnt->mnt);
	if (!mnt->mnt.mnt_root || IS_ERR(mnt->mnt.mnt_root)) {
		mntput(&mnt->mnt);
		unlock_mount_hash();
		return vfsmnt;
	}
	dget(mnt->mnt.mnt_root);
	unlock_mount_hash();
	return &mnt->mnt;
}

#endif // CONFIG_KSU_SUSFS

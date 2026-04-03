# ───────────────── DICTS SUPPLÉMENTAIRES ─────────────────
# Description des fichiers systèmes Linux importants
# Utilisé pour enrichir les descriptions (priorité haute)

LINUX_SPECIAL_FILES = {
        # ── SYSTEM CONFIG & ENVIRONMENT ──────────────────
    "/etc/environment": "global environment variables",
    "/etc/profile": "system-wide shell profile",
    "/etc/bash.bashrc": "system-wide bash config (Debian/Ubuntu)",
    "/etc/bashrc": "system-wide bash config (RHEL/CentOS)",
    "/etc/hostname": "system static hostname",
    "/etc/issue": "pre-login message/system identification",
    "/etc/motd": "message of the day (post-login)",
    "/etc/locale.conf": "system language and regional settings",
    "/etc/os-release": "operating system identification",
    "/etc/shells": "list of valid login shells",
    "/etc/timezone": "system timezone configuration",
    "/etc/skel/.bashrc": "default bashrc template for new users",
    
    # ── USER SHELL CONFIGS (HOME) ────────────────────
    "~/.bashrc": "user-specific bash aliases and functions",
    "~/.bash_profile": "user login shell configuration",
    "~/.bash_logout": "commands executed at user logout",
    "~/.profile": "user-specific environment settings",
    "~/.zshrc": "Zsh shell configuration (if installed)",
    
    # ── NETWORK & DNS ────────────────────────────────
    "/etc/hosts": "static hostname to IP mapping",
    "/etc/resolv.conf": "DNS resolver configuration",
    "/etc/network/interfaces": "legacy network interface config",
    "/etc/netplan": "modern network configuration (Ubuntu/Debian)",
    "/etc/nsswitch.conf": "name service switch configuration",
    "/etc/host.conf": "resolver lookup order",
    "/etc/protocols": "list of IP protocols and numbers",
    "/etc/services": "list of port names and numbers",
    
    # ── USERS & SECURITY ─────────────────────────────
    "/etc/passwd": "user account information",
    "/etc/shadow": "secure user password hashes",
    "/etc/group": "group account information",
    "/etc/gshadow": "secure group password hashes",
    "/etc/sudoers": "sudo privileges configuration",
    "/etc/pam.d": "pluggable authentication modules config",
    "/etc/login.defs": "shadow password suite configuration",
    "/etc/securetty": "list of terminals allowed for root login",
    "/etc/security/limits.conf": "system resource limits for users",
    "~/.ssh/authorized_keys": "SSH public keys for remote access",
    "~/.ssh/id_rsa": "SSH private key (highly sensitive)",
    "~/.ssh/known_hosts": "list of trusted remote host keys",
    
    # ── FILESYSTEM & STORAGE ─────────────────────────
    "/etc/fstab": "static information about filesystems",
    "/etc/mtab": "list of currently mounted filesystems",
    "/etc/crypttab": "encrypted device table",
    "/etc/exports": "NFS server export configuration",
    "/etc/auto.master": "autofs mount points configuration",
    
    # ── SERVICES & CRON ──────────────────────────────
    "/etc/crontab": "system-wide cron schedule",
    "/etc/cron.d": "modular system cron jobs",
    "/etc/systemd/system": "systemd service unit files",
    "/etc/ssh/sshd_config": "SSH server daemon configuration",
    "/etc/nginx/nginx.conf": "Nginx web server configuration",
    "/etc/apache2/apache2.conf": "Apache web server configuration",
    "/etc/mysql/my.cnf": "MySQL/MariaDB database configuration",
    "/etc/redis/redis.conf": "Redis server configuration",
    
    # ── PACKAGE MANAGEMENT ───────────────────────────
    "/etc/apt/sources.list": "APT software repository list",
    "/etc/apt/sources.list.d": "additional APT repository files",
    "/etc/yum.repos.d": "YUM/DNF repository configuration",
    "/var/lib/dpkg/status": "installed package status database",
    
    # ── KERNEL & HARDWARE ────────────────────────────
    "/etc/modules": "list of kernel modules to load at boot",
    "/etc/modprobe.d": "kernel module loading rules",
    "/etc/sysctl.conf": "kernel runtime parameters (sysctl)",
    "/etc/X11/xorg.conf": "X Server (graphics) configuration",
    "/boot/grub/grub.cfg": "GRUB bootloader configuration",
    
    # ── VIRTUAL FILESYSTEMS (KERNEL/PROCESS) ──────────
    "/proc/cpuinfo": "processor and architecture details",
    "/proc/meminfo": "detailed memory usage statistics",
    "/proc/uptime": "system uptime and idle time",
    "/proc/version": "kernel version and build info",
    "/proc/cmdline": "bootloader kernel parameters",
    "/proc/net/dev": "network interface statistics",
    "/proc/sys": "kernel runtime parameters (sysctl)",
    "/proc/self/exe": "link to current process executable",
    "/dev/null": "null device (data sink)",
    "/dev/zero": "zero device (null byte generator)",
    "/dev/random": "blocking random number generator",
    "/dev/urandom": "non-blocking random number generator",
    "/dev/sda": "primary hard drive device file",
    
    # ── LOGS & HISTORY ────────────────────────────────
    "/var/log/syslog": "central system log (Debian/Ubuntu)",
    "/var/log/messages": "general system log (RHEL/CentOS)",
    "/var/log/auth.log": "authentication and security logs",
    "/var/log/kern.log": "kernel messages log",
    "/var/log/dmesg": "kernel ring buffer messages",
    "/var/log/dpkg.log": "Debian package manager logs",
    "/var/log/apt/history.log": "apt package history",
    "/var/log/faillog": "failed login attempts",
    "/var/log/lastlog": "last login information for users",
    "/var/log/wtmp": "login/logout history (binary)",
    "/var/log/btmp": "failed login records (binary)",
    "~/.bash_history": "user shell command history",
}
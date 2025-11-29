# AppArmor Profile for Secure Exam System
# This profile implements a deny-by-default policy for exam mode
# Only explicitly allowed processes and actions are permitted

#include <tunables/global>

profile secure-exam-system flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/nameservice>
  
  # ===== DENY BY DEFAULT =====
  # Everything is denied unless explicitly allowed below
  
  # ===== NETWORK ACCESS =====
  # Allow network access only through VPN interface
  network inet stream,
  network inet6 stream,
  network inet dgram,
  network inet6 dgram,
  
  # ===== FILE SYSTEM ACCESS =====
  
  # Allow read access to system libraries and binaries
  /lib/** r,
  /usr/lib/** r,
  /usr/share/** r,
  
  # Allow execution of allowed binaries
  /usr/bin/python3* ix,
  /usr/bin/chromium-browser ix,
  /usr/bin/chromium ix,
  
  # System processes (critical)
  /usr/lib/systemd/systemd ix,
  /usr/bin/dbus-daemon ix,
  /usr/bin/X ix,
  /usr/bin/Xorg ix,
  /usr/bin/pulseaudio ix,
  /usr/bin/pipewire ix,
  
  # Shells - EXPLICITLY DENIED  
  deny /bin/bash x,
  deny /bin/sh x,
  deny /bin/dash x,
  deny /bin/zsh x,
  deny /bin/fish x,
  
  # Terminal emulators - DENIED
  deny /usr/bin/gnome-terminal x,
  deny /usr/bin/konsole x,
  deny /usr/bin/xterm x,
  deny /usr/bin/terminator x,
  deny /usr/bin/tilix x,
  deny /usr/bin/alacritty x,
  
  # Package managers - DENIED
  deny /usr/bin/apt x,
  deny /usr/bin/apt-get x,
  deny /usr/bin/dpkg x,
  deny /usr/bin/yum x,
  deny /usr/bin/dnf x,
  deny /usr/bin/pacman x,
  deny /usr/bin/snap x,
  
  # Privilege escalation tools - DENIED
  deny /usr/bin/sudo x,
  deny /usr/bin/su x,
  deny /usr/bin/pkexec x,
  deny /usr/bin/gksu x,
  deny /usr/bin/kdesu x,
  
  # System modification tools - DENIED
  deny /usr/bin/systemctl x,
  deny /usr/sbin/modprobe x,
  deny /usr/sbin/insmod x,
  deny /usr/sbin/rmmod x,
  
  # File managers - DENIED (could be used to bypass)
  deny /usr/bin/nautilus x,
  deny /usr/bin/dolphin x,
  deny /usr/bin/thunar x,
  deny /usr/bin/nemo x,
  
  # Text editors - DENIED
  deny /usr/bin/gedit x,
  deny /usr/bin/kate x,
  deny /usr/bin/vim x,
  deny /usr/bin/vi x,
  deny /usr/bin/nano x,
  deny /usr/bin/emacs x,
  
  # Development tools - DENIED
  deny /usr/bin/gcc x,
  deny /usr/bin/g++ x,
  deny /usr/bin/make x,
  deny /usr/bin/cmake x,
  deny /usr/bin/python x,
  deny /usr/bin/python2* x,
  deny /usr/bin/perl x,
  deny /usr/bin/ruby x,
  deny /usr/bin/node x,
  
  # Allow read/write to temp directories
  /tmp/** rw,
  /var/tmp/** rw,
  
  # Allow read/write to user's home for browser profile
  owner @{HOME}/.config/chromium/** rw,
  owner @{HOME}/.cache/chromium/** rw,
  owner /tmp/exam-browser-profile/** rw,
  
  # Allow read-only access to user's home (for exam files)
  owner @{HOME}/** r,
  
  # Deny write to sensitive system locations
  deny /etc/** w,
  deny /boot/** w,
  deny /sys/** w,
  
  # ===== CAPABILITIES =====
  # Deny dangerous capabilities
  deny capability sys_admin,
  deny capability sys_module,
  deny capability sys_rawio,
  deny capability dac_override,
  deny capability dac_read_search,
  deny capability chown,
  deny capability setuid,
  deny capability setgid,
  
  # ===== PROCESS RESTRICTIONS =====
  # Prevent forking unauthorized processes
  deny /proc/*/exe r,
  
  # ===== DBUS RESTRICTIONS =====
  # Allow basic dbus communication for GUI
  dbus,
  
  # ==== SIGNALS =====
  signal send set=(term,kill),
  signal receive set=(term,kill),
}

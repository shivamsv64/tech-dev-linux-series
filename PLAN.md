# Linux Zero to Hero — episode plan (Tech-dev)

Daily at 5:00 PM IST on the Tech-Dev channel (YouTube channel id UCkMTPE1hLFUG1-4ccCDmP9w).
Ep 1 published Sat 31 Oct 2026 (evening). Ep N goes live on 31 Oct + (N-1) days at 17:00 IST.
Full plan doc: https://claude.ai/artifact/PJPYUrTLpfGzJqaknoJJMw

| Ep | Date | Episode | Commands | Builds on | SRE scenario | Mistake shown |
|---|---|---|---|---|---|---|
| 1 | 31 Oct | Linux, the shell and your first commands | whoami, hostname, uname -a, echo $SHELL, cat /etc/os-release | — | First login to a new EC2 box | Typing Whoami: case-sensitive |
| 2 | 1 Nov | Moving around the filesystem | pwd, cd, ls -l -a -h -t -r, absolute vs relative paths, ~, .. | Ep 1 | Finding a Jenkins workspace under /var/lib/jenkins | cd into a path with spaces without quotes |
| 3 | 2 Nov | Getting help like a pro | man, --help, type, which, whatis, history, !!, Tab completion | Ep 1–2 | Learning an unknown CLI on a box with no internet | Searching Google before man |
| 4 | 3 Nov | Create and delete files and folders | mkdir -p, touch, rm -i, rm -r, rmdir | Ep 2 | Building a release folder layout in one command | rm -rf with a stray space; no undo |
| 5 | 4 Nov | Copy, move, rename and wildcards | cp -r -p, mv, *, ?, [ ], {a,b} | Ep 4 | Backing up configs: cp app.conf{,.bak} | mv silently overwriting (fix: -i, -n) |
| 6 | 5 Nov | Links and file details | ln -s, ln, stat, file, tree | Ep 5 | Symlink releases: current -> releases/v42 | Relative symlink breaks after moving |
| 7 | 6 Nov | Reading files and live logs | cat, less, head -n, tail -n, tail -f, tac | Ep 2 | Watching an app log live during a deploy | cat on a 4 GB log |
| 8 | 7 Nov | Count, sort and slice text | wc -l, sort -n -r -k, uniq -c, cut -d -f, paste | Ep 7 | Requests per status code in an access log | uniq without sort first |
| 9 | 8 Nov | Vim survival kit (and nano) | vim modes, :w, :q!, /search, dd, yy, p, u; nano | Ep 7 | Editing a config on a server with only vim | Stuck in vim: the way out |
| 10 | 9 Nov | Printing and saving output | echo -e, printf, tee, tee -a | Ep 7 | Log a script's output to screen and file | sudo echo x > /etc/file fails; use sudo tee |
| 11 | 10 Nov | Comparing files | diff -u, cmp, comm, sha256sum | Ep 8 | Config drift between two servers | comm on unsorted files |
| 12 | 11 Nov | stdin, stdout, stderr and redirection | >, >>, <, 2>, 2>&1, &>, /dev/null | Ep 10 | Silencing noisy cron output, keeping errors | cmd > f 2>&1 vs cmd 2>&1 > f |
| 13 | 12 Nov | Pipes and xargs | \|, xargs, xargs -I{}, xargs -0 | Ep 8, 12 | Deleting old build artifacts in one pipeline | Filenames with spaces breaking xargs |
| 14 | 13 Nov | Exit codes and chaining | $?, &&, \|\|, ;, $( ), true, false | Ep 12–13 | build && deploy \|\| alert in a Jenkins step | Not checking $? |
| 15 | 14 Nov | grep: find anything in text | grep -i -n -v -c -r -w -E, -A/-B/-C | Ep 7, 13 | First ERROR before a crash, with context | Regex . matching too much |
| 16 | 15 Nov | find: locate files by anything | find -name -type -size -mtime -user -exec, locate | Ep 4, 13 | Files over 500 MB modified in the last day | -exec rm without -print first |
| 17 | 16 Nov | sed: edit text without opening it | sed 's///g', -i, -n p, d, addresses | Ep 15 | Changing a port in 20 config files | sed -i without -i.bak |
| 18 | 17 Nov | awk: columns and quick reports | awk '{print $1}', -F, NR, NF, conditions, sums | Ep 8, 17 | Top 10 IPs and total bytes from nginx logs | Double quotes eating $1 |
| 19 | 18 Nov | Combo: a real log investigation | grep \| awk \| sort \| uniq -c \| sort -nr \| head | Ep 7–18 | 5xx spike: which endpoint, client, since when | Building the pipeline all at once |
| 20 | 19 Nov | Users and groups | id, who, w, useradd -m, usermod -aG, passwd, userdel, /etc/passwd | Ep 1 | Onboarding an engineer to the docker group | usermod -G without -a |
| 21 | 20 Nov | Permissions and chmod | ls -l decoded, chmod u+x, chmod 755, chmod -R | Ep 2, 20 | "Permission denied" running a deploy script | chmod 777 as a fix |
| 22 | 21 Nov | Ownership and defaults | chown user:group, chown -R, chgrp, umask | Ep 21 | Web root owned by the wrong user | chown -R on the wrong path |
| 23 | 22 Nov | sudo and su | sudo, sudo -i, su -, visudo, /etc/sudoers.d | Ep 20 | Least-privilege sudo for a CI account | Editing sudoers without visudo |
| 24 | 23 Nov | Special bits and ACLs | SUID, SGID, sticky bit, find -perm, getfacl, setfacl | Ep 16, 21 | Audit: list SUID binaries (Qualys/Wiz-style) | Sticky bit missing on a shared folder |
| 25 | 24 Nov | Seeing processes | ps aux, ps -ef --forest, top, htop, pgrep -a | Ep 15 | Which process is eating CPU? | ps aux \| grep java matching grep itself |
| 26 | 25 Nov | Signals and killing | kill -15, kill -9, pkill, killall, kill -l | Ep 25 | Graceful restart of a stuck worker | Jumping straight to kill -9 |
| 27 | 26 Nov | Jobs and background work | &, jobs, fg, bg, Ctrl+Z, nohup, nice, renice | Ep 26 | Long migration surviving logout | Closing SSH and losing a job |
| 28 | 27 Nov | systemd services | systemctl status/start/stop/restart/enable, unit files, daemon-reload | Ep 25 | Jenkins agent as a service | Forgetting daemon-reload |
| 29 | 28 Nov | Reading system logs | journalctl -u -f --since -p err, dmesg -T, /var/log | Ep 7, 28 | Service keeps restarting: find why | Reading only the last line |
| 30 | 29 Nov | Disk usage | df -h, df -i, du -sh, du -h --max-depth=1 \| sort -h, ncdu | Ep 8, 16 | Disk 98% full at 2 AM | Deleted log still held open (lsof +L1) |
| 31 | 30 Nov | Disks, partitions and mounts | lsblk, blkid, mount, umount, /etc/fstab, mkfs | Ep 30 | Mounting a new EBS volume | Bad fstab line (use nofail) |
| 32 | 1 Dec | Memory and load | free -h, uptime, load average, vmstat 1, iostat -x | Ep 25, 30 | CPU, memory or disk I/O? | Reading free instead of available |
| 33 | 2 Dec | Archives and compression | tar -czvf, tar -xzvf, tar -tf, gzip, zip, unzip | Ep 5 | Archiving logs older than 7 days | Extracting into the wrong folder (-C) |
| 34 | 3 Dec | Installing software | apt update/install/remove, dnf/yum, dpkg -l, rpm -qa | Ep 23 | Same install on Ubuntu and Amazon Linux | apt install before apt update |
| 35 | 4 Dec | IPs, routes and reachability | ip a, ip r, ping -c, traceroute, mtr | Ep 1 | VM cannot reach the internet | ICMP blocked looks like "host down" |
| 36 | 5 Dec | Ports and connections | ss -tulpn, netstat, lsof -i :8080, nc -zv | Ep 25, 35 | "Address already in use" on deploy | No sudo, missing process name |
| 37 | 6 Dec | Talking to web services | curl -I -v -X -d -H, curl -s \| jq, wget | Ep 13, 36 | Health-checking an API and a load balancer | Missing -L on redirects |
| 38 | 7 Dec | DNS | dig, dig +short, nslookup, host, /etc/hosts, /etc/resolv.conf | Ep 35 | Works by IP but not by name | Stale /etc/hosts override |
| 39 | 8 Dec | SSH done right | ssh, ssh-keygen -t ed25519, ssh-copy-id, ~/.ssh/config, -i, -J | Ep 21 | Jump host into a private subnet | Key permissions too open (chmod 600) |
| 40 | 9 Dec | Moving files between servers | scp, rsync -avz --delete --dry-run, sftp | Ep 33, 39 | Syncing build output to a web server | rsync trailing slash; --delete without --dry-run |
| 41 | 10 Dec | Environment, PATH and aliases | env, export, echo $PATH, ~/.bashrc, source, alias | Ep 3, 14 | Command works in shell but not in cron | Overwriting PATH |
| 42 | 11 Dec | Scheduling jobs | crontab -e/-l, cron syntax, at, systemctl list-timers | Ep 12, 41 | Nightly log cleanup and backup | Cron job fails silently |
| 43 | 12 Dec | Your first shell script | shebang, chmod +x, variables, $1, $#, if, for, set -euo pipefail | Ep 14, 21 | Disk-space alert script | script.sh vs ./script.sh |
| 44 | 13 Dec | Drill: "the server is slow" | uptime → top → free → iostat → df → journalctl | Modules 6–7 | Live triage of a slow EC2 instance | Rebooting before collecting evidence |
| 45 | 14 Dec | Capstone: "the website is down" | systemctl → ss → curl → journalctl → df → dig | Whole series | End-to-end outage investigation + cheat sheet | Fixing the symptom, not the root cause |

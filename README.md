## Repository stats:
![GitHub issues](https://img.shields.io/github/issues/shatadru/simpletools)
![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/shatadru/simpletools)
![GitHub last commit](https://img.shields.io/github/last-commit/shatadru/simpletools)

## otpgen.sh : 2 Factor Authentication for Linux

##### Supports : Fedora, Ubuntu, RHEL, Debian (more to be added including CentOS, Manjaro, Mint)

- Open a new issue for any Linux support and I will try to add it.

~~~
	otpgen.sh, otpgen:   2 Factor Authentication for Linux
              
                             This tool allows you to generate 2 step verification codes in Linux command line

			     Features:
				* Generate verification code offline
				* Support for both HOTP and TOTP based tokens
				* Automatic setup via QR Code
				* Add multiple account/keys

	Syntax:  ./otpgen.sh [-V|--version][-i|--install][--clean-install][-a|--add-key <path to image>] [-l|--list-key][-g|--gen-key]
         -V, --version       Print version
         
         -i, --install       Install otpgen.sh in system
                  
         --clean-install     Clean any local data and re-install
         
         -a, --add-key FILE  Add a new 2FA from image containing QR Code
         
         -l, --list-key      List all available 2FA stored in the system
         
         -g, --gen-key [ID]  Generate one time password
                             Passing ID is optional, else it will ask for ID
                             for which you want to generate OTP.       
    
 ~~~
 
You can read more details in my [Blog link](https://shatadru.in/wordpress/how-to-configure-two-step-authenticator-in-linux-shellgoogle-authenticator-freeotp-alternative/)

### otpgen CI Status:
![Fedora CI](https://github.com/shatadru/simpletools/workflows/Fedora%20CI/badge.svg)
![Ubuntu 18.04 CI](https://github.com/shatadru/simpletools/workflows/Ubuntu%2018.04%20CI/badge.svg)
![Ubuntu 20.04 CI](https://github.com/shatadru/simpletools/workflows/Ubuntu%2020.04%20CI/badge.svg)

![RHEL CI](https://github.com/shatadru/simpletools/workflows/RHEL%20CI/badge.svg)
![Debian CI](https://github.com/shatadru/simpletools/workflows/Debian%20CI/badge.svg)

![Shell-Check CI](https://github.com/shatadru/simpletools/workflows/Shell-Check%20CI/badge.svg)


#### fix_dup_rpm.sh

[Blog link](https://shatadru.in/wordpress/how-to-fix-duplicate-rpm-issue-in-rhel-fedora/)

- Can be used to remove duplicate rpms if package-cleanup is failing
~~~
Syntax:  bash fix_dup_rpm.sh [-v][-d]
         -d/--dry-run: Dry Run, do not make any changes, checks for duplicates, 
                       lists rpms need which will be removed. 
                       
         -v/--verbose: Prints verbose log
~~~

#### fix-rpm.sh	

[blog libk](https://shatadru.in/wordpress/how-to-verify-rpm-integrity-and-fix-any-rpm-issues-such-as-missing-files-unsatisfied-dependencies-modified-binaries-etc)

### vol-control.sh : 
###### Don't have volume control keys ? set this shell scrip in shortcut to control volumes


1. Save this script in /usr/bin or /bin, set execute permission and create keyboard shortut 

2. In GNOME goto keyboard settings -> Custom Shortcuts -> Click on "+" to add a new one 

3. It will popup a window where set 

  Name : Volume Low
  Command : /bin/vol-control.sh decrease

  Click on add -> Next you need to add key shortcut, click on where it is written as disabled, input the key combo you want

  Similary you can set :
  Name : Volume Up
  Command : /bin/vol-control.sh increase

  Name : Volume Mute
  Command : /bin/vol-control.sh mute


### notifyatlogin  : 
###### Log user logins and see notification everytime a remote user logs in. 

1. Save this script in /usr/bin or /bin, set execute permission and create keyboard shortut 
Add below lines in /etc/profile :
~~~
####### Notification at login #############
IP="$(echo $SSH_CONNECTION | cut -d " " -f 1)"
/usr/bin/notifyatlogin $IP
#########################################
~~~
2. The default behavior is it logs into system logs using logger and /var/log/login_history.

3. Additionally in case of a remote ssh login, where the $IP will be passed from /etc/profile, it will send a GUI notification using notify-send.

4. In case that does not work for you enable a wall message which should always work (Just remove the comment)

5. You can even enable notification for local login.

6. The script is easy to read so you should be able to modify it without any issue.

#### Fedora_wallpaper_changer.sh

- What does it do ?

   1. Let's face it windows 10 does have some cool features when its comes to user interface, like everytime you get awesome wallpaper whenever you boot up the system.

   2. With this script you can use online API like unsplash to set awesome wallpapers based on your choice.

   3. You can use other APIs as well to retrieve pics with little tweaking...

   4. Feel free to add features.

   5. Should ideally work in linux distros with GNOME 3 + systemd. but might need tweaking in other distros only tested in Fedora 25, 26


- How to install and run ?
~~~
# Fedora_wallpaper_changer.sh -s
# systemctl daemon-reload
# systemctl  fedora-wallpaper.service
~~~
- How to enable this on boot ?
~~~
#  systemctl enable fedora-wallpaper.service
~~~
- Config file :
~~~
/etc/fedora_wallpaper_changer.conf
~~~


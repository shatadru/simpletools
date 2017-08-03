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


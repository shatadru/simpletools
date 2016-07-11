
- vol-control.sh : don't have volume control keys ? set this shell scrip in shortcut to control volumes
~~~
Save this script in /usr/bin or /bin, set execute permission and create keyboard shortut 

In GNOME goto keyboard settings -> Custom Shortcuts -> Click on "+" to add a new one 

It will popup a window where set 
Name : Volume Low
Command : /bin/vol-control.sh decrease

Click on add -> Next you need to add key shortcut, click on where it is written as disabled, input the key combo you want

Similary you can set :
Name : Volume Up
Command : /bin/vol-control.sh increase

Name : Volume Mute
Command : /bin/vol-control.sh mute
~~~
- notifyatlogin  : Log user logins and see notification everytime a remote user logs in. 
~~~
Save this script in /usr/bin or /bin, set execute permission and create keyboard shortut 
Add below lines in /etc/profile :

####### Notification at login #############
IP="$(echo $SSH_CONNECTION | cut -d " " -f 1)"
/usr/bin/notifyatlogin $IP
#########################################
The default bahavour is it logs into system logs using logger and /var/log/login_history.

Additionally in case of a remote ssh login, where the $IP will be passed from /etc/profile, it will send a GUI notification using notify-send.

In case that does not work for you enable a wall message which should always work (Just remove the comment)

You can even enable notification for local login.

The script is easy to read so you should be able to modify it without any issue.
~~~

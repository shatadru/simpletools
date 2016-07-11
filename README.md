
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
- notifyatlogin  : Log user login  

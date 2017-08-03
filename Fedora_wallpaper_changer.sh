#!/bin/bash
# Author / Maintainer : Shatadru Bandyopadhyay sbandyop@redhat.com
#
#
# Licenced under GPLv3, check LICENSE.txt
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# export DBUS_SESSION_BUS_ADDRESS environment variable
#
# Should ideally work in linux distros with GNOME 3 + systemd. but might need tweaking in other distros only tested in Fedora 25, 26
#
# What does it do ?
#------------------
# Let's face it windows 10 does have some cool features when its comes to user interface, like everytime you get awesome wallpaper whenever you boot up the system.
# With this script you can use online API like unsplash to set awesome wallpapers based on your choice.
# You can use other APIs as well to retreive pics with little tweaking...
# Feel free to add features.
# Config file : /etc/fedora_wallpaper_changer.conf



 




#~~~~~~~~~~~~~~~~~~~~ Command Line Arg handling ~~~~~~~~~~~~~~~~~~~~~~~~~~ #

           # ---- Saves the command line argument ---- #
args=( "$@" )
#echo ${meminfo_args[@]}

numarg=$#

          # ----------- Argument parsing ------------#
argnum=$((numarg-1))
for i in `seq 0 "$argnum"`
        do
        key=${args[$i]}
        case $key in
                -s|--setup)

                        setup="1"
                ;;
                -r|--run)
                        run="1"
                ;;
                -d|--debug)
                        debug="1"
                        set -x
                ;;
                -h|--help)
                        help="1"
                ;;

                *)
                        error_show=1
                ;;
        esac
        #shift
done



#-----------
#### Functions

function down_new_pic () {
# check number of already present files and download remaining files....
cd /var/lib/fedora-wallpaper/
touch database
fdupes -d -N ./
num=$(ls|wc -l)

if [ "$num" -lt "$download_limit" ]; then
    remaining_num=$(echo $download_limit-$num|bc -l)
    while [  $remaining_num  -gt 0 ]; do
        file_name=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1`
        wget -O $file_name.jpg $imgurl
        echo "$file_name.jpg 0" >> database
        fdupes -d -N ./
        num=$(ls|wc -l)
        remaining_num=$(echo $download_limit-$num|bc -l)

        done
fi
fdupes -d -N ./

}
function down_one_pic_set () {

cd /var/lib/fedora-wallpaper/
        file_name=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1`
        wget -O $file_name.jpg $imgurl
        gsettings set org.gnome.desktop.background picture-uri file:///var/lib/fedora-wallpaper/$file_name.jpg && echo "$file_name.jpg 1" >> database

}

function del_old_pic () {

cd /var/lib/fedora-wallpaper/

rand=$( seq 1 5|shuf -n1)
for i in $(cat database |grep -iv deleted|sort -nk2 -r|awk '$NF!="0" {print $1}' |grep -iv $1|shuf|grep -iv $1 |head -n $rand);
do
  rm -rf $i
  sed -i "s/.*$i*/$i DELETED/g" database
done

}
#------------

function setup () {

  if [ "$EUID" -ne 0 ]
  then
          echo "$(tput setaf 1)Setup mode needs root, run with sudo or root user $(tput init)"
          exit
  fi

# We need 3 files
# 1. The config file /etc/fedora_wallpaper_changer.conf ; comes pre-loaded with config which should get you started ; uses unsplash by default to get images.
# 2. The service file fedora-wallpaper.service
# 3. The binary which reads the config file, fetches and sets wallpaper. It is started by fedora-wallpaper.service

# Additionally we also keep the temporary wallpapers in /var/lib/fedora-wallpaper/
#~~~~~ Create Temporary Files needed ~~~~~~~~~
#tempdirname=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1`
#mkdir /tmp/fedora-wallpaper-changer/$tempdirname/

echo "Creating config file..."
echo
cat > /etc/fedora_wallpaper_changer.conf <<EOF
#Screen resolution
# TODO : auto detect
screen_resolution=1920x1080


# img url should retun different images everytime for this to work
# we are taking advantage of unsplash API
# https://source.unsplash.com/
#
imgurl=https://source.unsplash.com/1920x1080/?nature,water

#How many images should we download when internet is available for offline use
#
download_limit=10

# Rate at which wallpaper should be changed
#
refresh_rate=2

EOF


echo "Creating service file"
echo

cat > /etc/systemd/system/fedora-wallpaper.service <<EOF

[Unit]
Description=Changes Wallpaper automatically
After=graphical.target

[Service]
Type=simple
Environment=DISPLAY=:0
User=shatadru
ExecStart=/sbin/Fedora_wallpaper_changer.sh --run
IgnoreSIGPIPE=false

[Install]
WantedBy=graphical.target

EOF



echo "Copying the binary in /sbin"
echo
cp -f "$(readlink -f $0)" "/sbin/"
chmod +x /sbin/$0
}


function run () {

USER=$(whoami)
PID=$(pgrep -u $USER gnome-session)
export DBUS_SESSION_BUS_ADDRESS=$(grep -z DBUS_SESSION_BUS_ADDRESS /proc/$PID/environ|cut -d= -f2-)
echo "Starting service..."

# reading the config

if [ "$EUID" -eq 0 ]
then
        echo "$(tput setaf 1)This does not work as root$(tput init)"
        exit
fi

error=0
if [ ! -f /etc/fedora_wallpaper_changer.conf ]; then
	echo "Config file not found!; Run setup"
	error=1
fi

if [ ! -f /etc/systemd/system/fedora-wallpaper.service ]; then
	echo "Service file not found!; Run setup"
	error=1
fi

if [ ! -f /etc/systemd/system/fedora-wallpaper.service ]; then
	echo "Service file not found!; Run setup"
	error=1
fi

bin_path=$(readlink -f $0)


if [ "$bin_path" != "/sbin/Fedora_wallpaper_changer.sh" ] && [  "$bin_path" != "/usr/sbin/Fedora_wallpaper_changer.sh" ] ; then
	echo "We are not running from /sbin/ !; Did you run setup ?"
	error=1
fi

if [ $error -eq "1" ]
then
        echo "Did you run the installer?? Either missing config file or something is wrong"
        echo "Can't continue, sorry!! Please try to install/re-install if the issue persists please report it."
        exit
fi

CONFIG=/etc/fedora_wallpaper_changer.conf
imgurl=$(awk -F "=" '/^imgurl/{print $2}' "${CONFIG}")
download_limit=$(awk -F "=" '/^download_limit/{print $2}' "${CONFIG}")
refresh_rate=$(awk -F "=" '/^refresh_rate/{print $2}' "${CONFIG}")
screen_resolution=$(awk -F "=" '/^screen_resolution/{print $2}' "${CONFIG}")
refresh_rate_s=$(echo $refresh_rate*60|bc -l)
echo
echo "Current config :"
echo $imgurl
echo $download_limit
echo $refresh_rate
echo $screen_resolution
echo
echo "Changing wallpaper..."

cd /var/lib/fedora-wallpaper/
# Do some clean up
rm -rf *.jpg
rm -rf database
touch database

down_one_pic_set


while true; do
# Now we do a shuffle
select=`ls *.jpg|shuf -n1`
gsettings set org.gnome.desktop.background picture-uri file:///var/lib/fedora-wallpaper/$select

# Check if file exits in DB
grep  $select /var/lib/fedora-wallpaper/database

if [ $? -ne "0" ]; then
    # add new entry
    echo "$select 1" >> database
else

    # Increase counter
    # find counter first
    counter=$(grep $select database|awk '{print $NF}'|head -1)
    new_counter=$(echo $counter+1|bc -l)
    sed -i "s/.*$select.*/$select $new_counter/g" database
fi
    #current_pic= $(gsettings get org.gnome.desktop.background picture-uri|sed  "s-file://--g"|sed "s/'//g")
current_pic=$select
sleep $refresh_rate_s

#sleep 5
#### We delete old pic ####
del_old_pic $current_pic

#### Down load new pic ####
down_new_pic
done

}

function help_show () {
echo help

}

function error_show () {
echo "Unrecognised command argument"
echo "For help run: Fedora_wallpaper_changer.sh --help"

}

#-----------

           #------------ HELP MODE ------------ #
if [ $help ];then
        help_show ;
        exit ;

           #------------ Setup / Install MODE ------------ #
elif [ $setup ];then
        setup ;
        exit ;

           #------------ Run MODE ------------ #

elif [ $run ];then
        run ;
        exit ;
elif [ $error_show ];then
        error_show ;
        exit ;
fi

#!/bin/bash
# Author : Shatadru Bandyopadhyay
whattodo=$1
curr_vol=`amixer get Master|grep -i Playback|grep Left:|cut -f2 -d "[" |sed 's/\%]//g'`

if [ -z "$whattodo" ]
	then
	zenity --error --text "Expects 1 argument" --title "vol-control.sh"  2>/dev/null
	exit
else


	if [ $whattodo == "increase" ]
	then 
		set_vol=$(($curr_vol+20))
	elif [ $whattodo == "decrease" ]
	then
		set_vol=$(($curr_vol-20))
	elif [ $whattodo == "mute" ]
	then
		set_vol=0
	else
	zenity --error --text "Unexpected argument" --title "vol-control.sh"  2>/dev/null

	fi	
fi 

amixer set Master $set_vol%




#!/bin/bash

function rpmva(){
	echo 'Collecting "rpm -Va" '
#	rpm -Va 2> /dev/null  > /tmp/rpmva
	rpmva="/tmp/rpmva"
}
function missing_file_rpm(){
	rpm -qf $(cat $rpmva|grep -i missing|awk '{print $NF}' ) |sort|uniq > /tmp/rpms_which_has_file_missing
}
function changed_files_rpm(){
	rpm -qf $(cat $rpmva|egrep -iv "dependencies| g | c |missing"|grep [S,.][M,.][5,.]*[L,.]*[T,.].|awk  '{print $NF}' ) |sort|uniq > /tmp/rpms_which_has_file_changed
}
function check_fix(){
	echo "Do you want to fix $1? [y/n]"
	read a
	if [ "$a" == "Y" ] || [ "$a" == "y" ]  ;then
		$2
	else
		echo "Incorrect choice, exiting..." 
		exit
	fi
}

function fix_change () {
	dnf reinstall -y $(cat /tmp/rpms_which_has_file_missing)
}

function fix_missing () {
	dnf reinstall -y $(cat /tmp/rpms_which_has_file_changed)
}

rpmva
missing_file_rpm
changed_files_rpm

missing_file_rpm_num=$(wc -l /tmp/rpms_which_has_file_missing)
changed_files_rpm_num=$(wc -l /tmp/rpms_which_has_file_changed)

echo "number of rpms with files changed $changed_files_rpm_num="
check_fix "changed rpms" fix_change
check_fix "rpms with missing files" fix_missing


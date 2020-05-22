#!/bin/bash:

# Author : Shatadru Bandyopadhyay
#           shatadru1@gmail.com
# Supports : Fedora, Ubuntu (more to be added)
# Services tested so far : amazon.in
# Tested OS:  Fedora 30,31,32

# OBTAIN THE LATEST VERSION OF THE SCRIPT AT :  https://github.com/shatadru/simpletools/blob/master/otpgen.sh
#                       DIRECT DOWNLOAD LINK : https://raw.githubusercontent.com/shatadru/simpletools/master/otpgen.sh

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


export HOME=$(bash <<< "echo ~${SUDO_USER:-}")
os=""
fedora=0
ubunu=0
rhel=0
debian=0
args=( "$@" )
numarg=$#
argnum=$((numarg-1))
install=0
root=0
fail_install=0
tempdirname=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1`

function check_root(){
if [[ $EUID -ne 0 ]]; then
   install=0
   root=0
else
   install=1
   root=1
fi
}
function fatal_error() {
echo -e "\e[31m\e[1m Fatal Error \e[0m: $1"
exit 255
}

function warning() {
echo -e "\e[33m\e[1m Warning \e[0m: $1 "
}
function success() {
echo -e "\e[32m\e[1m Success \e[0m: $1 "
}
function check_version () {
SCRIPT=$(readlink -f "$0")
md5sum_local=$(md5sum $SCRIPT|awk '{print $1}')
mkdir -p /tmp/$tempdirname
curl -s -H 'Cache-Control: no-cache'  https://raw.githubusercontent.com/shatadru/simpletools/master/otpgen.sh > /tmp/$tempdirname/otpgen.sh

md5sum_remote=$(md5sum /tmp/$tempdirname/otpgen.sh|awk '{print $1}')

if [ "$md5sum_local" == "$md5sum_remote" ] ; then 
	success "The script is at latest available version"
else
	warning "Using older version of script"
	echo "Get latest source at https://github.com/shatadru/simpletools/blob/master/otpgen.sh"
fi

}
function pckg_check() {

        rpm -q $1 > /dev/null 2> /dev/null
        if [ "$?" -ne "0" ];then
                echo Package : $1 Not found...
                if [ "$install" == "1" ];then
                        echo "Installing $1 package....";echo
                        install_command $1;echo
                else
                        echo "Please install $1 package....";echo
                        print_command $1;echo
			fail_install=1
                fi
                        
        fi

}


function install_command(){

pckg=$1
case $os in

  fedora)
   dnf install $pckg -y
    ;;

  ubuntu)
   apt-get install $pckg -y
    ;;

  *)
    echo "Install $pckg"
    ;;
esac



}

function print_command(){

pckg=$1
case $os in

  fedora)
   echo "  # dnf install $pckg -y"
    ;;

  ubuntu)
   echo "  # apt-get install $pckg -y"
    ;;

  *)
    echo "Install $pckg"
    ;;
esac



}

function extract_secret_from_image() {
        img=$1
        secret=$(/usr/bin/zbarimg  $img 2> /dev/null|grep -i secret=|cut -f2 -d "="  |cut -f "1" -d "&")
        echo $secret
}



function detect_os() {
        os=$(cat /etc/os-release|grep -i ^id=|cut -f2 -d "=")

        if [ "$os" == "fedora" ]; then
                fedora=1

        elif [ "$os" == "ubuntu" ]; then
                ubuntu=1
        fi
}

function install_pckgs() {
        pckg_check oathtool
        pckg_check xclip
        pckg_check zbar
}
function install_main() {
	echo -en "Checking for required packages.";sleep 1; echo -en "." ; sleep 1 ; echo -en "."
        install_pckgs
	echo
	if [ "$fail_install" == "1" ];then
	fatal_error "Please install required packages before proceeding."
	fi
	if [ -d "$HOME/otpgen" ];then
        	fatal_error "otpgen Already installed. You can re-install using --clean-install"
	else
		echo "Creating required file"
        	mkdir -p $HOME/otpgen
        	touch  $HOME/otpgen/.secret_list
		success "Installation successful"
	fi
}

function add_key(){
image=$1
name=$2

if [ -z $image ]; then
        fatal_error "Image file not supplied, please add a image file containing QR Code"
fi

if [ ! -f $image ]; then
        fatal_error "File not found, cant add key..."
fi


        secret_val=$(extract_secret_from_image $image)
        num_lines=$(cat  $HOME/otpgen/.secret_list|wc -l)

        echo "$((num_lines+1)) $name $secret_val" >> $HOME/otpgen/.secret_list
        echo "Key added successfully"

}
function remove_key(){
all=$1
}

function list_keys() {
check_install
line=$(wc -l $HOME/otpgen/.secret_list |awk '{print $1}')
if [ $line == "0" ];
then 
	echo "No keys installed, use -a or --add-key to install"
else

	cat $HOME/otpgen/.secret_list|awk '{print $1,$2}'
fi
}
function check_install(){
if [ -d "$HOME/otpgen" ];then
        echo "otpgen installed"
	return 0
else
        fatal_error "Seems otpgen is not installed, please install using -i/--install"
	
fi
}


function clean_install(){
warning "This will remove all existing keys, Press any key to continue, Ctrl+C to exit ..."
read a
rm -rf $HOME/otpgen 
install_main
}



function gen_key() {

        index=$1
        if [ -z $index ]; then

                list_keys
                echo "Which key do you want to select?"
                read a
                secret=$(sed "${a}q;d" $HOME/otpgen/.secret_list|awk '{print $2}')
        else
                secret=$(sed "${index}q;d" $HOME/otpgen/.secret_list|awk '{print $2}')
        fi
        token=$(oathtool --base32 --totp "$secret")
        echo $token
	printf $token|xclip -sel clip


}

check_version
detect_os
check_root

# Command line arg handling...

for i in `seq 0 "$argnum"`
        do
        key=${args[$i]}
        key2=${args[$((i+1))]}
        key3=${args[$((i+2))]}

        case $key in
                -i|--install)
                        install_main
                ;;
                -a|--add-key)
                        add_key $key2 $key3
                ;;
                -r|--remove-key)

                        remove_key $key2
                ;;
                -l|--list-key)

                        list_keys
                ;;
                -c|--check-install)

                        check_install
                ;;

                --clean-install)

                        clean_install
		;;
                -g|--gen-key)
                        gen_key $key2
                ;;


                *)
                ;;
        esac
done

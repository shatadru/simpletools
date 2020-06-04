#!/bin/bash
# Author : Shatadru Bandyopadhyay
#           shatadru1@gmail.com
# Supports : Fedora, Ubuntu, Debian, RHEL  (more to be added including CentOS, Manjaro, Mint)
# Services tested so far : amazon.in
# Manually Tested OS:  Fedora 30-32, Ubuntu 18.04(container)

# CI test runs on: Fedora 32, Debian 10, Ubuntu 18.04, Ubuntu 20.04, RHEL 7.8

# OBTAIN THE LATEST VERSION OF THE SCRIPT AT :  https://github.com/shatadru/simpletools/blob/master/otpgen/otpgen.sh
#                       DIRECT DOWNLOAD LINK : https://raw.githubusercontent.com/shatadru/simpletools/master/otpgen/otpgen.sh

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



## Variable declarations :

version="0.5-5"

if [ -n "$SUDO_USER" ] ; then
        USER=$SUDO_USER
        export USER
else
        USER=$(whoami)
        export USER
fi

HOME=$(bash <<< "echo ~${SUDO_USER:-}")
export HOME
os=""
fedora=0
ubuntu=0
args=( "$@" )
numarg=$#
argnum=$((numarg-1))
install=0
root=0
fail_install=0
tempdirname=$(curl -s "https://www.random.org/strings/?num=1&len=8&digits=on&upperalpha=on&loweralpha=on&unique=on&format=plain&rnd=new")
if [ -z "$tempdirname" ]; then
	tempdirname=$(timeout 2 < /dev/urandom  tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1)
fi

if [ -z "$tempdirname" ]; then
	tempdirname=$(md5sum /proc/meminfo |tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1)
fi
qr_secret=""
qr_type=""
qr_issuer=""
qr_user=""

function print_help(){
	cat > /tmp/"$tempdirname"-help <<EOF
		
	otpgen.sh, otpgen:   2 Factor Authettication for Linux
              
                             This tool allows you to generate 2 step verification codes in Linux command line

			     Features:

				* Generate verification code offline
				* Support for both HOTP and TOTP based tokens
				* Automatic setup via QR Code
				* Add multiple accounts/keys, list and genetate keys
				* Supports : Fedora, Ubuntu, Debian, RHEL (more to be added including CentOS, Manjaro, Mint)

	Syntax:  ./otpgen.sh [-V|--version][-i|--install][--clean-install][-a|--add-key <path to image>] [-l|--list-key][-g|--gen-key]
         -V, --version       Print version
         
         -i, --install       Install otpgen.sh in system
                  
         --clean-install     Clean any local data and re-install
         
         -a, --add-key FILE  Add a new 2FA from image containing QR Code
         
         -l, --list-key      List all available 2FA stored in the system
         
         -g, --gen-key [ID]  Generate one time password
                             Passing ID is optional, else it will ask for ID
                             for which you want to generate OTP.       

Author     : Shatadru Bandyopadhyay(shatadru1@gmail.com)
Maintainer : Shatadru Bandyopadhyay(shatadru1@gmail.com)
License    : GPLv3

EOF
cat /tmp/"$tempdirname"-help

}
function print_version(){
    info "Version: $version"
}
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

function info() {
    echo -e "\e[34m\e[1m Info \e[0m: $1"
}
function warning() {
    echo -e "\e[33m\e[1m Warning \e[0m: $1 "
}
function success() {
    echo -e "\e[32m\e[1m Success \e[0m: $1 "
}
function check_version () {
    info "Checking for updates of otpgen.sh"
    SCRIPT=$(readlink -f "$0")
    md5sum_local=$(md5sum "$SCRIPT"|awk '{print $1}')
    mkdir -p /tmp/"$tempdirname"
    curl -s -H 'Cache-Control: no-cache'  https://raw.githubusercontent.com/shatadru/simpletools/master/otpgen/otpgen.sh > /tmp/"$tempdirname"/otpgen.sh 
    curl_error=$?
    
    if [ "$curl_error" == "0" ]; then

        md5sum_remote=$(md5sum /tmp/"$tempdirname"/otpgen.sh|awk '{print $1}')

        if [ "$md5sum_local" == "$md5sum_remote" ] ; then 
            success "The script is at latest available version"
        else
            warning "Using older version of script"
            info "Get latest source at https://github.com/shatadru/simpletools/blob/master/otpgen.sh"
        fi
    else    
        warning "Unable to get check for update, curl failed" 
        curl_error_meaning=$(man curl|grep -i -A176 "exit codes"|awk '$1=='$curl_error'{print}')
        echo " Curl Error: $curl_error_meaning" 
    fi

}
function pckg_check() {
if [ "$fedora" == "1" ] || [ "$rhel" == "1" ] ; then
	run_command="rpm -q"
elif [ "$ubuntu" == "1" ] || [ "$debian" == "1" ] ; then
	run_command="dpkg -l"
fi

        if ! $run_command "$1" > /dev/null 2> /dev/null ; then
                echo Package : "$1" Not found...
                if [ "$install" == "1" ];then
                        echo "Installing $1 package....";echo
                        install_command "$1";echo
                else
                        echo "Please install $1 package....";echo
                        print_command "$1";echo
                        info "If you have sudo priviledge you can run this command with sudo"
                        fail_install=1
                fi
                        
        fi

}


function install_command(){
    pckg=$1
    if [ "$fedora" == "1" ] ; then
        dnf install "$pckg" -y
    elif [ "$ubuntu" == "1" ] || [ "$debian" == "1" ]; then 
        apt-get install "$pckg" -y
    elif [ "$rhel" == "1" ]; then
	yum install "$pckg" -y
    else
 	   info "Install $pckg in your distro"
	   fail_install=1
    fi
}

function print_command(){
    pckg=$1
    if [ "$fedora" == "1" ] ; then
        info "  # dnf install $pckg -y"
    elif [ "$ubuntu" == "1" ] || [ "$debian" == "1" ] ; then 
        info "  # apt-get install $pckg -y"
    elif [ "$rhel" == "1" ] ; then
        info "  # yum install $pckg -y"
    else
  	  echo "Install $pckg in your distro"
    fi    
}

function urldecode() { : "${*//+/ }"; echo -e "${_//%/\\x}"; }


function extract_secret_from_image() {
        img=$1
    out=$(/usr/bin/zbarimg  "$img"  2> /tmp/."$tempdirname"-error)
    zbar_exit=$?
    if [ "$zbar_exit" ==  "0" ]; then 
        
        decode=$(urldecode "$out")
            qr_secret=$(echo "$decode"|grep -i secret=|cut -f2 -d "="  |cut -f "1" -d "&")
        qr_issuer=$(echo "$decode"|grep -i secret=|grep -io "issuer.*"|cut -f2 -d "="|sed 's/ /_/g')
        qr_user=$(echo "$decode"|grep -i secret=|cut -f4 -d "/"|cut -f2 -d ":"|cut -f1 -d "?")
        qr_type=$(echo "$decode"|grep -i secret=|cut -f3 -d "/")
        
            return 0
    elif [ "$zbar_exit" ==  "1" ]; then
        echo "An error occured while processing image";echo
        cat /tmp/."$tempdirname"-error
        fatal_error "An error occurred while processing some image(s). This includes bad arguments, I/O errors and image handling errors from ImageMagick."
    elif [ "$zbar_exit"  ==  "2" ]; then
        echo "An error occured while processing image";echo
        cat /tmp/."$tempdirname"-error
        fatal_error "ImageMagick fatal error."
        return 1
    elif [ "$zbar_exit"  ==  "4" ]; then
        echo "An error occured while processing image";echo
        cat /tmp/."$tempdirname"-error
        fatal_error "No barcode was detected in supplied image.."
        return 1
    else 
        fatal_error "Unhandled error from zbarimg while processing image"
        return 1
    fi
}



function detect_os() {
        os=$(grep -i ^id= /etc/os-release|cut -f2 -d "="|sed  's/"//g' | sed  "s/'//g" )

        if [ "$os" == "fedora" ]; then
                fedora=1

        elif [ "$os" == "ubuntu" ]; then
                ubuntu=1
	elif [ "$os" == "debian" ]; then
		debian=1
	elif [ "$os" == "rhel" ]; then
		rhel=1
	else
		warning "OS Not supported, might not work correctly"
        fi
}

function install_pckgs() {
        pckg_check oathtool
        pckg_check xclip
	if [ "$fedora" == "1" ]; then
	    pckg_check zbar
        elif [ "$ubuntu" == "1" ]; then 
	    pckg_check zbar-tools
	fi
}
function install_main() {
    echo -en "Checking for required packages.";sleep .3; echo -en "." ; sleep .3 ; echo -en "."
        install_pckgs
    echo
    if [ "$fail_install" == "1" ];then
        fatal_error "Please install required packages before proceeding."
    fi
    if [ -d "$HOME/otpgen" ];then
            fatal_error "otpgen Already installed. You can re-install using --clean-install"
    else
        echo "Creating required files"
            mkdir -p "$HOME"/otpgen||failed=1
        touch  "$HOME"/otpgen/.secret_list||failed=1
            chown -R "$USER":"$USER" "$HOME"/otpgen||failed=1
        if [  -z "$failed" ]; then
            success "Installation successful"
        else
            fatal_error "Unhandled Error, probably permission issues(?), You can re-install using --clean-install"
        fi
    fi
}

function add_key(){
    image=$1
    name=$2

    if [ -z "$image" ]; then
            fatal_error "Image file not supplied, please add a image file containing QR Code"
    fi

    if [ ! -f "$image" ]; then
            fatal_error "File not found, cant add key..."
    fi

    echo -en "Detecting QR Code from supplied image.";sleep .3; echo -en "." ; sleep .3 ; echo -en "."; echo
    extract_secret_from_image "$image"
    exit_stat=$?

    if [ "$exit_stat" != "0" ]; then
        fatal_error "Failed to detect usable QR Code..."

    fi 

    if [ "$qr_type" == "totp" ]; then
        info "TOTP token detected"
    elif [ "$qr_type" == "hotp" ]; then
        info "HOTP token detected"
    else
        fatal_error "OTP type unsupported! Only TOTP and HOTP are supported"
    fi
    secret_val=$qr_secret
    last_key_id=$(tail -1 "$HOME"/otpgen/.secret_list|awk '{print $1}')
    if [ "$qr_type" == "hotp" ] ; then
        echo "$((last_key_id+1)) $name $secret_val  $qr_type  $qr_issuer  $qr_user 0" >> "$HOME"/otpgen/.secret_list|| fatal_error "Failed to add key, try using sudo or check file permission" && success "Key added successfully"
    else
        echo "$((last_key_id+1)) $name $secret_val  $qr_type  $qr_issuer  $qr_user" >> "$HOME"/otpgen/.secret_list||fatal_error "Failed to add key, try using sudo or check file permission" && success "Key added successfully"
    fi
}

function remove_key(){
    fatal_error "Feature is not implemented yet...."
}

function list_keys() {
    check_install
    line=$(wc -l "$HOME"/otpgen/.secret_list |awk '{print $1}')
    if [ "$line" == "0" ];
    then 
        info "No keys installed, use -a or --add-key to install"
    else
        echo "ID Secret  TYPE  ISSUER  USER Counter(HOTP)"|awk '{printf "%2s %30s %6s %20s %30s %20s \n", $1,$2,$3,$4,$5,$6}'

        awk '{printf "%2s %30s %6s %20s %30s %20s \n", $1,"••••••••••••••••••",$3,$4,$5,$6}' "$HOME"/otpgen/.secret_list

    fi
}
function check_install(){
if [ -d "$HOME/otpgen" ];then
        info "otpgen installed"
    return 0
else
        fatal_error "Seems otpgen is not installed, please install using -i/--install"
    
fi
}


function clean_install(){
    warning "This will remove all existing keys, Press any key to continue, Ctrl+C to exit ..."
    read -r a
    rm -rf "$HOME"/otpgen || fatal_error "Unable to run command #rm -rf $HOME/otpgen, try with sudo or run this from root user #rm -rf $HOME/otpgen "
    install_main
}



function gen_key() {

        index=$1
        if [ -z "$index" ]; then

                list_keys
                echo "Which key do you want to select?"
                read -r a
        index=$a
        fi
    no_lines_selected=$(awk -v i="$index" '$1==i {print}' "$HOME"/otpgen/.secret_list|wc -l)
    if [ "$no_lines_selected" != "1" ];then
        fatal_error "Unable to generate key for ID: $index, check if ID is correct, run ./otpgen.sh -l to list all keys"
    fi
        secret=$(awk -v i="$index" '$1==i {print $2}' "$HOME"/otpgen/.secret_list)
        token_type=$(awk -v i="$index" '$1==i {print $3}' "$HOME"/otpgen/.secret_list)
        counter=$(awk -v i="$index" '$1==i {print $6}' "$HOME"/otpgen/.secret_list)
     
    if [ "$token_type" == "totp" ] ; then     
            token=$(oathtool --base32 --totp "$secret")
        else
        token=$(oathtool --base32 -c "$counter" --hotp "$secret")
        counter=$((counter+1))
        awk -v i="$index" -v c="$counter" '$1==i{$6=c}{print}' /home/the_flash/otpgen/.secret_list > /tmp/."$tempdirname"-newhotp
        line_changes=$(sdiff -s  /tmp/."$tempdirname"-newhotp /home/the_flash/otpgen/.secret_list| wc -l)
        if [ "$line_changes" == "1" ]; then
            mv  /tmp/."$tempdirname"-newhotp /home/the_flash/otpgen/.secret_list || fatal_error "Error while incrementing HOTP counter, report this issue @ https://github.com/shatadru/simpletools/issues"
        else
            fatal_error "Error while incrementing HOTP counter, bug detected, report this issue @ https://github.com/shatadru/simpletools/issues"
        fi
        
    fi
    success "OTP : $token"
    printf "%s" "$token"|xclip -sel clip && success "OTP has been copied to clipboard, Ctrl+V to paste"


}

check_version
detect_os
check_root
if [ "$root" == 1 ];then
    info "Running with root priviledge"
else
    info "Running without root priviledge"
fi

# Command line arg handling...

for i in $(seq 0 "$argnum"); do
        key=${args[$i]}
        key2=${args[$((i+1))]}
        key3=${args[$((i+2))]}

        case $key in
                -i|--install)
                        install_main
                ;;
                -a|--add-key)
                        add_key "$key2" "$key3"
                ;;
                -r|--remove-key)

                        remove_key "$key2"
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
                -V|--version)

                        print_version
                ;;
                -g|--gen-key)
                        gen_key "$key2"
                ;;
		-h|--help)
			print_help
		;;

                *)
                ;;
        esac
done

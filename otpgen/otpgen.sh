#!/bin/bash
# Author : Shatadru Bandyopadhyay
#           shatadru1@gmail.com
# Supports : Fedora, Ubuntu, Debian, RHEL  (more to be added including CentOS, Manjaro, Mint)
#            should work in most RPM or DPKG based distros
#            Open github issue to add Distro support
# Services tested so far : amazon.in, gmail.com, facebook.com
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

version="0.7-2"

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
args=( "$@" )
numarg=$#
argnum=$((numarg-1))
install=0
root=0
fail_install=0
debug_var=""
debug=2
tempdirname=$(timeout 2 < /dev/urandom  tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1)
if [ -z "$tempdirname" ]; then
	# This can slow down the script
	tempdirname=$(curl -s "https://www.random.org/strings/?num=1&len=8&digits=on&upperalpha=on&loweralpha=on&unique=on&format=plain&rnd=new")
fi

if [ -z "$tempdirname" ]; then
	tempdirname=$(md5sum /proc/meminfo |tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1)
fi

mkdir -p /tmp/."$tempdirname"
qr_secret=""
qr_type=""
qr_issuer=""
qr_user=""
base_dir="$HOME/otpgen"
keystore_file="$base_dir/.secret_list"

function debug(){
debug_var="$1"
case "$debug_var" in
0)
  echo "Warning, this will supress error message"
  debug=0
  ;;
1)
  echo "Warning, this will supress warning message"
  debug=1
  ;;
2)
  debug=2
  ;;
3)
  debug=3
  ;;
4)
  debug=4
  ;;
*)
  debug=3
  ;;
esac

}
function print_help(){
	cat > /tmp/."$tempdirname"/helpfile <<EOF
		
	otpgen.sh, otpgen:   2 Factor Authettication for Linux
              
                             This tool allows you to generate 2 step verification codes in Linux command line

			     Features:

				* Generate verification code offline
				* Support for both HOTP and TOTP based tokens
				* Automatic setup via QR Code
				* Add multiple accounts/2FA, list, remove and genetate 2FA tokens
				* Supports : Fedora, Ubuntu, Debian, RHEL (more to be added including CentOS, Manjaro, Mint)
                                * CI tests all features automatically for all supported distro

	Syntax:  ./otpgen.sh [-V|--version] [-d|--debug level] [-s] [-i|--install] [--clean-install] [-a|--add-key <path to image>] [-l|--list-key] [-g|--gen-key] [-r|--remove-key]

         -V, --version       Print version
         
         -i, --install       Install otpgen.sh in system
                  
         --clean-install     Clean any local data and re-install
         
         -a, --add-key FILE  Add a new 2FA from image containing QR Code
         
         -l, --list-key      List all available 2FA stored in the system
         
         -g, --gen-key [ID]  Generate one time password
                             Passing ID is optional, else it will list all 2FA and ask for ID
                             for which you want to generate OTP. 
         -r  [ID]	     Remove a 2FA token from keystore 
          --remove-key [ID]  Passing ID is optional, else it will list all 2FA and ask for ID
                             for which one you would like to remove
         -d, --debug [debug level]  
                             Determines debug level, Prints messages which 
                             is greater than or equal to debug level
                             
                             4: Debug
                             3: Info 
                             2: Warning (Default)
                             1: Error
                             0: Silent
         -s, --silent        Same as "--debug 0"

Author     : Shatadru Bandyopadhyay(shatadru1@gmail.com)
Maintainer : Shatadru Bandyopadhyay(shatadru1@gmail.com)
License    : GPLv3
Link       :  https://github.com/shatadru/simpletools
EOF
cat /tmp/."$tempdirname"/helpfile

}
function print_version(){
    debug=4
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
    if [ "$debug" -ge 1 ];then
    echo -e "\e[31m\e[1m Fatal Error \e[0m: $1"
    fi
    cleanup
    exit 255
}

function info() {
    if [ "$debug" -ge 3 ];then
    	echo -e "\e[34m\e[1m Info \e[0m: $1"
    fi
}
function warning() {
    if [ "$debug" -ge 2 ];then
   	 echo -e "\e[33m\e[1m Warning \e[0m: $1 "
    fi
}
function success() {
    echo -e "\e[32m\e[1m Success \e[0m: $1 "
}
function question() {
    echo -e "\e[1m\e[96m\e[1m Question \e[0m: $1 "
}
function check_version () {
    # Only check update once a day
    # Check if update check was performed recently
    check_update_cache=$(find "$HOME"/otpgen/ -mtime +1 -name .check_update 2> /dev/null|wc -l)
    if [ ! -f "$HOME"/otpgen/.check_update ] || [ "$check_update_cache" == "1" ]; then
    
    info "Checking for updates of otpgen.sh"
    SCRIPT=$(readlink -f "$0")
    md5sum_local=$(md5sum "$SCRIPT"|awk '{print $1}')
    curl -s -H 'Cache-Control: no-cache'  https://raw.githubusercontent.com/shatadru/simpletools/master/otpgen/otpgen.sh > /tmp/."$tempdirname"/otpgen.sh 
    curl_error=$?
    
    if [ "$curl_error" == "0" ]; then

        md5sum_remote=$(md5sum /tmp/."$tempdirname"/otpgen.sh|awk '{print $1}')

        if [ "$md5sum_local" == "$md5sum_remote" ] ; then 
            success "The script is at latest available version"
        else
            warning "Using older version of script"
            info "Get latest source at https://github.com/shatadru/simpletools/blob/master/otpgen.sh"
        fi
	    touch "$HOME"/otpgen/.check_update
    else    
        warning "Unable to get check for update, curl failed" 
        curl_error_meaning=$(man curl|grep -i -A176 "exit codes"|awk '$1=='$curl_error'{print}')
        echo " Curl Error: $curl_error_meaning" 
    fi

   else
	info "Skipping update check, this is only done once a day..."

fi

}
function pckg_check() {
if [ "$package_manager" == "yum" ] ; then
	run_command="rpm -q"
elif [ "$package_manager" == "apt-get" ] ; then
	run_command="dpkg -l"
fi

        if ! $run_command "$1" > /dev/null 2> /dev/null ; then
                echo Package : "$1" Not found...
                if [ "$install" == "1" ];then
			echo "Do you want to install $1? Press any key to continue, ctrl+c to exit" ; read -r a ;
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
    if [  "$package_manager" == "yum" ] ; then
	if type -p dnf > /dev/null 2> /dev/null; then
		alias yum='dnf'
	fi
        yum install "$pckg" -y && info "$pckg was successfully installed" || fail_install=1
    elif [ "$package_manager" == "apt-get" ]; then 
        apt-get install "$pckg" -y  && info "$pckg was successfully installed"  || fail_install=1
    else
 	   info "Install $pckg in your distro"
	   fail_install=1
    fi
}

function print_command(){
    pckg=$1
    if [  "$package_manager" == "yum" ] ; then
	if type -p dnf ; then
	package_manager='dnf'
	fi
        info "  # $package_manager install $pckg -y"
    else
  	  echo "Install $pckg in your distro"
    fi    
}

function urldecode() { : "${*//+/ }"; echo -e "${_//%/\\x}"; }


function extract_secret_from_image() {
        img=$1
    out=$(/usr/bin/zbarimg  "$img"  2> /tmp/."$tempdirname"/error)
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
        cat /tmp/."$tempdirname"/error
        fatal_error "An error occurred while processing some image(s). This includes bad arguments, I/O errors and image handling errors from ImageMagick."
    elif [ "$zbar_exit"  ==  "2" ]; then
        echo "An error occured while processing image";echo
        cat /tmp/."$tempdirname"/error
        fatal_error "ImageMagick fatal error."
        return 1
    elif [ "$zbar_exit"  ==  "4" ]; then
        echo "An error occured while processing image";echo
        cat /tmp/."$tempdirname"/error
        fatal_error "No barcode was detected in supplied image.."
        return 1
    else 
        fatal_error "Unhandled error from zbarimg while processing image"
        return 1
    fi
}
function encrypt(){
	out=$(echo "$1"  | openssl enc -aes-256-cbc -md sha512 -pbkdf2 -iter 100000 -salt -k "$happy" -out "$keystore_file" -base64  2> /tmp/."$tempdirname"/encrypt_error )  || out="Encryption failed"
        if [[ "$out" =~ .*"Encryption failed".* ]];then
                    if [ $debug -ge 4 ]; then
                        out+="Output of openssl command:\n"
                        out+="-----------------------------\n"
                        out+=$(cat /tmp/."$tempdirname"/encrypt_error)
                        out+="\n-----------------------------\n"
                    fi
                    echo "$out"
                return 1
        else
		echo "$out"
                return 0
        fi


}
function decrypt(){
	out=$(openssl enc  -aes-256-cbc -md sha512 -pbkdf2 -iter 100000 -d -k "$happy" -in "$keystore_file" -base64  2> /tmp/."$tempdirname"/decrypt_error  )  || out="Decryption failed, please re-check your password and try again"
	if [[ "$out" =~ .*"Decryption failed".* ]];then
		    if [ $debug -ge 4 ]; then
			out+="\nOutput of openssl command:\n"
        		out+="-----------------------------\n"
        		out+=$(cat /tmp/."$tempdirname"/decrypt_error)
        		out+="\n-----------------------------\n"
    		    fi
		    echo "$out"
		return 1
	else
		echo "$out"
		return 0
	fi

}

function ask_pass(){
mode="$1"
if [ "$mode" == "create" ];
	then
	question "Enter a stong password which will be used to encrypt your tokens..."
	read -rs happy
	question "Re-enter the password again to verify"
	read -rs toohappy
else 
	question "Enter keystore password: "
	read -rs happy
fi
}
function check_pass(){
    info "Tesing password strength..."
    okay=$(/usr/sbin/cracklib-check<<<"$1" |awk -F': ' '{ print $2}')
    if [[ "$okay" == "OK" ]]; then
	success "Password accepted... Do not loose this password"
	return 0
    else
	warning "Your password was rejected - $okay, Try again"
	return 1
    fi
}


function detect_os() {
	os=$(uname -s)
	case "$os" in
        SunOS)    os=Solaris ;;
        MINIX)    os=MINIX ;;
        AIX)      os=AIX ;;
        IRIX*)    os=IRIX ;;
        FreeMiNT) os=FreeMiNT ;;

        Linux|GNU*)
            os=Linux
        ;;

        *BSD|DragonFly|Bitrig)
            os=BSD
        ;;

        CYGWIN*|MSYS*|MINGW*)
            os=Windows
        ;;

        *)
            warning "Unknown OS detected: $os aborting..." 
            fatal_error "Open an issue on GitHub to add support for your OS." 
        ;;
       esac

	if [ "$os" != "Linux" ]; then
		fatal_error "$os is not supported, Open an issue on GitHub to add support for your OS."
	fi

	if [ -f /etc/os-release ] ||  [ -f /etc/lsb-release ]; then
		os=$(grep -i ^id= /etc/os-release|cut -f2 -d "="|sed  's/"//g' | sed  "s/'//g" )
		os_like=$(grep -i ^id_like= /etc/os-release|cut -f2 -d "="|sed  's/"//g' | sed  "s/'//g" )
	fi
        if [ "$os" == "fedora" ] || [ "$os_like" == "fedora" ]; then
                package_manager="yum"
        elif [ "$os" == "debian" ] || [ "$os_like" == "debian" ]; then
                package_manager="apt-get"
	#elif [ "$os" == "arch" ] || [ "$os_like" == "arch" ]; then
	#	package_manager="pacman"
	
	else
		fatal_error "Distro is not supported right now, Open an issue on GitHub to add support for your Distro."
        fi
}

function install_pckgs() {
        pckg_check oathtool ## requires for OTP generation
	pckg_check openssl ## requires for encryption
        pckg_check xclip ## Requires to copy the token in clipboard
	if [ "$package_manager" == "yum" ]; then
	    pckg_check zbar  ## Requires for reading QR code from image
	    pckg_check cracklib
        elif [ "$package_manager" == "apt-get" ]; then 
	    pckg_check zbar-tools
	    pckg_check libcrack2
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
        ask_pass "create"
        while(true); do
		
    		if [ "$happy" != "$toohappy" ]; then
    			warning "Passwords do not match! Try again"
			ask_pass "create"
			continue
		else
			
        		if check_pass "$happy"  ; then
	        		break
			else
				ask_pass "create"
				continue
			fi
    		fi
    	done
	info "Creating encrypted secret store..."
    	out=$(encrypt "" ) || fatal_error "Key store creation failed... $out "    
	    if type -p stat 2> /dev/null > /dev/null ; then
		cur_user=$(stat -c '%U'  "$HOME"/otpgen)
	    else
		cur_user=$(find "$HOME"/otpgen -type d -printf "%g" )
	    fi
	    if [ "$cur_user" != "$USER" ]; then
	            chown -R "$USER":"$USER" "$HOME"/otpgen||failed=1
	    fi
        if [  -z "$failed" ]; then
            success "Installation successful"
        else
            fatal_error "Unhandled Error, probably permission issues(?), You can re-install using --clean-install"
        fi
    fi
}
function remove_image(){
	img_file=$1
	warning "The image contains your secret for OTP generation, you should delete this file as 2FA has been added"
	echo "Do you want to delete the image? [Y/N]"
	read -r answer
	if [ "$answer" == "y" ]|| [ "$answer" == "Y" ]; then
		rm -f "$img_file" || warning "Delete failed, try deleting manually"
	else
		info "Setting chmod 000 to restrict unwanted access"
		chmod 000 "$img_file"
		warning "This file can reveal your secret, consider deleting it.($img_file)"
	fi
}
function add_key(){
    image=$1

    if [ -z "$image" ]; then
            fatal_error "Image file not supplied, please add a image file containing QR Code"
    fi

    if [ ! -f "$image" ]; then
            fatal_error "File not found, cant add 2FA..."
    fi

    echo -en "Detecting QR Code from supplied image.";sleep .3; echo -en "." ; sleep .3 ; echo -en "."; echo

    if ! extract_secret_from_image "$image" ; then
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
    # Decrypt file before adding password
    ask_pass
    out=$(decrypt)||fatal_error "$out"
    check_dups=$(echo -n "$out"|grep  $qr_issuer|grep  $qr_user|grep "$secret_val"|grep "$qr_type")
    if [ ! -z "$check_dups" ]; then
	
	warning "2FA is already added in keystore..."
	echo "ID Secret  TYPE  ISSUER  USER Counter(HOTP)"|awk '{printf "%2s %30s %6s %20s %30s %20s \n", $1,$2,$3,$4,$5,$6}'
        echo "$check_dups" | awk '{printf "%2s %30s %6s %20s %30s %20s \n", $1,"••••••••••••••••••",$3,$4,$5,$6}'
    	fatal_error "Not adding duplicate entry..."
    fi
    last_key_id=$(echo -n "$out"|tail -1|awk '{print $1}')
    if [ "$qr_type" == "hotp" ] ; then
        new_line="$((last_key_id+1))  $secret_val  $qr_type  $qr_issuer  $qr_user 0"
    else
	new_line="$((last_key_id+1))  $secret_val  $qr_type  $qr_issuer  $qr_user"
    fi
read -r -d "" var << EOM
$out
$new_line
EOM
if  encrypt "$var" ; then
	 success "New 2FA added successfully" 
#    remove_image "$image"

else
	 fatal_error "Failed to add 2FA, Wrong password?"
fi
}

function remove_key(){
    #fatal_error "Feature is not implemented yet...."
    ask_pass
    out=$(decrypt)||fatal_error "$out"
        index=$1
        if [ -z "$index" ]; then
                list_keys
                echo "Which 2FA do you want to select?"
                read -r a
        index=$a
        fi
    no_lines_selected=$(echo "$out"|awk -v i="$index" '$1==i {print}'|wc -l)
    if [ "$no_lines_selected" != "1" ];then
        fatal_error "Unable to find a 2FA with ID: $index, check if ID is correct, run ./otpgen.sh -l to list all 2FA"
    else
	newotp=$(echo "$out"|sed "/^$index /d")
	line_changes=$(sdiff -s  <(echo  "$newotp") <(echo  "$out")| wc -l)
        if [ "$line_changes" == "1" ]; then
		question "Are you sure you want to 2FA with ID: $index? Press Enter to continue, Ctrl+C to exit ..."
		read -r a
		if  encrypt "$newotp" ; then
        		 success "2FA removed successfully"
		else
         		fatal_error "Failed to remove 2FA, Wrong password?"
		fi
	else
		fatal_error "Bug detected, report this issue @ https://github.com/shatadru/simpletools/issues"
	fi
fi

}

function list_keys() {
    check_install
    # Decrypt the secret file
    ask_pass
    out=$(decrypt)||fatal_error "$out"
    line=$(echo "$out"|wc -l|awk '{print $1}')
   	
    if [ -z "$out" ] || [ "$line" == "0" ];
    then 
        warning "No 2FA found in keystore, use -a or --add-key to add new 2FA"
    else
        echo "ID Secret  TYPE  ISSUER  USER Counter(HOTP)"|awk '{printf "%2s %30s %6s %20s %30s %20s \n", $1,$2,$3,$4,$5,$6}'

        echo "$out" | awk '{printf "%2s %30s %6s %20s %30s %20s \n", $1,"••••••••••••••••••",$3,$4,$5,$6}'

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
    warning "This will remove all existing 2FA, Press Enter to continue, Ctrl+C to exit ..."
    read -r a
    rm -rf "$HOME"/otpgen || fatal_error "Unable to run command #rm -rf $HOME/otpgen, try with sudo or run this from root user #rm -rf $HOME/otpgen "
    install_main
}



function gen_key() {
	## Decrypt the secret file
    ask_pass
    out=$(decrypt)||fatal_error "$out"

        index=$1
        if [ -z "$index" ]; then

                list_keys
                echo "Which 2FA do you want to select?"
                read -r a
        index=$a
        fi
    no_lines_selected=$(echo "$out"|awk -v i="$index" '$1==i {print}'|wc -l)
    if [ "$no_lines_selected" != "1" ];then
        fatal_error "Unable to generate 2FA token for ID: $index, check if ID is correct, run ./otpgen.sh -l to list all 2FA"
    fi
        secret=$(echo "$out"|awk -v i="$index" '$1==i {print $2}' )
        token_type=$(echo "$out"|awk -v i="$index" '$1==i {print $3}')
        counter=$(echo "$out"|awk -v i="$index" '$1==i {print $6}')
     
    if [ "$token_type" == "totp" ] ; then     
            token=$(oathtool --base32 --totp "$secret")
        else
        token=$(oathtool --base32 -c "$counter" --hotp "$secret")
        counter=$((counter+1))
        newotp=$(echo "$out"|awk -v i="$index" -v c="$counter" '$1==i{$6=c}{print}' )
        line_changes=$(sdiff -s  <(echo  "$newotp") <(echo  "$out")| wc -l)
        if [ "$line_changes" == "1" ]; then
	encrypt "$newotp" || fatal_error "Error increamenting token, this token might not work! bug detected, report this issue @ https://github.com/shatadru/simpletools/issues"

        else
            fatal_error "Error while incrementing HOTP counter, bug detected, report this issue @ https://github.com/shatadru/simpletools/issues"
        fi
        
    fi
    success "OTP : $token"
    if [[ $(printf "%s" "$token" |xclip -sel clip 2> /dev/null ) ]]; then
	 success "OTP has been copied to clipboard, Ctrl+V to paste" 
    else

	warning "OTP was not copied in clipboard, *NOTE* this does not work via ssh"
    fi

}
# Cleanup tempfiles
function cleanup(){
	if [ -n "$tempdirname" ]; then
 		rm -rf /tmp/."$tempdirname"/
 	fi
}


### Parse debug level cmdline args
for i in $(seq 0 "$argnum"); do
        key=${args[$i]}
        key2=${args[$((i+1))]}
        case $key in
		-d|--debug)
                        debug "$key2"
                ;;
		-s|--silent)
                        debug 0 
                ;;
                *)
                ;;
        esac
done

check_version
detect_os
check_root
if [ "$root" == 1 ];then
    info "Running with root priviledge"
else
    info "Running without root priviledge"
fi


# Parse command line arguments
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


# Command line arg handling...
cleanup

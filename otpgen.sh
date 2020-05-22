#!/bin/bash:

# Author : Shatadru Bandyopadhyay
#           shatadru1@gmail.com
# Supports : ubuntu, debian, Fedora, RHEL
# Services tested so far
# amazon.in + Fedora 30

os=""
fedora=0
ubunu=0
rhel=0
debian=0
args=( "$@" )
numarg=$#
argnum=$((numarg-1))
install=""

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
   echo "dnf install $pckg -y"
    ;;

  ubuntu)
   echo "apt-get install $pckg -y"
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
        install_pckgs
        mkdir -p $HOME/otpgen
        touch  $HOME/otpgen/.secret_list
}

function add_key(){
image=$1
name=$2

if [ -z $image ]; then
        echo "Image file not supplied, please add a image file containing QR Code"
        exit
fi

if [ ! -f $image ]; then
        echo "Image not found, cant add key..."
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
        echo "Seems otpgen installed"
else
        echo "Seems otpgen is not installed"
fi
}


function clean_install(){
echo "This will remove all existing keys, Press any key to continue, Ctrl+C to exit ..."
read a
mv $HOME/otpgen /var/tmp
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


detect_os


# Command line arg handling...

for i in `seq 0 "$argnum"`
        do
        key=${args[$i]}
        key2=${args[$((i+1))]}
        key3=${args[$((i+2))]}

        case $key in
                -i|--install)
                        install=1
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

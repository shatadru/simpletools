# Check for duplicate rpm and remove them ....
#  skips glibc, kernel or gpg-pubkey

verbose=0
verbose=0
# Command line arg handling #

args=( "$@" )
numarg=$#
argnum=$((numarg-1))

for i in `seq 0 "$argnum"`
	do
	key=${args[$i]}
	case $key in
    		-h|--help)

			help="1"
		;;
    		-d|--dry-run)

			dryrun="1"
		;;
		-v|--verbose)

			verbose="1"
		;;

 		*)
    		;;
	esac
done



for i in $(rpm -qa --qf "%{name}.%{arch}\n"|sort |uniq|egrep -iv "kernel|glibc|gpg-pubkey" ) ; 
  do  
  count=`rpm -q $i|wc -l`; 
  if [ $count -gt 1 ]; then 
    echo "dups detected: $i" ;
    echo ------------- ; 
    rpm=`rpm -q $i|sort|head -1` ; 
    if [ "$dryrun" == "1" ]; then
      
      echo "Listing duplicates for $i ..."  ; 
      rpm -q $i; echo ---------------   ;      
      echo "$rpm will be removed"
      echo "============================"
    else
      echo "Attempting to remove $rpm ..." ; 
      rpm -ev --nodeps $rpm && echo "$rpm removed successfully" || echo "$rpm remove failed"; 
      echo "Checking list after removal..."  ; 
      rpm -q $i; 
      echo "============================"

    fi
  else 
    if [ "$verbose" == "1" ]; then
      echo "No dups found: $i" ; 
      echo -------------------; 
    fi
  fi 
  done

    if [ "$dryrun" == "0" ] ||  ; then
	echo "Running package-cleanup --dupes after cleanup..."
	package-cleanup --dupes
    fi


# Check for duplicate rpm and remove them ....
#  skips glibc, kernel or gpg-pubkey

verbose=0;
if [ "$1" == "-v" ];then
verbose=1;
fi

for i in $(rpm -qa --qf "%{name}.%{arch}\n"|sort |uniq|egrep -iv "kernel|glibc|gpg-pubkey" ) ; 
  do  
  count=`rpm -q $i|wc -l`; 
  if [ $count -gt 1 ]; then 
    echo "dups detected: $i" ;
    echo ------------- ; 
    rpm=`rpm -q $i|sort|head -1` ; 
    echo "Attempting to remove $rpm ..." ; 
    rpm -ev --nodeps $rpm && echo "$rpm removed successfully" || echo "$rpm remove failed"; 
    echo "Checking list after removal..." $i ; 
    rpm -q $i; echo ---------------   ; 
  else 
    if [ "$verbose" == "1" ]; then
      echo "No dups found: $i" ; 
      echo -------------------; 
    fi
  fi 
  done

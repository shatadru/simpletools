#!/bin/bash:

# Author : Shatadru Bandyopadhyay
#           shatadru1@gmail.com

# OBTAIN THE LATEST VERSION OF THE SCRIPT AT :  https://github.com/shatadru/simpletools/blob/master/fix_dup_rpm.sh
#                       DIRECT DOWNLOAD LINK : https://raw.githubusercontent.com/shatadru/simpletools/master/fix_dup_rpm.sh
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

# Check for duplicate rpm and remove them ....
#  skips glibc, kernel or gpg-pubkey

verbose=0
verbose=0
count_dup=0
count_rm=0

# Command line arg handling #
tempdirname=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1`
mkdir /tmp/$tempdirname/
DIR="/tmp/$tempdirname"
FILENAME="rpm-dup.txt"

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
    echo "dups detected: $i" |tee -a $DIR/$FILENAME  ;
    count_dup=$((count_dup+1))
    echo ------------- |tee -a $DIR/$FILENAME ;
    rpm=`rpm -q $i|sort|head -1` ;
    if [ "$dryrun" == "1" ]; then

      echo "Listing duplicates for $i ..."  |tee -a $DIR/$FILENAME ;
      rpm -q $i |tee -a $DIR/$FILENAME ;
      echo ---------------   |tee -a $DIR/$FILENAME ;
      echo "$rpm will be removed" |tee -a $DIR/$FILENAME
      echo "============================" |tee -a $DIR/$FILENAME
    else
      echo "Attempting to remove $rpm ..." |tee -a $DIR/$FILENAME ;
      count_rm=$((count_rm+1))
      rpm -ev --nodeps $rpm && echo "$rpm removed successfully"|tee -a $DIR/$FILENAME  || echo "$rpm remove failed"|tee -a $DIR/$FILENAME ;
      echo "Checking list after removal..."  |tee -a $DIR/$FILENAME ;
      rpm -q $i |tee -a $DIR/$FILENAME ; 
      echo "============================"|tee -a $DIR/$FILENAME ; 

    fi
  else
    if [ "$verbose" == "1" ]; then
      echo "No dups found: $i" |tee -a $DIR/$FILENAME ;
      echo -------------------|tee -a $DIR/$FILENAME ;
    fi
  fi
  done

    if [ "$dryrun" == "0" ]   ; then
        echo "Running package-cleanup --dupes after cleanup..."|tee -a $DIR/$FILENAME
        package-cleanup --dupes|tee -a $DIR/$FILENAME
    fi
echo
echo "Summary"
echo "-----------"
echo "Found $count_dup duplicate rpm(s)"
if [ "$dryrun" == "1" ]   ; then
	echo "DRY RUN MODE: No changes has been performed on the system..."
else
	echo "Removed $count_rm" rpms
fi
echo "Summary has been saved in $DIR/$FILENAME"

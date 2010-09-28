#!/bin/sh

echo '# All editions as of' `date +%Y-%m-%d`
wget -q -O - http://meta.wikimedia.org/wiki/List_of_Wikipedias | grep '<td><a href="http://[a-z-]*\.wikipedia.org/wiki/"'| sed 's%</a></td>$%%;s%^.*>%%' | tr '\n' ' '
echo

#!/bin/bash
# Interwiki analysis tools
# Copyright (C) 2007-2009  Lukasz Bolikowski
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# This script downloads the most recent database dumps of selected language editions of Wikipedia.
# By default, it downloads all the editions listed below.  You can override the selection by passing
# the codes of the requested editions as command-line arguments.
#
# Note that the script will store the dumps in the current working directory.

# All editions as of 2009-05-05
LANGUAGES="en de fr pl ja it nl pt es ru sv zh no fi ca uk tr cs hu ro vo eo da sk id ar ko he lt vi sl sr bg et fa hr simple ht new nn gl th te el ms eu ceb mk hi ka la bs lb br is bpy mr sq az cy sh tl lv pms bn be_x_old jv ta oc io be su nds an scn nap ku ast af fy wa sw zh_yue qu bat_smg ur cv ksh ml tg ga vec roa_tara uz gd war kn mi pam yo yi nah co lmo gu hsb zh_min_nan roa_rup glk als li ia hy sah kk sa wuu tk tt nds_nl fo nrm vls fiu_vro am os rm map_bms pag dv se gan diq ne fur sco mn lij gv nov bar bh arz mt ilo pi zh_classical km frp lad csb mzn pdc kw ang haw si ug to bcl sc ps ie szl kv gn pa mg ln my stq hif wo jbo crh tpi ty arc cbk_zam ky eml zea srn ay ext myv hak ig pap or so kg kab lo rmy ba mo sm ce udm av ks kaa tet cu sd mdf bo got iu dsb nv na bm cdo chr ee om as pnt pih zu ti ts kl ss ab bi cr ve dz ch ha xh tn bug ik bxr st rw xal za tw chy ak ny fj ff sn sg lbe rn ki lg tum ng ii cho mh aa kj ho mus kr hz tokipona"

function error {
  echo "Please install curl and wget before running this script"
  exit 1
}

which curl > /dev/null || error
which wget > /dev/null || error

if [ $# -gt 0 ]
then
  LANGUAGES="$@"
fi

function get {
  lg=$1
  tab=$2
  tmp=`curl http://download.wikimedia.org/${lg}wiki/latest/${lg}wiki-latest-${tab}-rss.xml 2> /dev/null | grep 'href' | sed 's/^[^"]*"//;s/".*$//'`
  if [ X$tmp == X ]
  then
    echo "WARNING: Cannot download: " $lg $tab
  else
    wget -q $tmp
    f=`echo $tmp | sed 's%^.*/%%'`
    [ ! -f $f ] && echo "WARNING: Cannot download:" $lg $tab
  fi
}

echo Started at `date`
for lg in $LANGUAGES
do
  get ${lg} "page.sql.gz" 
  get ${lg} "redirect.sql.gz" 
  get ${lg} "langlinks.sql.gz" 

  get ${lg} "categorylinks.sql.gz" 
  get ${lg} "pagelinks.sql.gz" 
done
echo Finished at `date`


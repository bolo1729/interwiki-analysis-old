#!/bin/bash
# Interwiki analysis tools
# Copyright (C) 2007-2010  Lukasz Bolikowski
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

# All editions as of 2010-09-28
LANGUAGES="en de fr pl it ja es nl pt ru sv zh ca no fi uk hu cs ro tr ko da ar eo id vi sr vo lt sk he bg fa sl war hr et ms new simple gl th roa_rup nn eu hi el ht te la ka mk ceb az tl br sh mr lb jv lv bs is cy pms be_x_old sq bpy ta be an oc bn sw io ksh fy gu lmo nds af scn qu ku ur su zh_yue ml ast nap bat_smg wa ga cv hy yo kn tg roa_tara vec pnb gd yi zh_min_nan uz pam tt os ne sah als mi kk arz nah li hsb glk co gan ia am mn bcl fiu_vro nds_nl fo tk vls si sa bar sco gv dv nrm pag rm my map_bms diq ckb se wuu mzn ug fur lij mt bh nov mg csb sc ilo zh_classical km lad pi ang cbk_zam bo frp hif hak pa kw ps xal pdc szl haw ie stq crh fj kv to ace so nv myv gn krc ln ky ext mhr arc jbo eml wo ay pcd kab ty tpi frr ba pap zea srn kl udm ce ig or dsb kg lo ab rmy cu mwl mdf kaa sm mo av tet sn ks got sd na bm pih pnt iu chr ik as bi cdo ee ss om za bug ti ts ve zu ha dz sg ch cr ak xh rw tn ki bxr ny lbe st tw rn chy ff tum lg ng ii cho mh aa kj ho mus kr hz"

# All editions as of 2011-04-01
LANGUAGES="en de fr pl it es ja ru nl pt sv zh ca no uk fi vi cs hu ko id ro tr da ar eo sr lt sk fa vo ms he bg sl war hr hi et gl new simple th eu nn roa_rup el az ht la tl ka te mk ceb sh pms br be_x_old lv mr jv lb cy sq bs is ta be an bpy oc bn io sw lmo fy gu ml af nds scn ur qu ku zh_yue su ast hy nap yo bat_smg ne cv ga wa pnb kn tg kk roa_tara vec tt yi als zh_min_nan gd os uz pam sah arz bug am mi li hsb nah sco gan co glk mn my ia bcl fo fiu_vro si nds_nl vls tk sa bar mg gv ilo map_bms dv nrm pag ckb diq rm se mzn wuu fur ug lij mt bo bh hif ang nov csb lad sc zh_classical km cbk_zam pi ps frp hak mrj kw ksh rue nv pa szl xal rw haw pdc stq ie so udm mhr kv to ln krc crh pcd ace ky ext myv gn ce eml ba arc pap ay bjn jbo kl wo frr tpi kab ty srn zea gag ab dsb koi or lo ig av kg tet mdf mwl lbe rmy cu ltg kaa sm mo kbd got ks bm ik sd bi pfl as na pih iu pnt ss cdo chr ha ee ti bxr zu om za ve ts rn sg dz cr ch lg fj ny tum st ak xh ff tn ki sn tw chy ng ii cho mh aa kj ho mus kr hz"

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
  tmp=`curl http://dumps.wikimedia.org/${lg}wiki/latest/${lg}wiki-latest-${tab}-rss.xml 2> /dev/null | grep 'href' | sed 's/^[^"]*"//;s/".*$//'`
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


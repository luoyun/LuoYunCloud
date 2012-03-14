#!/bin/sh

myexit()
{
  [ -n "$1" ] && echo $1
  exit 1
}

insert_new()
{
  [ -z "$1" ] && myexit "insert_new needs an argument"
  [ ! -f "$1" ] && myexit "can not find $1"
  file=$1
  name=${file%.img.gz}
  [ "$file" == "${name}" ] && myexit "$file not end with .img.gz"
  name=$(basename $name)
  size=$(ls -lH $file | awk '{print $5}')

  m=$(md5sum $file) || myexit "md5sum $file"
  m=$(echo $m | awk '{print $1}' )
  sql=$(cat <<EOL
psql -c \
'insert into appliance (name, summary, user_id, catalog_id, filesize, checksum, created, updated)'\
'values ('\'$name\'', '\'$file\'', 1, 1, $size, '\'$m\'', '\'now\'', '\'now\'');' \
-d luoyun
EOL
)
  su postgres -c "$sql" || myexit "ERR:$sql"
  #cp $file /opt/LuoYun/data/appliance/appliance_$m || myexit "cp $1 ..."
}

update_old()
{
  [ -z "$1" ] && myexit "insert_new needs an argument"
  [ ! -f "$1" ] && myexit "can not find $1"
  file=$1
  name=${file%.img.gz}
  [ "$file" == "${name}" ] && myexit "$file not end with .img.gz"
  name=$(basename $name)
  size=$(ls -lH $file | awk '{print $5}')

  [ -z "$2" ] && myexit "insert_new needs more argument"
  id=$2

  sql=$(cat <<EOL
psql -c \
'select name,checksum from appliance where id = $id;' \
-d luoyun
EOL
)
  r=$(su postgres -c "$sql" || myexit "ERR:$sql")
  n=$(echo $r | awk '{print $5}')
  mold=$(echo $r | awk '{print $7}')
  [ "$n" == "$name" ] || myexit "ERR:name $name not match id $id"

  m=$(md5sum $file) || myexit "md5sum $file"
  m=$(echo $m | awk '{print $1}' )
  [ "$mold" == "$m" ] && myexit "checksum same?"

  sql=$(cat <<EOL
psql -c \
'update appliance set filesize = $size, checksum = '\'$m\'', updated = '\'now\'\
' where id = $id;' \
-d luoyun
EOL
)
  su postgres -c "$sql" || myexit "ERR:$sql"
  cp $file /opt/LuoYun/data/appliance/appliance_$m || myexit "cp $1 ..."
  rm -f /opt/LuoYun/data/appliance/appliance_$mold
}

if [ -n "$2" ] 
then
  update_old $1 $2
else
  insert_new $1
fi




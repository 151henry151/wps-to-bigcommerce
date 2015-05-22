
#!/bin/bash

#{ echo 'create table table1 ('; for ((i=1;i<80;i++)); do ((i>1)) && printf ',\n'; printf " col%i VARCHAR(255)" "$i"; done; echo ');'; } > table.sql


{ echo 'CREATE TABLE basepricefile ('; for i in $( head -n 1 BasePriceFile.csv | sed -e's/"//g' -e 's/,//g' ); do printf "\t$i\t\tVARCHAR(255),\n" "$i"; done; echo ');'; } > table.sql

#!/usr/bin/tclsh
package require sqlite3
set tablenum [expr [llength $argv] - 1]
if {$tablenum <= 0 || $tablenum % 2} {
    set scriptname [info script]
    puts "Sort SQLite tables by defined order"
    puts "Usage: tclsh $scriptname dbname table1 orderby1 \[table2 orderby2 ...\]"
    puts "dbname    is the file name of the SQLite database"
    puts "tableN    is the table name"
    puts "orderbyN  is the ORDER BY clause for the table"
    exit 1
}
set dbfilename [lindex $argv 0]
sqlite3 db $dbfilename

set i 0
while {$i < $tablenum} {
    set tablename [lindex $argv [expr $i + 1]]
    set orderby [lindex $argv [expr $i + 2]]
    puts "Sorting for $tablename ..."
    db eval "BEGIN"
    db eval "CREATE TEMP TABLE t_sorted AS
        SELECT * FROM $tablename ORDER BY $orderby"
    db eval "DELETE FROM $tablename"
    puts "Writing back..."
    db eval "INSERT INTO $tablename SELECT * FROM t_sorted"
    db eval "DROP TABLE temp.t_sorted"
    db eval "COMMIT"
    incr i 2
}
puts "Vacuum..."
db eval {VACUUM}
db close

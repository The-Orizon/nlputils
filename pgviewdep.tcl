#!/usr/bin/tclsh
# Prints GraphViz dot graph for view dependencies in PostgreSQL.
# usage: tclsh pgviewdep.tcl dbname=DBNAME [host|port|user|password|options=...]

package require Pgtcl
set conninfo {}
foreach arg $argv {
  set option [split $arg =]
  lappend conninfo [lindex $option 0] = [lindex $option 1]
}
set db [pg_connect -conninfo $conninfo]
puts "digraph \{"
puts {graph [pad="0.5", nodesep="0.5", ranksep="2"];
  node [shape=plain]
  edge [arrowhead=open]
  rankdir=LR;
}
set currtable _
pg_execute -array d $db {
  SELECT
    cl.oid, ns.nspname, cl.relname, cl.relkind, att.attname
  FROM pg_class cl
  INNER JOIN pg_namespace ns ON cl.relnamespace=ns.oid
  INNER JOIN pg_attribute att ON cl.oid=att.attrelid
  WHERE cl.relkind IN ('r', 'v', 'm') AND att.attnum>0
  AND cl.oid IN (
    SELECT dependent_view.oid
    FROM pg_depend
    JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid
    JOIN pg_class as dependent_view ON pg_rewrite.ev_class = dependent_view.oid
    JOIN pg_attribute ON pg_depend.refobjid = pg_attribute.attrelid
      AND pg_depend.refobjsubid = pg_attribute.attnum
    JOIN pg_namespace dependent_ns ON dependent_ns.oid = dependent_view.relnamespace
    WHERE dependent_ns.nspname NOT IN ('pg_catalog', 'information_schema')
    UNION
    SELECT pg_depend.refobjid
    FROM pg_depend
    JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid
    JOIN pg_class as dependent_view ON pg_rewrite.ev_class = dependent_view.oid
    JOIN pg_attribute ON pg_depend.refobjid = pg_attribute.attrelid
      AND pg_depend.refobjsubid = pg_attribute.attnum
    JOIN pg_namespace dependent_ns ON dependent_ns.oid = dependent_view.relnamespace
    WHERE dependent_ns.nspname NOT IN ('pg_catalog', 'information_schema')
  )
  AND ns.nspname NOT IN ('pg_catalog', 'information_schema')
  ORDER BY cl.relkind!='r', cl.oid, att.attnum
} {
  set tablename "$d(nspname)__$d(relname)"
  if {![string equal $currtable $tablename]} {
    if {![string equal $currtable _]} {puts {</table>>];}}
    puts "$tablename \[label=<"
    puts {<table border="0" cellborder="1" cellspacing="0">}
    puts -nonewline "<tr><td port=\"$tablename\"><i>$d(nspname)</i>.<br/>"
    if {[string equal $d(relkind) r]} {
      puts "<b>$d(relname)</b></td></tr>"
    } elseif {[string equal $d(relkind) v]} {
      puts "<i>$d(relname)</i></td></tr>"
    } else {
      puts "$d(relname)</td></tr>"
    }
    set currtable $tablename
  }
  puts "<tr><td port=\"$d(attname)\">$d(attname)</td></tr>"
}
puts {</table>>];}

set currview _
set viewcount 0
# DISTINCT ON (dependent_view.oid, source_table.oid)
pg_execute -array d $db {
  SELECT
    dependent_ns.nspname as dependent_schema,
    dependent_view.relname as dependent_view,
    source_ns.nspname as source_schema,
    source_table.relname as source_table,
    pg_attribute.attname as column_name
  FROM pg_depend
  JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid
  JOIN pg_class as dependent_view ON pg_rewrite.ev_class = dependent_view.oid
  JOIN pg_class as source_table ON pg_depend.refobjid = source_table.oid
  JOIN pg_attribute ON pg_depend.refobjid = pg_attribute.attrelid
    AND pg_depend.refobjsubid = pg_attribute.attnum
  JOIN pg_namespace dependent_ns ON dependent_ns.oid = dependent_view.relnamespace
  JOIN pg_namespace source_ns ON source_ns.oid = source_table.relnamespace
  WHERE dependent_ns.nspname NOT IN ('pg_catalog', 'information_schema')
  AND pg_attribute.attnum > 0
  ORDER BY dependent_view.oid, source_table.oid, pg_attribute.attnum
} {
  set fromtablename "$d(dependent_schema)__$d(dependent_view)"
  set totablename "$d(source_schema)__$d(source_table)"
  puts -nonewline "$totablename:$d(column_name) -> $fromtablename:$fromtablename"
  #puts -nonewline "$totablename:$totablename -> $fromtablename:$fromtablename"
  if {![string equal $currview $fromtablename]} {
    set viewcount [expr $viewcount % 9 + 1]
  }
  puts " \[color=\"/set19/$viewcount\"\]"
  set currview $fromtablename
}

puts "}"

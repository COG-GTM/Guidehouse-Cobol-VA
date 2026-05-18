#!/usr/bin/perl
#
# LABA05
#
use File::Copy;
$uname_fld = getpwuid( $< );
$bigtime = localtime(time);
print "BEGIN RUN OF LABA05 -- submitted by $uname_fld, $bigtime\n";
$timestamp = `perl $ENV{'SCRDIR'}/TIMESTAMP.pl`;
open (RUNLOG, ">$ENV{'LOGDIR'}/LABA05.$timestamp.log");
print RUNLOG ("BEGIN RUN OF LABA05 -- submitted by $uname_fld, $bigtime\n");
$rc=0;
$rcp=0;
$rs=0;
$!="";
# *** redirect output of COBOL program DISPLAY UPON PRINTER to log file ***
open (COBPRTR, ">$ENV{'RUNTMP'}/LABA05.cobprtr.$timestamp.ksh");
print COBPRTR ("cat <&0 >> $ENV{'RUNTMP'}/LABA05.$timestamp.cobprtr\n");
close (COBPRTR);
chmod 0775, "$ENV{'RUNTMP'}/LABA05.cobprtr.$timestamp.ksh";
$ENV{'COBPRINTER'}="$ENV{'RUNTMP'}/LABA05.cobprtr.$timestamp.ksh";
# ***
# **************** RUN A PROGRAM  ****************
print RUNLOG ("rtsora $ENV{'BINDIR'}/LABA05\n");
print RUNLOG (" \n");
print RUNLOG ("Program LABA05 Input File: \n");
print RUNLOG (" \n");
print RUNLOG ("     None \n");
print RUNLOG (" \n");
print RUNLOG ("Program LABA05 Output File: \n");
print RUNLOG (" \n");
print RUNLOG ("     None \n");
print RUNLOG (" \n");
system ("rtsora $ENV{'BINDIR'}/LABA05");
$rc=$?>>8;
print RUNLOG ("*** return code = $rc ***\n");
if ($rc ne 0) { print "*** return code = $rc ***\n"; goto ENDRUN; }
# **************** END OF PROGRAM ****************
ENDRUN:
$bigtime = localtime(time);
print RUNLOG ("END RUN OF LABA05 -- $bigtime\n");
print RUNLOG ("\n*** Program displays follow:\n");
close (RUNLOG);
if (-e "$ENV{'RUNTMP'}/LABA05.$timestamp.cobprtr") {
  system ("cat $ENV{'RUNTMP'}/LABA05.$timestamp.cobprtr >> $ENV{'LOGDIR'}/LABA05.$timestamp.log");
  unlink "$ENV{'RUNTMP'}/LABA05.$timestamp.cobprtr";
}
unlink "$ENV{'RUNTMP'}/LABA05.cobprtr.$timestamp.ksh";
print "END RUN OF LABA05 -- $bigtime\n";
if ($rc ne 0) {
  print "*** exit $rc -- program error\n";
  exit $rc
}
elsif ($rcp ne 0) {
  print "*** exit $rcp -- file copy error\n";
  exit $rcp
}
elsif ($rs ne 0) {
  print "*** exit $rs -- mfsort error\n";
  exit $rs
}
else {
  print "*** exit 0 -- successful job\n";
  exit 0
}
# END OF SCRIPT

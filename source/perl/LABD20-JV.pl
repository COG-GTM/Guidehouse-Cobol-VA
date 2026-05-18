#!/usr/bin/perl
#
# LABD20-JV
#
use File::Copy;
$uname_fld = getpwuid( $< );
$bigtime = localtime(time);
print "BEGIN RUN OF LABD20-JV -- submitted by $uname_fld, $bigtime\n";
$timestamp = `perl $ENV{'SCRDIR'}/TIMESTAMP.pl`;
open (RUNLOG, ">$ENV{'LOGDIR'}/LABD20-JV.$timestamp.log");
print RUNLOG ("BEGIN RUN OF LABD20-JV -- submitted by $uname_fld, $bigtime\n");
$rc=0;
$rcp=0;
$rs=0;
$!="";
# *** redirect output of COBOL program DISPLAY UPON PRINTER to log file ***
open (COBPRTR, ">$ENV{'RUNTMP'}/LABD20-JV.cobprtr.$timestamp.ksh");
print COBPRTR ("cat <&0 >> $ENV{'RUNTMP'}/LABD20-JV.$timestamp.cobprtr\n");
close (COBPRTR);
chmod 0775, "$ENV{'RUNTMP'}/LABD20-JV.cobprtr.$timestamp.ksh";
$ENV{'COBPRINTER'}="$ENV{'RUNTMP'}/LABD20-JV.cobprtr.$timestamp.ksh";
# ***
unlink "$ENV{'DATADIR'}/PLABD-A.LABIDD2001.dat";
unlink "$ENV{'DATADIR'}/PLABD-A.LABTDD2003.dat";
#
$ext=`perl $ENV{'SCRDIR'}/GETGDGNO.pl NEXT PLABD-A LABSAVECMTS +1 2>&1`;
print RUNLOG ("copy  $ENV{'DATADIR'}/TST.JVCMTS.dat  to  $ENV{'DATADIR'}/PLABD-A.LABSAVECMTS.$ext.dat\n");
copy ("$ENV{'DATADIR'}/TST.JVCMTS.dat","$ENV{'DATADIR'}/PLABD-A.LABSAVECMTS.$ext.dat");
if ($! gt " ") { 
  $rcp=88;
  print "*** Copy failed: $!\n";
  print RUNLOG ("*** Copy failed: $!\n");
  goto ENDRUN;
}
$ENV{'COMMENT'}="$ENV{'DATADIR'}/TST.JVCMTS.dat";
# **************** RUN A PROGRAM  ****************
$ENV{'CARDFILE'}="$ENV{'PARMDIR'}/DAILY.MM-DD-CCYY.ctl";
print RUNLOG ("rtsora $ENV{'BINDIR'}/LABD20\n");
print RUNLOG (" \n");
print RUNLOG ("Program LABD20 Input File: \n");
print RUNLOG (" \n");
print RUNLOG ("     $ENV{'CARDFLE'} \n");
print RUNLOG ("     $ENV{'COMMENT'} \n");
print RUNLOG (" \n");
print RUNLOG ("Program LABD20 Output File: \n");
print RUNLOG (" \n");
print RUNLOG (" \n");
system ("rtsora $ENV{'BINDIR'}/LABD20");
$rc=$?>>8;
print RUNLOG ("*** return code = $rc ***\n");
if ($rc ne 0) { print "*** return code = $rc ***\n"; goto ENDRUN; }
# **************** END OF PROGRAM ****************
$ext=`perl $ENV{'SCRDIR'}/GETGDGNO.pl NEXT PLABD-A LABIDD2002 +1 2>&1`;
print RUNLOG ("copy  $ENV{'DATADIR'}/PLABD-A.LABIDD2001.dat  to  $ENV{'DATADIR'}/PLABD-A.LABIDD2002.$ext.dat\n");
ENDRUN:
$bigtime = localtime(time);
print RUNLOG ("END RUN OF LABD20-JV -- $bigtime\n");
print RUNLOG ("\n*** Program displays follow: \n");
close (RUNLOG);
if (-e "$ENV{'RUNTMP'}/LABD20-JV.$timestamp.cobprtr") {
  system ("cat $ENV{'RUNTMP'}/LABD20-JV.$timestamp.cobprtr >> $ENV{'LOGDIR'}/LABD20-JV.$timestamp.log");
  unlink "$ENV{'RUNTMP'}/LABD20-JV.$timestamp.cobprtr";
}
unlink "$ENV{'RUNTMP'}/LABD20-JV.cobprtr.$timestamp.ksh";
print "END RUN OF LABD20-JV -- $bigtime\n";
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

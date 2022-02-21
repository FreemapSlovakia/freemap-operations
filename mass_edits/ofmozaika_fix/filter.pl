#!/bin/perl
# download fresh dump (with metadata) from https://osm-internal.download.geofabrik.de/europe.html
# then run this perl script

use strict;
use warnings;
use utf8;

my @affected_users = ('aceman444', 'Durko_freemap', 'synalik', 'laznik');

my %tainted;
$tainted{0} = [];  # nodes
$tainted{1} = [];  # ways
$tainted{2} = [];  # relations

# input/output streams
open(OSMCONVERT, 'osmconvert slovakia-internal.osh.pbf --out-csv --csv="@id @lat @lon @user @otype @version source" |');
open(IDS, ">", "ids.txt");
open(ZBGIS, ">", "zbgis_ids.txt");
open(NOCHANGE, ">", "nochange.txt");

print "Looking at all objects history (checking known users + ZBGIS source)\n";

while (<OSMCONVERT>) {
  chomp;
  my @F = split('\t');
  (my $id, my $lat, my $lon, my $user, my $type, my $version, my $source) = @F;
  if (!defined($source)){ $source = "" };
  if  ( grep ( { $_ eq $user } @affected_users) and $source =~ /zbgis/i )  {
    push @{$tainted{$type}}, $id;
   }
  }

close(OSMCONVERT);

open(OSMCONVERT, 'osmconvert slovakia-internal.osh.pbf --out-csv --csv="@id @lat @lon @user @otype @version source" |');

print "Filtering and saving into ids.txt/nochange.txt\n";

my $osmconvert = <OSMCONVERT>;
while (<OSMCONVERT>) {
  chomp;
  my @F = split('\t');
  (my $id, my $lat, my $lon, my $user, my $type, my $version, my $source) = @F;
  if (!defined($source)){ $source = "" };
  if ($source =~ /ofmozaika|ofmozaka|ofmozajka|ofmozika|Ortofotomazaika SR|Orthopho.o mosaic Slovakia|orto\s*-?\s*zbgis®?( *, úrad geodézie, kartografie a katastra slovenskej republiky)?|ortozbgis|zbgis\s*orto|zbis ortofoto|zbgis-orto/i)
    {
	if ( grep ( { $_ eq $id } @{$tainted{$type}} ) )
          {
            print IDS "1\t" . "$_" . "\n";
          }
        else
          {
            print IDS "0\t" . "$_" . "\n";
          }
    }
  elsif ($source =~ /zbgis/i) {
	if ( grep ( { $_ eq $id } @{$tainted{$type}} ) )
          {
            print IDS "1\t" . "$_" . "\n";
          }
   }
  elsif ($source)
    {
    print NOCHANGE "$_" . "\n" 
    }
  #  >ids.txt
}

# print IDS join("\n", @ids);

close(OSMCONVERT);
close(NOCHANGE);
close(IDS);

print "Finished. Now run ids2osm.py\n";

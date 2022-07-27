#!/usr/bin/perl
# ARGV[0] is the input file
# format is
# config: [name of config to use]
# raw: [raw filter id]
# client: [client filter id]

# read in the config file and then build commands to 
# run Ibex/getReport.py

my $target = $ARGV[0];
my $rawcmd = "";
my $clientcmd = "";
my $ibexpath = "/opt/openvas-exporter/code/getReport.py";
my $config = "/opt/openvas-exporter/code/config/ibex.config";

if (! -e $ibexpath) {
    print "getReport.py not found at $ibexpath\n";
    exit;
}

if (! -e $config) {
    print "ibex config not found at $config\n";
    exit;
}

sub  trim { 
    my $s = shift; 
    $s =~ s/^\s+|\s+$//g; 
    return $s 
};


$target = trim($target);

if (! $target) {
    print "You must provide a taskname.\n";
    exit;
}

open (FH, "<", $config) or die ("Cannot open $file");
while (<FH>) {
    chomp $_;
    (my $key, my $value) = split ":", $_;
    $parameter{$key} = trim($value);
} 

if (!$parameter{config}) {
    print "Config file not set in run file\n";
    exit;
}

if ($parameter{'raw'}) {
    $rawcmd = "python3 $ibexpath -f $parameter{raw} -t $target -i $parameter{config}";
}

if ($parameter{'client'}) {
    $clientcmd = "python3 $ibexpath -f $parameter{client} -t $target -i $parameter{config} -P";
}

print "About to run the following commands\n";
print "Client: $clientcmd\n";
print "Raw: $rawcmd\n";

print "Starting client filter processing\n";
system ($clientcmd);

print "Starting raw filter processing\n";
system ($rawcmd);

print "Completed\n";

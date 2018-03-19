'''
bencher.py : Python 2
Author : Abhishek Munagekar
A script to quickly generate comparison between image qualities

Comparisons
vmaf
psnr
ssim
phone_model

Dependencies
ffmpeg with vmaf binding


Arguments:
Input Folder : Folder Containing the files given as input to the network
Output Folder : Fodler Contina the files given as output by the network
Reference Folder : Folder Containing the files to be used as reference
'''
import subprocess
import argparse
import os
from multiprocessing import Pool
from numpy import median, mean


# Helper Functions
def build_parser():
    parser = argparse.ArgumentParser(description='Fast Folder Benchmarking')
    parser.add_argument('-i', type=str,
                        help='Folder Containing Input Files')
    parser.add_argument('-r', type=str,
                        help='Folder Containing the Reference Files')
    parser.add_argument('-o', type=str,
                        help='Folder Containing the output Files')
    parser.add_argument('-itype', type=str,
                        help='Type of Images in Infolder')
    parser.add_argument('-otype', type=str,
                        help='Type of Image in Outfolder')
    parser.add_argument('--statfile', type=str, default="benchmark.txt",
                        help='Name/Location for Benchmark file')

    return parser


# Returns the median, average, min, max of a list
# Returns a dictionary for easy access
def liststat(l):
    stat = {}
    stat['medain'] = median(l)
    stat['mean'] = mean(l)
    stat['max'] = max(l)
    stat['min'] = min(l)
    return stat


# Helper Function for Pool Jobs
def statcomparehelper(i_ref):
    return statcompare(*i_ref)


# Calculate Comparisson for Two Files
# Does comparison for ssim , psnr, vmaf, vmaf - phone, ms_ssim
def statcompare(i, ref):
    params = {'ifile': i, 'rfile': ref}
    # VMaf - Phone
    command = 'ffmpeg -loglevel panic -i ' + i + ' -i ' + ref + \
        ' -lavfi libvmaf="phone_model=1" -f null - | grep "VMAF score"'
    result = subprocess.check_output(command, shell=True)
    params['vmafp'] = result.strip().split(' ')[-1]

    # VMaf
    command = 'ffmpeg -loglevel panic -i ' + i + ' -i ' + ref + \
        ' -lavfi libvmaf -f null - | grep VMAF '
    result = subprocess.check_output(command, shell=True)
    params['vmaf'] = result.strip().split(' ')[-1]

    # PSNR
    command = 'ffmpeg -loglevel info -i ' + i + ' -i ' + ref + \
        ' -filter_complex "psnr" -f null - '
    result = subprocess.check_output(
        command, stderr=subprocess.STDOUT, shell=True)
    params['psnr'] = result.split('\n')[-2].split(':')[-2].split(' ')[0]

    # SSIM
    command = 'ffmpeg -loglevel info -i ' + i + ' -i ' + ref + \
        ' -filter_complex "ssim" -f null - '
    result = subprocess.check_output(
        command, stderr=subprocess.STDOUT, shell=True)
    params['ssim'] = result.split('\n')[-2].split(' ')[-2].split(':')[1]

    return params


# Remove thumbnails as well other temp files
def cleanpnglist(ilist):
    cleanedlist = []
    for item in ilist:
        if 'png' in item:
            cleanedlist.append(item)
    return cleanedlist


#


parser = build_parser()
args = parser.parse_args()

IN = args.i
REF = args.r
OUT = args.o
INLABEL = args.itype
OUTLABEL = args.otype
BFILE = args.statfile

assert (os.path.exists(IN) and
        os.path.exists(REF)and
        os.path.exists(OUT)), "Invlaid Folder Paths"

infiles = cleanpnglist(os.listdir(IN))
infiles = map(lambda x: os.path.join(IN, x), infiles)
outfiles = cleanpnglist(os.listdir(OUT))
outfiles = map(lambda x: os.path.join(OUT, x), outfiles)
reffiles = cleanpnglist(os.listdir(REF))
reffiles = map(lambda x: os.path.join(REF, x), reffiles)

# Inplace Sort
infiles.sort()
outfiles.sort()
reffiles.sort()


assert(len(infiles) == len(outfiles) and
       len(outfiles) == len(reffiles)), "Num files Mismatch"

pool = Pool()
istats = pool.map(statcomparehelper, zip(infiles, reffiles))
ostats = pool.map(statcomparehelper, zip(outfiles, reffiles))


fp = open(BFILE, 'w')
fp.write('Type of File,File Location,Reference Location,' +
         'PSNR,SSIM,VMAF,VMAF Phone\n')


assert (len(istats) == len(ostats)), "Possible Crash in ffmpeg"

gpsnr = 0
gssim = 0
gvmaf = 0
gvmafp = 0


for istat, ostat in zip(istats, ostats):
    fp.write(INLABEL + ',')
    fp.write(istat['ifile'] + ',')
    fp.write(istat['rfile'] + ',')
    fp.write(istat['psnr'] + ',')
    fp.write(istat['ssim'] + ',')
    fp.write(istat['vmaf'] + ',')
    fp.write(istat['vmafp'])
    fp.write('\n')

    fp.write(OUTLABEL + ',')
    fp.write(ostat['ifile'] + ',')
    fp.write(ostat['rfile'] + ',')
    fp.write(ostat['psnr'] + ',')
    fp.write(ostat['ssim'] + ',')
    fp.write(ostat['vmaf'] + ',')
    fp.write(ostat['vmafp'])
    fp.write('\n')

    gpsnr += (float(ostat['psnr']) - float(istat['psnr']))
    gssim += (float(ostat['ssim']) - float(istat['ssim']))
    gvmaf += (float(ostat['vmaf']) - float(istat['vmaf']))
    gvmafp += (float(ostat['vmafp']) - float(istat['vmafp']))

print "Gain PSNR:", gpsnr / len(istats)
print "Gain SSIM:", gssim / len(istats)
print "Gain VMAF:", gvmaf / len(istats)
print "Gain VMAFP:", gvmafp / len(istats)
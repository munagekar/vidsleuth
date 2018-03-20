# coding=utf-8
'''
bencher.py : Python 2
Author : Abhishek Munagekar


Call Using
python bencher.py -ifols 10 net10 20 net20 25 net25 35 net35 45 net45 -itypes cqi10 net10 cqi20 net20 cqi25 net25 cqi35 net35 cqi45 net45 -rfol label --comps 0vs1 2vs3 4vs5 6vs7 8vs9
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


import argparse
import os
import core
from multiprocessing import Pool
from numpy import median, mean


def magprint(num):
    if num == 0:
        return(' ' + str(num))
    elif num > 0:
        return('+' + str(num))
    else:
        return('-' + str(num))

# Returns the median, average, min, max of a list
# Returns a dictionary for easy access


def liststat(l):
    stat = {}
    stat['medain'] = median(l)
    stat['mean'] = mean(l)
    stat['max'] = max(l)
    stat['min'] = min(l)
    return stat


def diff(stat1, stat2):
    diffstat = {}
    psnrdiff = []
    vmafdiff = []
    vmafpdiff = []
    ssimdiff = []
    for x, y in zip(stat1, stat2):
        psnrdiff.append(x['psnr'] - y['psnr'])
        vmafdiff.append(x['vmaf'] - y['vmaf'])
        vmafpdiff.append(x['vmafp'] - y['vmafp'])
        ssimdiff.append(x['ssim'] - y['ssim'])
    diffstat['psnr'] = liststat(psnrdiff)
    diffstat['vmaf'] = liststat(vmafdiff)
    diffstat['vmafp'] = liststat(vmafpdiff)
    diffstat['ssim'] = liststat(ssimdiff)
    return diffstat


# Helper Function for Pool Jobs
def statcomparehelper(i_ref):
    return statcompare(*i_ref)


# Calculate Comparisson for Two Files
# Does comparison for ssim , psnr, vmaf, vmaf - phone, ms_ssim
def statcompare(i, ref):
    params = {'ifile': i, 'rfile': ref}
    params['vmafp'] = core.vmafp(i, ref)
    params['vmaf'] = core.vmaf(i, ref)
    params['psnr'] = core.psnr(i, ref)
    params['ssim'] = core.ssim(i, ref)
    return params


# A Modification of os.listdir
# Gives the Path along with the file names
def pathdir(dir):
    return [os.path.join(dir, x) for x in os.listdir(dir)]


# TODO : Make a proper check for extension
# Remove thumbnails as well other temp files
def cleanlist(ilist, ext):
    cleanedlist = []
    for item in ilist:
        if ext in item:
            cleanedlist.append(item)
    return cleanedlist


# Helper Functions
def build_parser():
    parser = argparse.ArgumentParser(description='Fast Folder Benchmarking')
    parser.add_argument('-ifols', type=str, nargs='+',
                        help='Folders Containing Input Files')
    parser.add_argument('-rfol', type=str,
                        help='Folder Containing the Reference Files')
    parser.add_argument('-itypes', type=str, nargs='+',
                        help='Type of Images in Infolder')
    parser.add_argument('--statfile', type=str, default="benchmark.txt",
                        help='Name/Location for Benchmark file')
    parser.add_argument('--comps', type=str, nargs='+',
                        help='1vs2 2vs3 4vs5 etc')
    return parser


parser = build_parser()
args = parser.parse_args()

# Multiple Inputs for the same reference

INS = args.ifols
REF = args.rfol
INLABELS = args.itypes
BFILE = args.statfile
COMPS = args.comps


# Existence Check
for folder in INS:
    assert(os.path.exists(folder)), folder + " doesn't exist"
assert(os.path.exists(REF)), REF + "doesn't exist"


infiles = [cleanlist(pathdir(x), 'png') for x in INS]
reffiles = cleanlist(pathdir(REF), 'png')


# Inplace Sort
for x in infiles:
    x.sort()
reffiles.sort()

# Length Check
for x in infiles:
    assert(len(x) == len(reffiles)), "File Number Mismatch Occured"

pool = Pool()
istats = []
print('Parallel Processing : Using All Cores')
print('Please be Patient....')
for i, x in enumerate(infiles):
    istats.append(pool.map(statcomparehelper, zip(x, reffiles)))
    # TODO : Add a Prog Bar Call Here

fp = open(BFILE, 'w')
fp.write('Type of File,File Location,Reference Location,' +
         'PSNR,SSIM,VMAF,VMAF Phone\n')

# For Istatfol
for item in range(len(reffiles)):
    for i, istatfol in enumerate(istats):
        fp.write(INLABELS[i] + ',')
        fp.write(istatfol[item]['ifile'] + ',')
        fp.write(istatfol[item]['rfile'] + ',')
        fp.write(str(istatfol[item]['psnr']) + ',')
        fp.write(str(istatfol[item]['ssim']) + ',')
        fp.write(str(istatfol[item]['vmaf']) + ',')
        fp.write(str(istatfol[item]['vmafp']))
        fp.write('\n')


for i in range(len(COMPS)):
    fol1, fol2 = COMPS[i].split('vs')
    n1 = int(fol1)
    n2 = int(fol2)
    print('Gains ' + INLABELS[n1] + 'vs' + INLABELS[n2] + '\n')
    diffstat = diff(istats[n1], istats[n2])
    metrics = ['psnr', 'ssim', 'vmaf', 'vmafp']
    for metric in metrics:
        print(metric, ':', magprint(diffstat[metric]), '\n')

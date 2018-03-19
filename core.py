'''
core.py : Python 2
Author : Abhishek Munagekar
Base Wrapper on Top of ffmpeg and vmaf
'''

import subprocess


# VMAF
def vmaf(i, ref):
    command = 'ffmpeg -loglevel panic -i ' + i + ' -i ' + ref + \
        ' -lavfi libvmaf -f null - | grep VMAF '
    result = subprocess.check_output(command, shell=True)
    return result.strip().split(' ')[-1]


# VMAF - Phone
def vmafp(i, ref):
    command = 'ffmpeg -loglevel panic -i ' + i + ' -i ' + ref + \
        ' -lavfi libvmaf="phone_model=1" -f null - | grep "VMAF score"'
    result = subprocess.check_output(command, shell=True)
    return result.strip().split(' ')[-1]


# SSIM
def ssim(i, ref):
    command = 'ffmpeg -loglevel info -i ' + i + ' -i ' + ref + \
        ' -filter_complex "ssim" -f null - '
    result = subprocess.check_output(
        command, stderr=subprocess.STDOUT, shell=True)
    return result.split('\n')[-2].split(' ')[-2].split(':')[1]


def psnr(i, ref):
    command = 'ffmpeg -loglevel info -i ' + i + ' -i ' + ref + \
        ' -filter_complex "psnr" -f null - '
    result = subprocess.check_output(
        command, stderr=subprocess.STDOUT, shell=True)
    return result.split('\n')[-2].split(':')[-2].split(' ')[0]

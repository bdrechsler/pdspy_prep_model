#!/usr/bin/env python

import glob
import os
import numpy as np
from casatasks import mstransform, tclean, listobs, concat, rmtables, impbcor, exportfits
import pdspy.interferometry as uv
import argparse
from create_config import create_config


"""###################################
###### Regridding Parameters #########
######################################"""

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=str)
parser.add_argument('--chan_width', type=str, default='0.334km/s')
parser.add_argument('--nchan', type=int, default=36)
parser.add_argument('--svel', type=str, default='-2.0km/s')
parser.add_argument('--line', type=str, default='C18O')
parser.add_argument('--uvcut', action='store_false')
parser.add_argument('--robust', type=float, default=2.0)
parser.add_argument('--data_dir', type=str, default='./data/')
parser.add_argument('--model_dir', type=str)
parser.add_argument('--disk_type', type=str, default='dartois-truncated')
parser.add_argument('--dpc', type=float, default=132.)
parser.add_argument('--action', type=str)
args = parser.parse_args()

line_dict = {'C18O': '219.56035410GHz',
             '13CO': '220.39868420GHz',
             'CH3OH': '241.80652400GHz',
             'C17O': '224.714743800GHz'}

source = args.source # source name
chan_width = args.chan_width # channel width
nchan = args.nchan # number of channels
svel = args.svel # starting velocity
linename = args.line
rfreq = line_dict[linename] # rest freq of line
parallel = False

# determine which steps to perform
prep_data = False
make_config = False
make_start_script = False

if args.action=='all':
    prep_data=True
    make_config=True
    make_start_script=True
elif args.action == 'make_scripts':
    make_config=True
    make_start_script=True
elif args.action == 'config':
    make_config=True
elif args.action == 'start_script':
    make_start_script=True

# path to data
data_dir = args.data_dir
line_vis_list = glob.glob(data_dir + "*spectral_line.ms") # list of spectral line ms files

"""
#### Regrid the data #####
"""
if prep_data:
    regrid_vis = []

    for line_vis in line_vis_list:
        # find spectral window corresponding to rfreq

        # create listobs file
        listfile = line_vis.replace('.ms', '.listobs') 
        os.system("rm -rf " + listfile)
        listobs(vis=line_vis, listfile=listfile, verbose=False)
    
        # read listobs file into a list of lines
        listobs_file = open(listfile, "r")
        lines = listobs_file.readlines()

        # find lines corresponding to spws
        for i in range(len(lines)):
            split_line = lines[i].split() # split line into list of strings
            if split_line: # make sure line is not empty
                if split_line[0] == 'SpwID':
                    first_ind = i+1
                elif split_line[0] == 'Antennas:':
                    last_ind = i

        spw_header = lines[first_ind - 1] # line defining spw columns
        spw_lines = lines[first_ind:last_ind] # lines correponding to the spws

        # find spw with central frequency closest to rfreq
        ctrfreq_ind = spw_header.split().index('CtrFreq(MHz)')
        spws = [spw_lines[i].split()[ctrfreq_ind] for i in range(len(spw_lines))]
        spws_array = np.array(spws).astype('float64')
        freq_MHz = float(rfreq[:-3]) * 1000
        spw = str(np.argmin(np.abs(spws_array-freq_MHz)))
        listobs_file.close()

        outfile = line_vis.replace('spectral_line.ms', linename+'_lsrk.ms') # name of output ms file
        print("Creating " + outfile)
        os.system("rm -rf " + outfile)

        mstransform(vis=line_vis, regridms=True, mode='velocity', outputvis=outfile,
                    outframe='LSRK', veltype='radio', restfreq=rfreq, datacolumn='data',
                    width=chan_width, nchan=nchan, start=svel, combinespws=False, keepflags=False,
                    timeaverage=True, timebin='30.25s', spw=spw)
        
        regrid_vis.append(outfile)
        
    """
    ##### Clean and Image the Data #######
    """

    imagename = data_dir + source + '_' + linename + '_t2000klam'
    for ext in ['.image','.mask','.model','.pb','.psf','.residual','.sumwt','.workingdirectory']:
        os.system('rm -rf ' + imagename + ext)

    print("Running tlean:")

    if args.uvcut:
        uvrange='>50klambda'
    else:
        uvrange='all'

    tclean(vis=regrid_vis, spw='', imagename=imagename, specmode='cube', imsize=512,
        deconvolver='hogbom', start=svel, width=chan_width, nchan=nchan, outframe='LSRK',
        veltype='radio', restfreq=rfreq, cell='0.025arcsec',
        gain=0.1, niter=20000, weighting='briggs', robust=args.robust, threshold='1.0mJy',
        usemask='auto-multithresh', sidelobethreshold=2.0, noisethreshold=4.0,
        lownoisethreshold=1.0, interactive=False, restoringbeam='common',
        uvtaper=['2000klambda'], uvrange=uvrange, parallel=parallel)

    # primary beam correction
    myimages = glob.glob(data_dir + "*.image")

    rmtables(data_dir + '*.pbcor')
    for image in myimages:
        impbcor(imagename=image, pbimage=image.replace('.image','.pb'), outfile=image.replace('.image', '.pbcor'))

    # export the images
    myimages = glob.glob(data_dir + "*.image")
    for image in myimages:
        exportfits(imagename=image, fitsimage=image+'.fits', overwrite=True)

    myimages = glob.glob(data_dir + '*.pbcor')
    for image in myimages:
        exportfits(imagename=image, fitsimage=image+'.fits', overwrite=True)

    myimages = glob.glob(data_dir + "*.pb")
    for image in myimages:
        exportfits(imagename=image, fitsimage=image+'.fits', overwrite=True)

    for ext in ['*.pb', '*.psf', '*.model', '*.residual', '*.mask', '*.image', '*.pbcor']:
        os.system("rm -rf " + data_dir + ext)

    """
    ###### Write Data to an HDF5 file #######
    """

    # concatinate regridded visibility files
    os.system("rm -rf " + data_dir + "*concat.ms")
    concat_file = data_dir + source + '_' + linename + '_' + 'concat.ms'
    concat(vis=regrid_vis, concatvis=concat_file)

    # load concated ms file into pdspy
    data = uv.readms(filename=concat_file, datacolumn='data')

    # find indicies where weights are non-zero
    if args.uvcut:
        good, = np.where((data.weights[:,0] > 0) & (data.uvdist > 50000))
        cut_name = "_50klam"
    else:
        good, = np.where(data.weights[:,0] > 0)
        cut_name = ""

    # find data values at these indicies
    new_u = data.u[good]
    new_v = data.v[good]
    new_real = data.real[good,:]
    new_imag = data.imag[good,:]
    new_weights = data.weights[good,:]
    # create hdf5 file
    os.system("rm -rf *.hdf5")
    output_file = data_dir + source + '_' + linename + cut_name +  '.hdf5'
    new_data = uv.Visibilities(new_u, new_v, data.freq, new_real, new_imag, new_weights)
    new_data.write(output_file)

if make_config:
    if not os.path.exists(args.model_path):
        os.system("mkdir {}".format(args.model_path))
    create_config(data_dir, args.model_dir, linename, args.disk_type, args.dpc)


    


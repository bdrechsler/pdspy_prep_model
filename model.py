import glob
import os
import numpy as np
from casatasks import mstransform, tclean, listobs, concat, rmtables, impbcor, exportfits
import pdspy.interferometry as uv

class Model:
    
    def __init__(self, name, dpc, linename='C18O', chan_width='0.334km/s', nchan=36, svel="-2.0km/s", robust=2):
        self.name = name
        self.dpc = dpc
    
    def prep_lines(self, data_dir, model_dir, parallel=False):

        rfreq = '219.56035410GHz' # assume C18O
        
        # get list of spectral line ms files
        line_vis_list = glob.glob(data_dir + "*spectral_line.ms")
        
        """
        #### Regrid the data ###
        """
        
        regrid_vis = []
        for line_vis in line_vis_list:
        # find spectral window corresponding to rfreq

            # create listobs file
            listfile = line_vis.replace('.ms', '.listobs') 
            os.system("rm -rf " + data_dir + listfile)
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

            outfile = line_vis.replace('spectral_line.ms', self.name+'_lsrk.ms') # name of output ms file
            print("Creating " + outfile)
            os.system("rm -rf " + outfile) 

            mstransform(vis=line_vis, regridms=True, mode='velocity', outputvis=outfile,
                        outframe='LSRK', veltype='radio', restfreq=rfreq, datacolumn='data',
                        width=self.chan_width, nchan=self.nchan, start=self.svel, combinespws=False, keepflags=False,
                        timeaverage=True, timebin='30.25s', spw=spw)
        
            regrid_vis.append(outfile)
            
        """
        ##### Clean and Image the Data #######
        """
        print("Imaging")

        imagename = data_dir + self.name + '_' + self.linename + '_t2000klam'
        for ext in ['.image','.mask','.model','.pb','.psf','.residual','.sumwt','.workingdirectory']:
            os.system('rm -rf ' + imagename + ext)

        print("Running tlean:")

        uvrange='>50klambda'

        tclean(vis=regrid_vis, spw='', imagename=imagename, specmode='cube', imsize=512,
            deconvolver='hogbom', start=self.svel, width=self.chan_width, nchan=self.nchan, outframe='LSRK',
            veltype='radio', restfreq=rfreq, cell='0.025arcsec',
            gain=0.1, niter=20000, weighting='briggs', robust=self.robust, threshold='1.0mJy',
            usemask='auto-multithresh', sidelobethreshold=2.0, noisethreshold=4.0,
            lownoisethreshold=1.0, interactive=False, restoringbeam='common',
            uvtaper=['2000klambda'], uvrange=uvrange, parallel=parallel)
        
        # export the images
        myimages = glob.glob(data_dir + "*.image")
        for image in myimages:
            exportfits(imagename=image, fitsimage=image+'.fits', overwrite=True)

        for ext in ['*.pb', '*.psf', '*.model', '*.residual', '*.mask', '*.image', '*.pbcor']:
            os.system("rm -rf " + data_dir + ext)
import os
import glob
from prep_lines import prep_data
from create_config import create_config
from create_batch_submit import create_batch_submit

class Model:
    
    def __init__(self, source, dpc, user, vsys, linename='C18O', chan_width='0.334km/s',
                 nchan=42, robust=2, x0=[-0.5, 0.5], y0=[-0.5, 0.5],
                 disk_types=["truncated", "exptaper", "dartois-exptaper", "dartois-truncated"]):
        
        self.source = source
        self.dpc = dpc
        self.user = user
        self.linename = linename
        self.chan_width = chan_width
        self.nchan = nchan
        self.vsys = vsys
        self.robust = robust
        self.x0=x0
        self.y0=y0
        self.disk_types = disk_types
    
    def prep_model(self, data=True, config=True, batch_script=True,
                   remove_files=False, remote=1):
        
        # if there are ms files, prep the data
        data_dir = os.environ['PDSPY_LOCAL_DIR'] + self.source + '/data/'
        ms_files = glob.glob(data_dir + "*.ms")
        if data and len(ms_files) != 0:
            prep_data(source=self.source, chan_width=self.chan_width,
                      nchan=self.nchan, vsys=self.vsys, robust=self.robust,
                      linename=self.linename, remove_files=remove_files)
        
        if config or batch_script:
            for disk_type in self.disk_types:
                model_dir = os.environ['PDSPY_LOCAL_DIR'] + self.source + '/' + disk_type + "/"
                if not os.path.exists(model_dir):
                    os.system("mkdir {}".format(model_dir))

        if config:
            for disk_type in self.disk_types:
                create_config(source=self.source, line=self.linename,
                              disk_type=disk_type, dpc=self.dpc, vsys=self.vsys,
                              x0=self.x0, y0=self.y0)
                
        if batch_script:
            for disk_type in self.disk_types:
                create_batch_submit(source=self.source, disk_type=disk_type, user=self.user, remote=remote)
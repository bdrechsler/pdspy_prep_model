import os
from prep_lines import prep_data
from create_config import create_config
from create_batch_submit import create_batch_submit

class Model:
    
    def __init__(self, name, dpc, user, vsys, linename='C18O', chan_width='0.334km/s',
                 nchan=42, robust=2, x0=[-0.5, 0.5], y0=[-0.5, 0.5],
                 disk_types=["truncated", "exptaper", "dartois-exptaper", "dartois-truncated"]):
        
        self.name = name
        self.dpc = dpc
        self.user = user
        self.linename = linename
        self.chan_width = chan_width
        self.nchan = nchan
        self.vsys = vsys
        self.robust = robust
        self.disk_types = disk_types
    
    def prep_model(self, data=True, config=True, batch_script=True,
                   remove_files=False):

        if data:
            prep_data(source=self.name, chan_width=self.chan_width,
                      nchan=self.nchan, svys=self.vsys, robust=self.robust,
                      linename=self.linename, remove_files=remove_files)
        
        if config or batch_script:
            for disk_type in self.disk_types:
                model_dir = os.environ['PDSPY_LOCAL_DIR'] + self.name + '/' + disk_type + "/"
                if not os.path.exists(model_dir):
                    os.system("mkdir {}".format(model_dir))

        if config:
            for disk_type in self.disk_types:
                create_config(source=self.name, line=self.linename,
                              disk_type=disk_type, dpc=self.dpc)
                
        if batch_script:
            for disk_type in self.disk_types:
                create_batch_submit(source=self.name, disk_type=disk_type, user=self.user)
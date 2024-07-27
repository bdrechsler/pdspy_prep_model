import os
from prep_lines import prep_data
from create_config import create_config
from create_batch_submit import create_batch_submit

class Model:
    
    def __init__(self, name, dpc, path, user, linename='C18O', chan_width='0.334km/s',
                 nchan=36, svel="-2.0km/s", robust=2,
                 disk_types=["truncated", "exptaper", "dartois-exptaper", "dartois-truncated"]):
        
        self.name = name
        self.dpc = dpc
        self.path = path
        self.user = user
        self.linename = linename
        self.chan_width = chan_width
        self.nchan = nchan
        self.svel = svel
        self.robust = robust
        self.disk_types = disk_types
    
    def prep_model(self, data=True, config=True, batch_script=True,
                   remove_files=False):

        if data:
            prep_data(source=self.name, source_dir=self.path, chan_width=self.chan_width,
                      nchan=self.nchan, svel=self.svel, robust=self.robust,
                      linename=self.linename, remove_files=remove_files)
        
        if config or batch_script:
            for disk_type in self.disk_types:
                model_dir = self.path + disk_type + "/"
                if not os.path.exists(model_dir):
                    os.system("mkdir {}".format(model_dir))

        if config:
            for disk_type in self.disk_types:
                create_config(source=self.name, source_dir=self.path, line=self.linename,
                              disk_type=disk_type, dpc=self.dpc)
                
        if batch_script:
            for disk_type in self.disk_types:
                create_batch_submit(source=self.name, source_dir=self.path,
                                    disk_type=disk_type, user=self.user)
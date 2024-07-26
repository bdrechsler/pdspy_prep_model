from prep_lines import prep_data
from create_config import create_config

class Model:
    
    def __init__(self, name, dpc, path, linename='C18O', chan_width='0.334km/s',
                 nchan=36, svel="-2.0km/s", robust=2,
                 disk_types=["truncated", "exptaper", "dartois-exptaper", "dartois-truncated"]):
        
        self.name = name
        self.dpc = dpc
        self.path = path
        self.linename = linename
        self.chan_width = chan_width
        self.nchan = nchan
        self.svel = svel
        self.robust = robust
        self.disk_types = disk_types
    
    def prep_model(self, disk_types, data=True, config=True,
                   batch_script=True,remove_files=True):

        if data:
            prep_data(source=self.name, source_dir=self.path, chan_width=self.chan_width,
                      nchan=self.nchan, svel=self.svel, robust=self.robust,
                      linename=self.linename, remove_files=remove_files)
        
        if config:
            for disk_type in disk_types:
                create_config(source_dir=self.path, line=self.linename,
                              disk_type=disk_type, dpc=self.dpc)
                
        if 
import os

def create_batch_submit(source, model_path, user, environ='pdspy-2.0.8'):
    fname = model_path + "batch_submit.sh"
    home_dir = os.environ['HOME']
    with open(fname, 'w') as batch:
        batch.write('#PBS -S /bin/sh\n')
        batch.write('#PBS -l select=4:ncpus=28:mpiprocs=1:model=bro\n')
        batch.write('#PBS -l walltime=96:00:00\n')
        batch.write('#PBS -j oe\n')
        batch.write('#PBS -m bae\n')
        batch.write('#PBS -N {}\n'.format(source))
        batch.write('source {}/.bash_profile\n'.format(home_dir))
        batch.write('cd {}\n'.format(model_path))
        batch.write('conda activate {}\n'.format(environ))
        batch.write('rm nodelist\n')
        batch.write('qstat -nu {} -x $PBS_JOBID |tail -n1 > nodes\n'.format(user))
        batch.write('cat $PBS_NODEFILE > pbs_nodefile\n')
        batch.write('echo $PBS_NODEFILE > pbs_nodefile_path\n')
        batch.write('python3 makenodelist.py\n')
        batch.write('mpiexec -np 112 --hostfile nodelist flared_model_nested.py --object {0} --ncpus 1 --ftcode galario-unstructured\n'.format(source))



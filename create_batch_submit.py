import os

def create_batch_submit(source, source_dir, disk_type, user, environ='pdspy-2.0.8'):
    fname = "{0}{1}/batch_submit.sh".format(source_dir, disk_type)
    home_dir = os.environ['HOME']
    model_path = source_dir + disk_type + '/'
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

    with open(model_path + 'make_nodelist.py', 'w') as nodelist:
        nodelist.write("file1=open('pbs_nodefile')\n")
        nodelist.write("nodeline=file1.readlines()\n")
        nodelist.write("file1.close()\n")
        nodelist.write("file1 = open('nodelist', 'w')\n")
        nodelist.write("i=0\n")
        nodelist.write("for node in nodeline:\n")
        nodelist.write("    if i == 0:\n")
        nodelist.write("        file1.writelines(node.replace('\n','')+':29\n')\n")
        nodelist.write("    else:\n")
        nodelist.write("        file1.writelines(node.replace('\n','')+':28\n')\n")
        nodelist.write("    i+=1\n")
        nodelist.write("\n")
        nodelist.write("file1.close()")

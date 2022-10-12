

export CONDOR_INSTALL=/global/cfs/cdirs/jaws/condor/condor-9.5
export NERSC_PEGASUS_HOME=/global/common/software/m3792/pegasus
export PATH=${CONDOR_INSTALL}/bin:${CONDOR_INSTALL}/sbin:${NERSC_PEGASUS_HOME}/bin:${PATH}
export CONDOR_CONFIG=${HOME}/nersc-pegasus-example/htcondor_server.conf
export LOGDIR=/global/cscratch1/sd/tylern/condor
export PASSWORDFILE=${HOME}/.condor/cron.password
export PORT=9820
export CONDOR_SERVER=cori20-224.nersc.gov
export NERSC_USER=tylern
export NERSC_PROJECT=m3792


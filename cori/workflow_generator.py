#!/usr/bin/env python3
from Pegasus.api import (
    Properties,
    SiteCatalog,
    Site,
    Directory,
    FileServer,
    Operation,
    Grid,
    Scheduler,
    SupportedJobs,
    TransformationCatalog,
    Container,
    Transformation,
    ReplicaCatalog,
    Workflow,
    File,
    Job
)
import os
import logging
from pathlib import Path
from argparse import ArgumentParser

logging.basicConfig(level=logging.DEBUG)

# --- Import Pegasus API ------------------------------------------------------


class SplitWorkflow:
    # --- Init ----------------------------------------------------------------
    def __init__(self, dagfile="workflow.yml"):
        self.dagfile = dagfile
        self.wf_name = "split"
        self.wf_dir = os.path.join(
            "/global/cscratch1/sd/${NERSC_USER}/pegasus")

    # --- Configuration (Pegasus Properties) ----------------------------------
    def create_pegasus_properties(self):
        self.props = Properties()

        # props["pegasus.monitord.encoding"] = "json"
        # self.properties["pegasus.integrity.checking"] = "none"
        return
        # --- Write files in directory --------------------------------------------

    def write(self):
        # if not self.sc is None:
        #     self.sc.write()
        self.props.write()
        self.tc.write()
        self.rc.write()
        self.wf.write()

    # --- Site Catalog --------------------------------------------------------
    def create_sites_catalog(self, exec_site_name="cori"):
        self.sc = SiteCatalog()

        shared_scratch_dir = os.path.join(
            "/global/cscratch1/sd/${NERSC_USER}/pegasus/scratch")
        local_storage_dir = os.path.join(
            "/global/cscratch1/sd/${NERSC_USER}/pegasus/output")

        local = Site("local").add_directories(
            Directory(Directory.SHARED_SCRATCH, shared_scratch_dir).add_file_servers(
                FileServer("file://" + shared_scratch_dir, Operation.ALL)
            ),
            Directory(Directory.LOCAL_STORAGE, local_storage_dir).add_file_servers(
                FileServer("file://" + local_storage_dir, Operation.ALL)
            ),
        )

        exec_site = Site("cori")\
            .add_grids(
            Grid(grid_type=Grid.BATCH, scheduler_type=Scheduler.SLURM,
                 contact="${NERSC_USER}@cori.nersc.gov", job_type=SupportedJobs.COMPUTE)
        )\
            .add_directories(
            Directory(
                Directory.SHARED_SCRATCH, shared_scratch_dir)
            .add_file_servers(FileServer("file:///global/cscratch1/sd/${NERSC_USER}/pegasus/scratch", Operation.ALL)),
            Directory(
                Directory.SHARED_STORAGE, "/global/cscratch1/sd/${NERSC_USER}/pegasus/storage")
            .add_file_servers(FileServer("file:///global/cscratch1/sd/${NERSC_USER}/pegasus/storage", Operation.ALL))
        )\
            .add_env(key="PEGASUS_HOME", value="${NERSC_PEGASUS_HOME}")\
            .add_condor_profile(grid_resource='batch slurm')\
            .add_pegasus_profile(
            style="glite",
            data_configuration="sharedfs",
            project="nstaff",
            queue="shared",
            change_dir="true",
            create_dir="true",
            glite_arguments="-C haswell",
            cores="2",
            memory="4GB",
            runtime="1200",
            nodes=1,
        )

        self.sc.add_sites(local, exec_site)

    # --- Transformation Catalog (Executables and Containers) -----------------
    def create_transformation_catalog(self, exec_site_name="cori"):
        self.tc = TransformationCatalog()

        wc = Transformation(
            "wc", site=exec_site_name, pfn="/usr/bin/wc", is_stageable=False  # , container=centos,
        )
        split = Transformation(
            "split", site=exec_site_name, pfn="/usr/bin/split", is_stageable=False
        )

        self.tc.add_transformations(split, wc)

    # --- Replica Catalog ------------------------------------------------------
    def create_replica_catalog(self):
        self.rc = ReplicaCatalog()

        # Add f.a replica
        self.rc.add_replica(
            "local", "covid.csv", os.path.join(
                self.wf_dir, "input", "covid.csv")
        )

    # --- Create Workflow -----------------------------------------------------
    def create_workflow(self):
        self.wf = Workflow(self.wf_name, infer_dependencies=True)

        csv_file = File("covid.csv")

        # the split job that splits the csv_file into smaller chunks
        split = (
            Job("split")
            .add_args("-n", "4", "-a", "1", csv_file, "part.")
            .add_inputs(csv_file)
            .add_pegasus_profile(label="p1")
        )

        # we do a parmeter sweep on the first 4 chunks created
        counts = {}
        for c in ['a', 'b', 'c', 'd']:
            part = File("part.%s" % c)
            split.add_outputs(part, stage_out=True, register_replica=True)

            counts[c] = File("count.txt.%s" % c)

            wc = (
                Job("wc")
                .add_args("-l", part)
                .add_inputs(part)
                .set_stdout(counts[c], stage_out=True, register_replica=True)
                .add_pegasus_profile(label="p1")
            )

            self.wf.add_jobs(wc)

        self.wf.add_jobs(split)


if __name__ == "__main__":
    parser = ArgumentParser(description="Pegasus Split Workflow")

    parser.add_argument(
        "-s",
        "--skip_sites_catalog",
        action="store_true",
        help="Skip site catalog creation",
    )
    parser.add_argument(
        "-e",
        "--execution_site_name",
        metavar="STR",
        type=str,
        default="cori",
        help="Execution site name (default: cori)",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="STR",
        type=str,
        default="workflow.yml",
        help="Output file (default: workflow.yml)",
    )

    args = parser.parse_args()

    workflow = SplitWorkflow(args.output)

    # if not args.skip_sites_catalog:
    #     print("Creating execution sites...")
    #     workflow.create_sites_catalog(args.execution_site_name)

    print("Creating workflow properties...")
    workflow.create_pegasus_properties()

    print("Creating transformation catalog...")
    workflow.create_transformation_catalog(args.execution_site_name)

    print("Creating replica catalog...")
    workflow.create_replica_catalog()

    print("Creating split workflow dag...")
    workflow.create_workflow()

    workflow.write()

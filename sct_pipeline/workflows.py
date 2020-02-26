import os
import nipype
import os  # system functions
import nipype.interfaces.io as nio  # Data i/o
import nipype.interfaces.utility as util  # utility
import nipype.pipeline.engine as pe  # pypeline engine

from nipype import Workflow, Node, MapNode, Function, IdentityInterface
from nipype.interfaces.ants import Registration, AverageImages
from nipype.interfaces.ants import N4BiasFieldCorrection, Registration, ApplyTransforms
from nipype.interfaces.fsl import BET
from nipype.interfaces.fsl import Smooth
from .interfaces import FSLBET_Robust_R, MIMOSA_R, FrangiFilter, LesionCenter
from nipype.interfaces.ants import MultiplyImages
from iacl_pipeline.workflows.base import PipelineWorkflow


def create_centralveinsign_workflow(scan_directory, patient_id=None, scan_id=None):

    name = 'SpinalCordToolbox'
    if patient_id is not None and scan_id is not None:
        scan_directory = os.path.join(scan_directory, patient_id, 'pipeline')
        name += '_' + scan_id

    wf = PipelineWorkflow(name, scan_directory)

    wf = PipelineWorkflow('SpinalCordToolbox', scan_directory, patient_id, scan_id)

    inputnode = Node(IdentityInterface(["t1_sc_image", "dti_sc_image", "mt_on_sc_image", "mt_off_sc_image"]), "inputnode")


